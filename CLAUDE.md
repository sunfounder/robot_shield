# CLAUDE.md

This file provides guidance to Claude Code when working with the `robot_shield` library.

## Overview

`robot_shield` is a Python hardware abstraction layer for the SunFounder Robot Shield. It communicates with an STM32U5 I2C slave (address `0x20`) via Arduino Bridge RPC — the same mechanism used by Arduino App Lab bricks.

Three-layer architecture:

```
Python (robot_shield)  ──Bridge RPC──▶  Sketch (C++)  ──I2C──▶  Registers
```

Angle↔pulse conversion and register I/O happen in the sketch. Python classes call semantic Bridge functions only.

## Public API surface

Exported from `robot_shield/__init__.py`:

| Class/Function | Module | Purpose |
|---|---|---|
| `Servo` | `servo.py` | Angle control (-90°~90°), offset calibration, custom ranges |
| `PWM` | `pwm.py` | Raw PWM — frequency, pulse width, duty cycle, enable (12 channels) |
| `Motor` | `motor.py` | DC motor — power (-100~100), forward/reverse/brake, 4 channels |
| `Battery` | `battery.py` | Voltage, capacity, status via I2C registers |
| `UserButton` | `user_button.py` | USR button polling with 6 callback types |
| `I2C` | `i2c.py` | Low-level register read/write via Bridge RPC |
| `setup_audio_output` | `audio.py` | Qualcomm Codec ALSA mixer config |
| `reg_map` | `reg_map.py` | Register address constants (28 registers) |

## Internal modules (not exported)

| Module | Purpose |
|---|---|
| `_utils.py` | `constrain()`, `mapping()`, `retry(times, delay)` decorator, `LazyReader`, `run_command()` |
| `_version.py` | `__version__` string |

## Architecture rules

### All I2C goes through `I2C` class → `Bridge.call()`

```python
from robot_shield.i2c import I2C
i2c = I2C(address=0x20)
i2c.write_byte_data(0x40, 0x01)    # write 1 byte to register
i2c.read_word_data(0x50)           # read 16-bit LE from register pair
```

Every method in `I2C` uses the `@retry(5)` decorator (0.1s delay, 5 attempts). The `Bridge` import is `from arduino.app_utils import Bridge` — this is only available inside Arduino App Lab containers.

### Servo angle ↔ pulse mapping

Happens in sketch `servo_control.cpp`, not Python:

```
-90° → 500μs    0° → 1500μs    +90° → 2500μs
```

`Servo.angle()` calls `Bridge.call("servo_set_angle", channel, angle)`. If `angle=None`, it calls `servo_get_angle`.

Offset calibration: `calibrated = angle + offset`, clamped to `[min, max]`. Both `angle()` and `offset()` are getter/setter combos — call with no arg to read, with arg to write.

### Motor uses dual-PWM H-bridge

| Motor | Forward PWM | Reverse PWM | Register pairs |
|---|---|---|---|
| M0 | PWM4 | PWM5 | 0x44/0x45 |
| M1 | PWM6 | PWM7 | 0x46/0x47 |
| M2 | PWM8 | PWM9 | 0x48/0x49 |
| M3 | PWM10 | PWM11 | 0x4A/0x4B |

Motor frequency is fixed at 100Hz (10000μs period) in sketch `motor_control.cpp`. `Motor.power(0)` = brake (both phases low). `is_reversed` flag swaps forward/reverse.

### PWM channel layout

12 channels (PWM0–PWM11). Each channel has:
- Enable: register `0x40 + n` (1 byte)
- Period: registers `0x50 + 2n` (16-bit LE, default 20000μs = 50Hz)
- Pulse: registers `0x70 + 2n` (16-bit LE, range 500–2500μs)

Servo PAN = PWM0, Servo TILT = PWM1.

### Battery reads I2C directly (not Bridge servo/motor calls)

```python
bat = Battery()
bat.voltage    # reads REG_BAT_VOLT (0x20), unit 0.1V → returns float
bat.capacity   # reads REG_BAT_PERCENT (0x21)
bat.status     # reads REG_BAT_STATUS (0x22) → "Normal" / "Low Voltage" / etc.
```

### UserButton polls register 0x0C at 100ms

Signal values:
- `0x01` — press (PTT start)
- `0x02` — release (PTT stop)

Uses a generation counter to prevent stale long-press timers. Six callback types: `on_press`, `on_release`, `on_click`, `on_press_released(bool)`, `on_long_press(duration=2.0)`, `on_long_press_released(duration=2.0)`.

## Dependencies

- **Runtime**: `arduino.app_utils.Bridge` (Arduino App Lab framework, container-only)
- **No PyPI dependencies** in `[project] dependencies` (empty list)
- **Dev**: `pytest>=7`

## Testing

Examples live in `examples/`:

```bash
docker exec uno-q-ai-robot-puls-main-1 python /app/python-libraries/robot_shield/examples/servo_test.py
docker exec uno-q-ai-robot-puls-main-1 python /app/python-libraries/robot_shield/examples/motor_test.py
docker exec uno-q-ai-robot-puls-main-1 python /app/python-libraries/robot_shield/examples/pwm_test.py
docker exec uno-q-ai-robot-puls-main-1 python /app/python-libraries/robot_shield/examples/battery_status.py
docker exec uno-q-ai-robot-puls-main-1 python /app/python-libraries/robot_shield/examples/user_button_test.py
```

All examples require the container to be running (they depend on `Bridge`).

## Code conventions

- Getter/setter combo pattern: `angle(45)` sets, `angle()` gets — same method, arity check
- Registry-style classes: `Servo(0)` and `Servo(1)` create independent instances but share the same I2C bus
- All Bridge calls go through `I2C` methods, never call `Bridge.call()` directly outside `i2c.py`
- Public classes log to `logging.getLogger(__name__)`; no `print()` in library code
