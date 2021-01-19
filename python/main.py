import sys
import time
import tty
import termios
from typing import List


fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)


def enable_raw_mode():
    tty.setraw(fd)


def disable_raw_mode():
    termios.tcsetattr(fd, termios.TCSAFLUSH, old_settings)


def statistics(speeds: List[int]):
    avg_speed = sum(speeds) / len(speeds)
    pass


speeds = []
passage = ""
last_correct_character = None  # An index to the last correctly entered character

while True:
    # Main loop
    if input():
        break

# print(statistics(speeds))
