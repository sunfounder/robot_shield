"""Servo motor class — calls Bridge "servo_set_angle" / "servo_get_angle".

Layer:  Python Servo  →  Bridge  →  sketch servo_control  →  pwm_control  →  i2c

Example::

    >>> from robot_shield import Servo
    >>> servo = Servo(0)
    >>> servo.angle(-90)
    >>> servo.angle(0)
    >>> servo.angle(90)

    Change the angle range::

    >>> servo = Servo(0, min=0, max=180)
    >>> servo.angle(0)
    >>> servo.angle(180)

    Add offset::

    >>> servo = Servo(0, offset=10.0)
    >>> servo.angle(0)
"""

from arduino.app_utils import Bridge
from ._utils import constrain


class Servo:
    """Servo motor via Bridge → sketch servo_control.

    Args:
        channel: PWM channel number (0–11).
        offset: calibration offset in degrees (-20.0 ~ 20.0), default 0.0.
        min: minimum angle, default -90.
        max: maximum angle, default 90.
    """

    MIN_PW = 500
    MAX_PW = 2500
    FREQ = 50

    def __init__(self, channel: int, offset: float = 0.0,
                 min: float = -90, max: float = 90):
        self._ch = channel
        self._offset = offset
        self._angle = 0.0
        self._min = min
        self._max = max

    def offset(self, offset: float = None):
        """Get or set the calibration offset.

        Args:
            offset: Offset in degrees, clipped to ±20. Leave ``None`` to read.

        Returns:
            float: Current offset value in degrees.
        """
        if offset is None:
            return self._offset
        self._offset = constrain(offset, -20.0, 20.0)
        return self._offset

    def angle(self, angle: float = None):
        """Get or set the servo angle via Bridge → sketch servo_control.

        Args:
            angle: Desired angle in degrees (clamped to [*min*, *max*]).
                   Offset is added before sending to hardware.
                   Leave ``None`` to read current angle from sketch.

        Returns:
            float: Current angle in degrees.
        """
        if angle is None:
            return Bridge.call("servo_get_angle", str(self._ch))
        angle = constrain(angle, self._min, self._max)
        self._angle = angle
        calibrated = angle + self._offset
        calibrated = constrain(calibrated, -90.0, 90.0)
        Bridge.call("servo_set_angle", str(self._ch), str(int(calibrated)))
        return self._angle
