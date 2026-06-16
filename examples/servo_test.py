"""Servo example: angle-based control with calibration.

Demonstrates servo angle setting, range configuration, and offset calibration.
PAN servo = PWM0, TILT servo = PWM1 on the UNO Robot Shield.
"""

import time

from robot_shield import Servo

# Default configuration: ±90° range
pan = Servo(0)
tilt = Servo(1)

print("Centering both servos...")
pan.angle(0)
tilt.angle(0)
time.sleep(0.5)

# Sweep pan servo
print("\nSweeping PAN servo -90° → 90°...")
for angle in range(-90, 91, 30):
    pan.angle(angle)
    print(f"  PAN = {angle}°")
    time.sleep(0.3)

# Sweep tilt servo
print("\nSweeping TILT servo -45° → 45°...")
for angle in range(-45, 46, 15):
    tilt.angle(angle)
    print(f"  TILT = {angle}°")
    time.sleep(0.3)

# Calibrate with offset
print("\nApplying +5° offset to PAN servo...")
pan.offset(5.0)
print(f"  Offset: {pan.offset()}°")
pan.angle(0)  # will physically move to 5°
time.sleep(0.3)

# Reset offset
pan.offset(0.0)

# Custom angle range (0°–180°)
print("\nCreating servo with custom range 0°–180°...")
servo_180 = Servo(2, min=0, max=180)
servo_180.angle(0)
time.sleep(0.3)
servo_180.angle(90)
print(f"  Current angle: {servo_180.angle()}°")
time.sleep(0.3)
servo_180.angle(180)
time.sleep(0.3)

# Back to center
print("\nCentering all servos...")
pan.angle(0)
tilt.angle(0)
print("Done.")
