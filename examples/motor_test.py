"""DC Motor example: all 4 motors forward/backward/stop.

Channel mapping:
    M0 → PWM4/PWM5   M1 → PWM6/PWM7
    M2 → PWM8/PWM9   M3 → PWM10/PWM11
"""

import time

from robot_shield import Motor

m0 = Motor("M0", is_reversed=True)
m1 = Motor("M1", is_reversed=True)
m2 = Motor("M2", is_reversed=False)
m3 = Motor("M3", is_reversed=False)

try:
    for _ in range(3):
        print("Forward")
        m0.power(-50)
        m1.power(-50)
        m2.power(-50)
        m3.power(-50)
        time.sleep(1)

        print("Backward")
        m0.power(50)
        m1.power(50)
        m2.power(50)
        m3.power(50)
        time.sleep(1)

        print("Stop")
        m0.stop()
        m1.stop()
        m2.stop()
        m3.stop()
        time.sleep(1)

finally:
    m0.stop()
    m1.stop()
    m2.stop()
    m3.stop()
    time.sleep(0.1)
