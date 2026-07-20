"""Battery status reader via Arduino Bridge RPC.

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

from arduino.app_utils import Bridge

_STATUS_MAP = {
    0: "Normal",
    1: "Charging",
    2: "Full",
    3: "Low",
}

MODEL_NAME = "Robot Shield"
MANUFACTURER = "SunFounder"


class Battery:
    """Battery status reader via Arduino Bridge RPC.

    Uses the upstream Bridge functions ``get_bat_volt``, ``get_bat_percent``,
    and ``get_bat_status`` instead of raw I2C register reads.
    """

    @staticmethod
    def _bridge_call(func: str) -> int:
        """Call a Bridge battery function, returning 0 on failure."""
        try:
            return Bridge.call(func, "")
        except Exception:
            return 0

    @property
    def present(self) -> bool:
        """Check if battery is present (voltage > 0)."""
        return self._bridge_call("get_bat_volt") > 0

    @property
    def status(self) -> str:
        """Get battery health status.

        Returns:
            str: One of "Normal", "Charging", "Full", "Low",
                 or "Unknown(N)" for unrecognised codes.
        """
        raw = self._bridge_call("get_bat_status")
        return _STATUS_MAP.get(raw, f"Unknown({raw})")

    @property
    def raw_status(self) -> int:
        """Get raw battery status register value.

        Returns:
            int: 0=Normal, 1=Charging, 2=Full, 3=Low.
        """
        return self._bridge_call("get_bat_status")

    @property
    def capacity(self) -> int:
        """Get battery charge percentage (0–100)."""
        return self._bridge_call("get_bat_percent")

    @property
    def voltage(self) -> float:
        """Get battery voltage in volts.

        The co-processor reports in 0.1 V units (e.g. 74 → 7.4V).
        """
        raw = self._bridge_call("get_bat_volt")
        return round(raw / 10.0, 1)

    @property
    def model_name(self) -> str:
        """Get device model name.

        Returns:
            str: Always ``"Robot Shield"``.
        """
        return MODEL_NAME

    @property
    def manufacturer(self) -> str:
        """Get device manufacturer.

        Returns:
            str: Always ``"SunFounder"``.
        """
        return MANUFACTURER

    @property
    def is_ok(self) -> bool:
        """Check if battery status is normal (no warning or fault).

        Returns:
            bool: ``True`` if battery status is Normal (0).
        """
        return self.raw_status == 0

    def __str__(self) -> str:
        """Return a human-readable battery summary string.

        Returns:
            str: e.g. ``"Robot Shield SunFounder Normal 76% 7.4 V"``.
        """
        return f"{self.model_name} {self.manufacturer} {self.status} {self.capacity}% {self.voltage} V"
