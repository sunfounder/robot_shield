"""PWM channel control via Bridge → sketch pwm_control.

Layer:  Python PWM  →  Bridge  →  sketch pwm_control  →  i2c
"""

from arduino.app_utils import Bridge


class PWM:
    """Single PWM channel control via Bridge → sketch pwm_control.

    Args:
        channel: PWM channel number (0–11). Channels 0–1 are mapped to
                 PAN/TILT servos; channels 4–11 to motor phases.
    """

    MIN_PW = 500
    MAX_PW = 2500
    FREQ = 50

    def __init__(self, channel: int):
        self._ch = channel
        self._freq = self.FREQ
        self._enabled = False

    def freq(self, freq: int = None):
        """Get or set PWM frequency in Hz.

        Args:
            freq: Frequency in Hz. Leave ``None`` to read back current value.

        Returns:
            int: Current frequency in Hz.
        """
        if freq is None:
            return self._freq
        self._freq = freq
        Bridge.call("pwm_set_freq", str(self._ch), str(freq))
        return self._freq

    def pulse_width(self, pulse_width: int = None):
        """Get or set pulse width in microseconds.

        Args:
            pulse_width: Pulse width in μs (0–65535, 500–2500 for servos).
                         Leave ``None`` to read back current value from sketch.

        Returns:
            int: Current pulse width in μs.
        """
        if pulse_width is None:
            return Bridge.call("pwm_get_pulse", str(self._ch))
        pulse_width = max(0, min(65535, int(pulse_width)))
        Bridge.call("pwm_set_pulse", str(self._ch), str(pulse_width))
        self._enabled = True
        return pulse_width

    def pulse_width_percent(self, percent: float = None):
        """Get or set pulse width as a percentage of the period.

        Converts between percent and pulse width using the current frequency.

        Args:
            percent: Duty cycle percentage (0.0–100.0).
                     Leave ``None`` to read back current value.

        Returns:
            float: Current duty cycle as a percentage (0.0–100.0).
        """
        period_us = 1_000_000 / self._freq
        if percent is None:
            return (self.pulse_width() or 0) / period_us * 100.0
        pulse_us = percent / 100.0 * period_us
        return self.pulse_width(int(pulse_us))

    def enable(self, value: bool = None):
        """Get or set channel enable state.

        Args:
            value: ``True`` to enable PWM output, ``False`` to disable.
                   Leave ``None`` to read back current state.

        Returns:
            bool: ``True`` if channel is enabled, ``False`` otherwise.
        """
        if value is None:
            return self._enabled
        if self._enabled == bool(value):
            return self._enabled
        self._enabled = bool(value)
        Bridge.call("pwm_enable", str(self._ch), "1" if self._enabled else "0")
        return self._enabled
