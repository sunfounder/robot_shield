"""robot_shield — Servo, PWM, Motor, and Battery control via Arduino Bridge I2C.

Provides hardware abstraction for the SunFounder Robot Shield:

- ``Servo``      — angle control (-90° to +90°) with offset calibration
- ``PWM``        — raw PWM frequency/pulse control (12 channels)
- ``Motor``      — DC motor control (-100% to +100% power, 4 channels)
- ``Battery``    — battery voltage, percentage, and status via I2C registers
- ``UserButton`` — USR button press/release detection with callbacks
- ``I2C``        — low-level I2C bus read/write via Arduino Bridge RPC
- ``setup_audio_output`` — configure Qualcomm Codec ALSA mixer for playback

Usage::

    from robot_shield import Servo, PWM, Motor

    servo = Servo(0)
    servo.angle(45)
"""

from ._version import __version__
from .i2c import I2C
from .pwm import PWM
from .servo import Servo
from .motor import Motor
from .audio import setup_audio_output
from .battery import Battery
from .user_button import UserButton
from . import reg_map

__all__ = [
    "__version__",
    "I2C", "PWM", "Servo", "Motor",
    "Battery", "UserButton", "setup_audio_output", "reg_map",
]