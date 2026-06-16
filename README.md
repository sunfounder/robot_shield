# robot_shield

Hardware control library for the SunFounder Robot Shield — servo, PWM, motor, battery, audio, and button control via I2C registers through Arduino Bridge RPC.

## Modules

| Class / Function | Purpose |
|---|---|
| `Servo` | Angle control (-90° to +90°) with offset calibration |
| `PWM` | Raw PWM channel control — frequency, pulse width, enable |
| `Motor` | DC motor control — forward, reverse, brake (-100% to +100%) |
| `Battery` | Battery telemetry — voltage, capacity percentage, status |
| `UserButton` | USR button polling with click/long-press callbacks |
| `setup_audio_output()` | Qualcomm Codec ALSA mixer setup (LineOut playback + SoundWire mic capture) |
| `I2C` | Low-level I2C register read/write via Arduino Bridge RPC |
| `reg_map` | I2C register address constants (0x00–0x2A) |

## Architecture

Three-layer design:

```
Python (application)          Sketch (control)                I2C (transport)
Servo/PWM/Motor  ──Bridge RPC──▶  servo/pwm/motor_control  ──▶  registers
```

Python classes call semantic Bridge functions (`servo_set_angle`, `pwm_set_pulse`, `motor_set_power`). Angle-to-pulse conversion and register writes happen in the sketch.

## Usage

### Servo

```python
from robot_shield import Servo

servo = Servo(0)        # PWM channel 0, range -90° to +90°
servo.angle(0)          # center
servo.angle(-45)        # left 45°
servo.offset(5.0)       # calibrate +5°
```

Angle mapping: -90° → 500 μs, 0° → 1500 μs, +90° → 2500 μs (linear).

### Motor

```python
from robot_shield import Motor

motor = Motor("M0")     # M0–M3, maps to PWM4–PWM11
motor.power(50)         # forward 50%
motor.power(-30)        # reverse 30%
motor.power(0)          # brake
```

### PWM

```python
from robot_shield import PWM

pwm = PWM(2)
pwm.freq(50)            # 50 Hz
pwm.pulse_width(1500)   # 1500 μs center
pwm.enable(True)        # turn on
```

### Battery

```python
from robot_shield import Battery

battery = Battery()
print(battery.voltage)   # e.g. 7.4 V
print(battery.capacity)  # e.g. 85 %
print(battery.status)    # e.g. "Normal"
```

### UserButton

```python
from robot_shield import UserButton

btn = UserButton()
btn.set_on_long_press(lambda: print("PTT start"), duration=2.0)
btn.set_on_click(lambda: print("clicked"))
print(btn.is_pressed())
```

### Audio

```python
from robot_shield import setup_audio_output

setup_audio_output()    # configure Qualcomm Codec ALSA mixer paths
```

Called automatically at startup by `main.py`.

## Channel Mapping

### Servo

| Servo | PWM Channel | Control Reg | Period Reg | Pulse Reg |
|-------|-------------|-------------|------------|-----------|
| PAN | 0 | 0x40 | 0x50–0x51 | 0x70–0x71 |
| TILT | 1 | 0x41 | 0x52–0x53 | 0x72–0x73 |

### Motor

| Motor | PWM Channels |
|-------|-------------|
| M0 | PWM4 + PWM5 |
| M1 | PWM6 + PWM7 |
| M2 | PWM8 + PWM9 |
| M3 | PWM10 + PWM11 |

## Dependencies

- Arduino Bridge RPC (`/var/run/arduino-router.sock`)
- ALSA utilities (`amixer`) for audio setup
