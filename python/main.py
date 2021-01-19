import time
from typing import List


def enable_raw_mode():
    pass


def disable_raw_mode():
    pass


def statistics(speeds List[int]):
    avg_speed = sum(speeds) / len(speeds)
    pass


speeds = []
passage = ""
last_correct_character = None  # An index to the last correctly entered character

while True:
    # Main loop
    if input():
        break

print(statistics(speeds))
