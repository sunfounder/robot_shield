"""User button via I2C register polling (Arduino Bridge).

The USR button is read from the co-processor at I2C address 0x20 via
register ``REG_USR_KEY_SIGNAL`` (0x0C). Values are event-based:
0x01 = pressed, 0x02 = released.

Example::

    >>> from robot_shield import UserButton
    >>> btn = UserButton()
    >>> btn.set_on_click(lambda: print("clicked"))
    >>> btn.set_on_long_press(lambda: print("long press"), duration=2.0)
    >>> print(btn.is_pressed())
    False
"""

import time
import threading
import warnings
from typing import Callable, Optional

from .i2c import I2C
from .reg_map import REG_USR_KEY_SIGNAL

USR_KEY_PTT_START = 0x01
USR_KEY_PTT_STOP = 0x02

DEFAULT_POLL_INTERVAL = 0.1
DEFAULT_LONG_PRESS_DURATION = 2.0


class UserButton:
    """User button via I2C register polling over Arduino Bridge.

    The underlying register (0x0C) is *event-based*, not level-based:
    the co-processor writes 0x01 once on press and 0x02 once on release.
    This class tracks state internally so ``is_pressed()`` works as expected.
    """

    def __init__(self) -> None:
        """Initialize the button and start background polling.

        Sets up callback slots and launches a daemon poll thread that reads
        ``REG_USR_KEY_SIGNAL`` at 100 ms intervals.
        """
        self.pressed = False
        self.pressed_for = 0.0
        self.pressed_at = 0.0

        self._on_click: Optional[Callable[[], None]] = None
        self._on_press: Optional[Callable[[], None]] = None
        self._on_release: Optional[Callable[[], None]] = None
        self._on_press_released: Optional[Callable[[bool], None]] = None
        self._on_long_press: Optional[Callable[[], None]] = None
        self._on_long_press_released: Optional[Callable[[], None]] = None
        self._long_press_duration = DEFAULT_LONG_PRESS_DURATION

        self._long_press_triggered = False
        self._press_generation = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._start_polling()

    # ------------------------------------------------------------------
    #  Callback setters
    # ------------------------------------------------------------------

    def set_on_click(self, callback: Callable[[], None]) -> None:
        """Set callback for when the button is pressed and released (full click).

        Fires only for quick press-release cycles (shorter than the long-press
        threshold). Does not fire after a long press.

        Args:
            callback: Function to call on click, takes no arguments.
        """
        self._on_click = callback

    def set_on_press(self, callback: Callable[[], None]) -> None:
        """Set callback for when the button is pressed down.

        Args:
            callback: Function to call on press, takes no arguments.
        """
        self._on_press = callback

    def set_on_release(self, callback: Callable[[], None]) -> None:
        """Set callback for when the button is released.

        Args:
            callback: Function to call on release, takes no arguments.
        """
        self._on_release = callback

    def set_on_press_released(self, callback: Callable[[bool], None]) -> None:
        """Set callback for press/release state changes.

        Args:
            callback: Function called with ``True`` on press, ``False`` on release.
        """
        self._on_press_released = callback

    def set_on_long_press(self, callback: Callable[[], None], duration: float = 2.0) -> None:
        """Set callback for when the button is held down for *duration* seconds.

        Args:
            callback: Function to call on long press.
            duration: Hold time in seconds (2.0–5.0 recommended).
        """
        self._on_long_press = callback
        self._long_press_duration = max(0.1, duration)

    def set_on_long_press_released(self, callback: Callable[[], None], duration: float = 2.0) -> None:
        """Set callback for when the button is released after a long press.

        Args:
            callback: Function to call on long-press release.
            duration: Hold time threshold in seconds (2.0–5.0 recommended).
        """
        self._on_long_press_released = callback
        self._long_press_duration = max(0.1, duration)

    # ------------------------------------------------------------------
    #  State queries
    # ------------------------------------------------------------------

    def get_state(self) -> bool:
        """Return the current button state.

        Returns:
            bool: ``True`` if the button is currently pressed.
        """
        return self.pressed

    def is_pressed(self) -> bool:
        """Return whether the button is currently pressed.

        Returns:
            bool: ``True`` if the button is currently pressed.
        """
        return self.pressed

    def get_pressed_for(self) -> float:
        """Return how long the button has been (or was) pressed, in seconds.

        Returns the elapsed time since the current press started, or the
        duration of the most recent press if the button is now released.

        Returns:
            float: Press/release duration in seconds.
        """
        if self.pressed:
            return time.time() - self.pressed_at
        return self.pressed_for

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Deprecated — polling starts automatically in ``__init__``.

        Raises:
            DeprecationWarning: Always, since polling is auto-started.
        """
        warnings.warn(
            "UserButton.start() is deprecated. Polling starts automatically in __init__.",
            DeprecationWarning,
            stacklevel=2,
        )

    def stop(self) -> None:
        """Stop the background polling thread and release resources.

        Blocks up to 1 second waiting for the poll thread to exit.

        Returns:
            None
        """
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    # ------------------------------------------------------------------
    #  Internal
    # ------------------------------------------------------------------

    def _start_polling(self) -> None:
        """Launch the background polling thread as a daemon.

        Returns:
            None
        """
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def _poll_loop(self) -> None:
        """Poll REG_USR_KEY_SIGNAL at ``DEFAULT_POLL_INTERVAL`` for press/release events.

        Captures the initial register value to avoid firing on stale data at startup.

        Returns:
            None
        """
        prev = self._read_reg()
        while self._running:
            try:
                signal = self._read_reg()
                if signal is not None and signal != prev:
                    prev = signal
                    self._handle_signal(signal)
            except Exception:
                pass
            time.sleep(DEFAULT_POLL_INTERVAL)

    def _handle_signal(self, signal: int) -> None:
        """Process a register value change.

        Args:
            signal: Register value (``0x01`` = press, ``0x02`` = release).
                    Release is guarded against stale ``0x02`` at startup.
        """
        if signal == USR_KEY_PTT_START:
            self._on_press_event()
        elif signal == USR_KEY_PTT_STOP and self.pressed:
            self._on_release_event()

    def _on_press_event(self) -> None:
        """Record press time, invoke press callbacks, start long-press timer.

        Increments ``_press_generation`` to invalidate any stale long-press
        timers from prior presses.

        Returns:
            None
        """
        self.pressed = True
        self.pressed_at = time.time()
        self._long_press_triggered = False
        self._press_generation += 1

        self._safe_call(self._on_press)
        self._safe_call(self._on_press_released, True)

        if self._on_long_press is not None or self._on_long_press_released is not None:
            dur = self._long_press_duration
            gen = self._press_generation
            threading.Thread(
                target=self._long_press_timer, args=(dur, gen), daemon=True
            ).start()

    def _on_release_event(self) -> None:
        """Record release, invoke release/click/long-press-released callbacks.

        Fires ``_on_click`` for short presses, ``_on_long_press_released``
        if the long-press threshold was reached.

        Returns:
            None
        """
        self.pressed = False
        self.pressed_for = time.time() - self.pressed_at

        was_long = self._long_press_triggered
        self._long_press_triggered = False

        self._safe_call(self._on_release)
        self._safe_call(self._on_press_released, False)

        if was_long:
            self._safe_call(self._on_long_press_released)
        else:
            self._safe_call(self._on_click)

    def _long_press_timer(self, duration: float, generation: int) -> None:
        """Sleep for *duration*, then fire long-press callback if still pressed.

        Args:
            duration: Hold time threshold in seconds.
            generation: Press generation counter. If it no longer matches
                        ``self._press_generation``, this timer is stale
                        (from a prior press) and is silently discarded.
        """
        time.sleep(duration)
        if self.pressed and not self._long_press_triggered and self._press_generation == generation:
            self._long_press_triggered = True
            self._safe_call(self._on_long_press)

    _i2c: I2C | None = None

    @classmethod
    def _get_i2c(cls) -> I2C:
        """Get or create the shared I2C instance."""
        if cls._i2c is None:
            cls._i2c = I2C()
        return cls._i2c

    def _read_reg(self):
        """Read REG_USR_KEY_SIGNAL via I2C.

        Returns:
            int or None: Register value, or ``None`` if the read fails.
        """
        try:
            return self._get_i2c().read_byte_data(REG_USR_KEY_SIGNAL)
        except Exception:
            return None

    @staticmethod
    def _safe_call(callback, *args) -> None:
        """Invoke a callback, swallowing any exceptions silently.

        Args:
            callback: The callable to invoke, or ``None`` (no-op).
            *args: Positional arguments forwarded to *callback*.
        """
        if callback is None:
            return
        try:
            callback(*args)
        except Exception:
            pass
