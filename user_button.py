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

from arduino.app_utils import Bridge
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
        """Set callback for when the button is pressed and released (full click)."""
        self._on_click = callback

    def set_on_press(self, callback: Callable[[], None]) -> None:
        """Set callback for when the button is pressed down."""
        self._on_press = callback

    def set_on_release(self, callback: Callable[[], None]) -> None:
        """Set callback for when the button is released."""
        self._on_release = callback

    def set_on_press_released(self, callback: Callable[[bool], None]) -> None:
        """Set callback for press/release state changes.

        Called with ``True`` on press, ``False`` on release.
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
        """Return True if the button is currently pressed."""
        return self.pressed

    def is_pressed(self) -> bool:
        """Return True if the button is currently pressed."""
        return self.pressed

    def get_pressed_for(self) -> float:
        """Return how long the button has been (or was) pressed, in seconds."""
        if self.pressed:
            return time.time() - self.pressed_at
        return self.pressed_for

    # ------------------------------------------------------------------
    #  Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Deprecated — polling starts automatically in __init__."""
        warnings.warn(
            "UserButton.start() is deprecated. Polling starts automatically in __init__.",
            DeprecationWarning,
            stacklevel=2,
        )

    def stop(self) -> None:
        """Stop the background polling thread and release resources."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    # ------------------------------------------------------------------
    #  Internal
    # ------------------------------------------------------------------

    def _start_polling(self) -> None:
        """Launch the background polling thread."""
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def _poll_loop(self) -> None:
        """Poll REG_USR_KEY_SIGNAL for press/release events."""
        # Capture initial state so we don't fire on stale register values
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
        """Process a register value change."""
        if signal == USR_KEY_PTT_START:
            self._on_press_event()
        elif signal == USR_KEY_PTT_STOP and self.pressed:
            # Guard against stale 0x02 at startup: only accept release if
            # we previously saw a press (pressed == True).
            self._on_release_event()

    def _on_press_event(self) -> None:
        """Handle button press."""
        self.pressed = True
        self.pressed_at = time.time()
        self._long_press_triggered = False
        self._press_generation += 1  # invalidate any stale long-press timers

        self._safe_call(self._on_press)
        self._safe_call(self._on_press_released, True)

        if self._on_long_press is not None or self._on_long_press_released is not None:
            dur = self._long_press_duration
            gen = self._press_generation  # capture the generation this timer belongs to
            threading.Thread(
                target=self._long_press_timer, args=(dur, gen), daemon=True
            ).start()

    def _on_release_event(self) -> None:
        """Handle button release."""
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

        *generation* prevents a stale timer (from a previous press) from
        firing during a subsequent rapid press.
        """
        time.sleep(duration)
        if self.pressed and not self._long_press_triggered and self._press_generation == generation:
            self._long_press_triggered = True
            self._safe_call(self._on_long_press)

    def _read_reg(self):
        """Read REG_USR_KEY_SIGNAL via Arduino Bridge."""
        try:
            return Bridge.call("read_reg", str(REG_USR_KEY_SIGNAL))
        except Exception:
            return None

    @staticmethod
    def _safe_call(callback, *args) -> None:
        """Invoke a callback, swallowing any exceptions."""
        if callback is None:
            return
        try:
            callback(*args)
        except Exception:
            pass
