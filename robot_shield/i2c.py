"""I2C bus read/write via Arduino Bridge.

A clean I2C abstraction over the Arduino Bridge RPC layer. Provides the same
API as a typical smbus2 wrapper but uses Bridge.call() for communication
with the STM32U5 I2C slave at address 0x20.

Example::

    >>> from robot_shield.i2c import I2C
    >>> i2c = I2C(address=0x20)
    >>> i2c.write_byte_data(0x40, 0x01)   # enable PWM0
    >>> i2c.read_byte_data(0x21)          # read battery percent
    76
    >>> i2c.write_word_data(0x50, 0x4E20) # set PWM0 period = 20000us
    >>> i2c.read_word_data(0x50)          # read PWM0 period
    20000
    >>> i2c.is_ready()
    True
"""

import logging

from arduino.app_utils import Bridge

from ._utils import retry

logger = logging.getLogger(__name__)


class I2C:
    """I2C bus read/write via Arduino Bridge.

    Args:
        address: I2C device address (default 0x20 for Arduino UNO Robot).
                 Kept for API compatibility — the Bridge handles the
                 actual I2C addressing internally.
        bus: I2C bus number (ignored, kept for API compatibility).
    """

    RETRY = 5
    DEFAULT_BUS = 1

    def __init__(self, address=0x20, bus=DEFAULT_BUS):
        self._bus = bus
        self.address = address

    # ── byte (no register) ──────────────────────────────────────────

    @retry(RETRY)
    def write_byte(self, data):
        """Write a byte to the I2C bus (no register address).

        Note: Bridge requires a register address, so this writes to
        register 0x00 (CHIP_ID). Prefer :meth:`write_byte_data` for
        register-based operations.

        Args:
            data: byte to write.
        """
        logger.debug("write_byte: 0x%02x(%d)", data, data)
        Bridge.call("write_reg", 0x00, data)
        return True

    @retry(RETRY)
    def read_byte(self):
        """Read a byte from the I2C bus (reads register 0x00 / CHIP_ID).

        Note: Prefer :meth:`read_byte_data` for register-based operations.

        Returns:
            int: byte read.
        """
        logger.debug("read_byte")
        return Bridge.call("read_reg", str(0x00))

    # ── byte + register ─────────────────────────────────────────────

    @retry(RETRY)
    def write_byte_data(self, reg, data):
        """Write a byte to a register.

        Args:
            reg: register address.
            data: byte to write.

        Returns:
            True on success.
        """
        logger.debug("write_byte_data: reg=0x%02x data=0x%02x(%d)", reg, data, data)
        Bridge.call("write_reg", reg, data)
        return True

    @retry(RETRY)
    def read_byte_data(self, reg):
        """Read a byte from a register.

        Args:
            reg: register address.

        Returns:
            int: byte read.
        """
        logger.debug("read_byte_data: reg=0x%02x", reg)
        return Bridge.call("read_reg", str(reg))

    # ── word (16-bit) + register ────────────────────────────────────

    @retry(RETRY)
    def write_word_data(self, reg, data, lsb=False):
        """Write a 16-bit word to consecutive registers.

        Writes low byte to *reg* and high byte to *reg+1*, matching the
        little-endian register layout used by the STM32U5 I2C slave.

        Args:
            reg: starting register address (low byte).
            data: 16-bit word to write.
            lsb: if True, LSB-first byte order (swapped). Default False
                 matches the hardware register layout.

        Returns:
            True on success.
        """
        l_byte = data & 0xFF
        h_byte = (data >> 8) & 0xFF
        if lsb:
            l_byte, h_byte = h_byte, l_byte
        logger.debug("write_word_data: reg=0x%02x data=0x%04x(%d)", reg, data, data)
        Bridge.call("write_reg", reg, l_byte)
        Bridge.call("write_reg", reg + 1, h_byte)
        return True

    @retry(RETRY)
    def read_word_data(self, reg, lsb=False):
        """Read a 16-bit word from consecutive registers.

        Reads low byte from *reg* and high byte from *reg+1*.

        Args:
            reg: starting register address (low byte).
            lsb: if True, LSB-first byte order (swapped). Default False
                 matches the hardware register layout.

        Returns:
            int: 16-bit word read.
        """
        logger.debug("read_word_data: reg=0x%02x", reg)
        lo = Bridge.call("read_reg", str(reg))
        hi = Bridge.call("read_reg", str(reg + 1))
        result = ((hi or 0) << 8) | (lo or 0)
        if lsb:
            result = ((result & 0xFF) << 8) | ((result >> 8) & 0xFF)
        return result

    # ── block + register ────────────────────────────────────────────

    @retry(RETRY)
    def write_i2c_block_data(self, reg, data):
        """Write a block of bytes starting at a register.

        Args:
            reg: starting register address.
            data: list of bytes to write.

        Returns:
            True on success.
        """
        logger.debug("write_i2c_block_data: reg=0x%02x data=%s", reg, data)
        for i, byte in enumerate(data):
            Bridge.call("write_reg", reg + i, byte)
        return True

    @retry(RETRY)
    def read_i2c_block_data(self, reg, num):
        """Read a block of bytes from consecutive registers.

        Args:
            reg: starting register address.
            num: number of bytes to read.

        Returns:
            list: bytes read.
        """
        logger.debug("read_i2c_block_data: reg=0x%02x num=%d", reg, num)
        result = []
        for i in range(num):
            result.append(Bridge.call("read_reg", str(reg + i)))
        return result

    # ── device status ───────────────────────────────────────────────

    @retry(RETRY)
    def is_ready(self):
        """Check if the I2C device is ready by reading CHIP_ID (0x00).

        Returns:
            bool: True if device responds.
        """
        logger.debug("Check if 0x%02x(%d) is ready", self.address, self.address)
        try:
            Bridge.call("read_reg", str(0x00))
            return True
        except Exception:
            return False

    def is_available(self):
        """Alias for :meth:`is_ready`.

        Returns:
            bool: ``True`` if device responds.
        """
        return self.is_ready()

    @staticmethod
    def scan(bus=1, force=False):
        """Scan the I2C bus for devices.

        Note: With Bridge-based communication, only the Arduino at 0x20
        is accessible. Returns ``[0x20]`` if responsive, ``[]`` otherwise.

        Args:
            bus: I2C bus number (ignored).
            force: ignored.

        Returns:
            list: Detected device addresses.
        """
        try:
            Bridge.call("read_reg", str(0x00))
            return [0x20]
        except Exception:
            return []

    # ── convenience: auto-detect write / read ───────────────────────

    def write(self, data):
        """Write data to the I2C device, auto-detecting the format.

        ========== ===========================
        len(data)  method used
        ========== ===========================
        1 byte     :meth:`write_byte`
        2 bytes    :meth:`write_byte_data` (reg, val)
        3 bytes    :meth:`write_word_data` (reg, val16)
        4+ bytes   :meth:`write_i2c_block_data`
        ========== ===========================

        Args:
            data: int, list, or bytearray.
        """
        if isinstance(data, bytearray):
            data_all = list(data)
        elif isinstance(data, int):
            data_all = []
            if data == 0:
                data_all = [0]
            else:
                while data > 0:
                    data_all.append(data & 0xFF)
                    data >>= 8
        elif isinstance(data, list):
            data_all = data
        else:
            raise ValueError("data must be int, list, or bytearray")

        n = len(data_all)
        if n == 1:
            self.write_byte(data_all[0])
        elif n == 2:
            self.write_byte_data(data_all[0], data_all[1])
        elif n == 3:
            value = (data_all[2] << 8) | data_all[1]
            self.write_word_data(data_all[0], value)
        else:
            self.write_i2c_block_data(data_all[0], data_all[1:])

    def read(self, length=1):
        """Read bytes from the I2C device.

        Args:
            length: number of bytes to read (uses :meth:`read_byte` each).

        Returns:
            list: bytes read.
        """
        result = []
        for _ in range(length):
            result.append(self.read_byte())
        return result

    def mem_write(self, data, memaddr):
        """Write data to a specific register address.

        Args:
            data: int, list, or bytearray.
            memaddr: register address.
        """
        if isinstance(data, bytearray):
            data_all = list(data)
        elif isinstance(data, list):
            data_all = data
        elif isinstance(data, int):
            data_all = []
            if data == 0:
                data_all = [0]
            else:
                while data > 0:
                    data_all.append(data & 0xFF)
                    data >>= 8
        else:
            raise ValueError("data must be int, list, or bytearray")
        self.write_i2c_block_data(memaddr, data_all)

    def mem_read(self, length, memaddr):
        """Read data from a specific register address.

        Args:
            length: number of bytes to read.
            memaddr: register address.

        Returns:
            list: bytes read.
        """
        return self.read_i2c_block_data(memaddr, length)
