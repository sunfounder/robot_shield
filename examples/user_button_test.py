"""UserButton test — press USR button to test press/release."""

from arduino.app_utils import App
from robot_shield import UserButton


def on_press():
    print("press")


def on_release():
    print("release")


def main():
    # Observer pattern: register callbacks, the library polls I2C in a
    # background thread and invokes the right callback on each button event.
    btn = UserButton()
    btn.set_on_press(on_press)
    btn.set_on_release(on_release)

    print("Press USR button to test...\n")

    App.run()


if __name__ == "__main__":
    main()
