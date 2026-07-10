"""Battery example: read power status via I2C registers.

Demonstrates reading battery voltage, charge percentage, and health status
through the Arduino Bridge I2C interface.
"""

import time

from robot_shield import Battery


def main():
    battery = Battery()

    print(f"Battery online: {battery.online}")
    if not battery.online:
        print("WARNING: Battery is not reachable via I2C. Check Bridge connection.")
        exit(1)

    print(f"Battery present: {battery.present}")

    print("\n--- Battery Status ---")
    print(f"  Model:        {battery.model_name}")
    print(f"  Manufacturer: {battery.manufacturer}")
    print(f"  Voltage:      {battery.voltage} V")
    print(f"  Capacity:     {battery.capacity} %")
    print(f"  Status:       {battery.status}")
    print(f"  Is OK:        {battery.is_ok}")

    # Sample at 1 Hz for 5 seconds, then exit.
    print("\n--- Polling (5 seconds) ---")
    for i in range(5):
        print(f"  [{i+1}s] {battery.voltage}V  {battery.capacity}%  {battery.status}")
        time.sleep(1)

    print(f"\n{battery}")
    print("Sampling complete, exiting.")


if __name__ == "__main__":
    main()
