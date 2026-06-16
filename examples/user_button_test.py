"""Example: UserButton usage with all callback types.

Demonstrates:
  - Basic press / release / click detection
  - Long-press detection (hold >= 2 seconds)
  - State polling (is_pressed, get_pressed_for)
  - Clean shutdown via stop()

Run on the device:
  python /app/python/examples/user_button.py or ~/ArduinoApps/uno-q-ai-robot-puls$ docker exec -it uno-q-ai-robot-puls-main-1 python ./examples/user_button.py
"""

import time
from robot_shield import UserButton


def on_press():
    print("user button press\r")


def on_release():
    print("user button release\r")


def on_click():
    print("user button click\r")


def on_press_released(state: bool):
    print(f"user button press_released \r")


def on_long_press():
    print("user button long press\r")


def on_long_press_released():
    print("user button long press released\r")


def main():
    btn = UserButton()

    # Register callbacks
    btn.set_on_press(on_press)
    btn.set_on_release(on_release)
    btn.set_on_click(on_click)
    btn.set_on_press_released(on_press_released)
    btn.set_on_long_press(on_long_press, duration=2.0)
    btn.set_on_long_press_released(on_long_press_released, duration=2.0)

    print("UserButton example running. Press the USR button to test.")
    print("  Short press (< 2s)  → click callback")
    print("  Long press  (>= 2s) → long_press + long_press_released callbacks")
    print("  Press Ctrl+C to stop.\n")

    try:
        while True:
            pressed = btn.is_pressed()
            duration = btn.get_pressed_for()
            if pressed:
                print(f"\rpressing... {duration:.1f}s", end="")
            else:
                print(f"\r idle (last pressed {duration:.1f}s)", end="")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        btn.stop()
        print("Done.")


if __name__ == "__main__":
    main()
