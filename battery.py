"""Battery status reader via I2C registers (Arduino Bridge).

Register addresses are imported from :mod:`.reg_map`.

Example::

    >>> from robot_shield import Battery
    >>> battery = Battery()
    >>> print(battery)
    Robot Shield SunFounder Normal 76% 7.4 V
    >>> print(battery.voltage)
    7.4
    >>> print(battery.capacity)
    76
    >>> print(battery.status)
    Normal
"""

import logging

from arduino.app_utils import Bridge
from .reg_map import REG_BAT_VOLT, REG_BAT_PERCENT, REG_BAT_STATUS

logger = logging.getLogger(__name__)

_STATUS_MAP = {
    0: "Normal",
    1: "Low Voltage",
    2: "Over Voltage",
    3: "Over Current",
}

MODEL_NAME = "Robot Shield"
MANUFACTURER = "SunFounder"


class Battery:
    """Battery status reader via I2C registers over Arduino Bridge."""

    @property
    def present(self) -> bool:
        """Check if battery is present (voltage > 0)."""
        return self._read_reg(REG_BAT_VOLT) > 0

    @property
    def online(self) -> bool:
        """Check if battery is online — True when I2C is reachable."""
        try:
            Bridge.call("read_reg", str(REG_BAT_VOLT))
            return True
        except Exception:
            return False

    @property
    def status(self) -> str:
        """Get battery health status.

        Returns:
            str: One of "Normal", "Low Voltage", "Over Voltage", "Over Current",
                 or "Unknown(N)" for unrecognised codes.
        """
        raw = self._read_reg(REG_BAT_STATUS)
        return _STATUS_MAP.get(raw, f"Unknown({raw})")

    @property
    def raw_status(self) -> int:
        """Get raw battery status register value (0–3)."""
        return self._read_reg(REG_BAT_STATUS)

    @property
    def capacity(self) -> int:
        """Get battery charge percentage (0–100)."""
        return self._read_reg(REG_BAT_PERCENT)

    @property
    def voltage(self) -> float:
        """Get battery voltage in volts (register unit: 0.1 V)."""
        raw = self._read_reg(REG_BAT_VOLT)
        return round(raw / 10.0, 1)

    @property
    def model_name(self) -> str:
        """Get device model name."""
        return MODEL_NAME

    @property
    def manufacturer(self) -> str:
        """Get device manufacturer."""
        return MANUFACTURER

    @property
    def is_ok(self) -> bool:
        """Check if battery status is normal (no warning or fault)."""
        return self.raw_status == 0

    def _read_reg(self, addr: int) -> int:
        try:
            return Bridge.call("read_reg", str(addr))
        except Exception as e:
            logger.error("read_reg(0x%02X) failed: %s", addr, e)
            return 0

    def __str__(self) -> str:
        return f"{self.model_name} {self.manufacturer} {self.status} {self.capacity}% {self.voltage} V"
