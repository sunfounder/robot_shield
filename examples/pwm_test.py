"""PWM example: basic channel control.

Demonstrates writing and reading PWM frequency, pulse width, and duty cycle
through I2C registers via Arduino Bridge.
"""

import time

from robot_shield import PWM


def main():
    pwm = PWM(2)

    print("Setting frequency to 50 Hz on channel 2...")
    pwm.freq(50)
    print(f"Current frequency: {pwm.freq()} Hz")

    print("\nSetting pulse width to 1500 us (center)...")
    pwm.pulse_width(1500)
    print(f"Current pulse width: {pwm.pulse_width()} us")

    print("\nSetting duty cycle to 7.5% (center for 50 Hz)...")
    pwm.pulse_width_percent(7.5)
    print(f"Current duty cycle: {pwm.pulse_width_percent():.1f}%")

    print("\nEnabling PWM channel 2...")
    pwm.enable(True)
    print(f"Channel enabled: {pwm.enable()}")
    time.sleep(0.5)

    print("\nSweeping pulse width 500–2500 us...")
    for pw in range(500, 2501, 400):
        pwm.pulse_width(pw)
        print(f"  pulse_width = {pw} us")
        time.sleep(0.3)

    pwm.enable(False)
    print(f"\nChannel disabled: {not pwm.enable()}")


if __name__ == "__main__":
    main()
