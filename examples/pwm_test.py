"""PWM example: basic channel control.

Demonstrates writing and reading PWM frequency, pulse width, and duty cycle
through I2C registers via Arduino Bridge.
"""

import time

from robot_shield import PWM

# Use channel 2 (ch0=PAN, ch1=TILT are reserved by face tracking)
pwm = PWM(2)

# Set frequency to 50 Hz (standard servo)
print(f"Setting frequency to 50 Hz on channel 2...")
pwm.freq(50)
print(f"Current frequency: {pwm.freq()} Hz")

# Set pulse width
print(f"\nSetting pulse width to 1500 us (center)...")
pwm.pulse_width(1500)
print(f"Current pulse width: {pwm.pulse_width()} us")

# Set duty cycle
print(f"\nSetting duty cycle to 7.5% (center for 50 Hz)...")
pwm.pulse_width_percent(7.5)
print(f"Current duty cycle: {pwm.pulse_width_percent():.1f}%")

# Enable the channel
print(f"\nEnabling PWM channel 0...")
pwm.enable(True)
print(f"Channel enabled: {pwm.enable()}")
time.sleep(0.5)

# Sweep pulse width
print(f"\nSweeping pulse width 500–2500 us...")
for pw in range(500, 2501, 400):
    pwm.pulse_width(pw)
    print(f"  pulse_width = {pw} us")
    time.sleep(0.3)

# Disable
pwm.enable(False)
print(f"\nChannel disabled: {not pwm.enable()}")
