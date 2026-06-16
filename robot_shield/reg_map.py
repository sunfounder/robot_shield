"""Register address map for the UNO Robot I2C slave (mirrors sketch/reg_map.h).

**Register addresses only** — this module defines *where* each register lives.
Signal values, status codes, and default settings belong in their respective
domain modules (e.g. ``pwm.py``, ``battery.py``).

Usage::

    >>> from robot_shield.reg_map import (
    ...     REG_BAT_VOLT, REG_BAT_PERCENT, REG_BAT_STATUS,
    ... )
    >>> bat_volt = i2c.read_byte_data(REG_BAT_VOLT)
"""

# ===========================================================================
#  System registers (0x00–0x0C)
# ===========================================================================

REG_CHIP_ID          = 0x00   # Chip identification code
REG_I2C_ADDR         = 0x01   # I2C address configuration
REG_IO_VOLT          = 0x02   # IO voltage setting
REG_IOREF_VOLT       = 0x03   # IOREF voltage readout
REG_FW_VER_MAJOR     = 0x04   # Firmware version — major
REG_FW_VER_MINOR     = 0x05   # Firmware version — minor
REG_FW_VER_PATCH     = 0x06   # Firmware version — patch
REG_POWER_SWITCH     = 0x07   # Power switch control
REG_AUTO_SHUTDOWN    = 0x08   # Auto-shutdown configuration
REG_SYS_CTRL         = 0x09   # System control
REG_SHUTDOWN_SIGNAL  = 0x0A   # Write to trigger PWR shutdown
REG_KEY_SIGNAL       = 0x0B   # PWR button event
REG_USR_KEY_SIGNAL   = 0x0C   # USR button event

# ===========================================================================
#  Battery / power registers (0x20–0x23)
# ===========================================================================

REG_BAT_VOLT         = 0x20   # Battery voltage (unit: 0.1 V)
REG_BAT_PERCENT      = 0x21   # Battery charge percentage (0–100)
REG_BAT_STATUS       = 0x22   # Battery status flags
REG_ARDUINO_CURRENT  = 0x23   # Arduino board current draw

# ===========================================================================
#  Raw ADC registers (0x25–0x2A) — 16-bit, little-endian
# ===========================================================================

REG_RAW_BAT_ADC_L    = 0x25   # Raw battery ADC — low byte
REG_RAW_BAT_ADC_H    = 0x26   # Raw battery ADC — high byte
REG_RAW_CUR_ADC_L    = 0x27   # Raw current ADC — low byte
REG_RAW_CUR_ADC_H    = 0x28   # Raw current ADC — high byte
REG_RAW_IOREF_ADC_L  = 0x29   # Raw IOREF ADC — low byte
REG_RAW_IOREF_ADC_H  = 0x2A   # Raw IOREF ADC — high byte

