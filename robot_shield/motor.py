"""DC motor control via Bridge → sketch motor_control.

Layer:  Python Motor  →  Bridge  →  sketch motor_control  →  pwm_control  →  i2c

Example::

    >>> from robot_shield import Motor
    >>> motor = Motor('M0')
    >>> motor.power(50)    # forward 50%
    >>> motor.power(-30)   # reverse 30%
    >>> motor.stop()       # brake

Channel mapping:

    ======= ====== ======
    Motor   A相    B相
    ======= ====== ======
    M0      PWM4   PWM5
    M1      PWM6   PWM7
    M2      PWM8   PWM9
    M3      PWM10  PWM11
    ======= ====== ======

Control logic:

    = = ==========
    A B 模式
    = = ==========
    1 0 正转
    0 1 反转
    0 0 刹车
    = = ==========
"""

from arduino.app_utils import Bridge


class Motor:
    """DC motor driven by dual PWM channels (H-bridge) via Bridge → sketch."""

    MOTOR_PINS = {
        "M0": (4, 5),
        "M1": (6, 7),
        "M2": (8, 9),
        "M3": (10, 11),
    }

    def __init__(self, motor: str = None, **kwargs):
        """Initialize a DC motor instance.

        Args:
            motor: Motor identifier, one of ``"M0"``, ``"M1"``, ``"M2"``, ``"M3"``.
            is_reversed: If ``True``, inverts the direction (optional keyword).

        Raises:
            ValueError: If *motor* is not one of the valid identifiers.
        """
        if motor not in self.MOTOR_PINS:
            raise ValueError(
                f"motor must be one of {list(self.MOTOR_PINS.keys())}")
        self._motor = motor
        self._is_reversed = kwargs.get("is_reversed", False)
        self._power = 0

    def power(self, power: float = None):
        """Get or set motor power via Bridge → sketch motor_control.

        Args:
            power: -100.0 (full reverse) to 100.0 (full forward).
                   Leave None to read current value.

        Returns:
            Current power level.
        """
        if power is None:
            return self._power

        power = max(-100.0, min(100.0, float(power)))
        if self._is_reversed:
            power = -power
        self._power = power

        Bridge.call("motor_set_power", self._motor, str(int(power)))
        return self._power

    def set_is_reverse(self, is_reverse: bool):
        """Set whether the motor direction is reversed.

        Args:
            is_reverse: ``True`` to invert direction, ``False`` for normal.
        """
        self._is_reversed = is_reverse

    def stop(self):
        """Stop the motor (brake — both channels low)."""
        self.power(0)
