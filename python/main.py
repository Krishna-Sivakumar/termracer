import atexit
import curses
import random
import time
import threading


class Client:
    def __init__(self, passage: str):
        self.passage = passage

        self.total, self.errors = 0, 0
        self.last_correct_character = 0
        self.is_wrong = False
        self.id = f"player{random.randint(1, 1000)}"
        self.start = time.time()

    def typeCharacter(self, char: str) -> bool:
        """
            Checks the typed character w.r.t the passage.
            Returns true if the end of the passage has been reached.
        """

        if len(self.passage) == self.last_correct_character:
            return True

        if self.passage[self.last_correct_character] == char:
            self.is_wrong = False
            self.last_correct_character += 1
        else:
            self.is_wrong = True
            self.errors += 1

        self.total += 1

        self.printStatus()

        return self.isOver()

    def statistics(self) -> str:
        """
            Returns current race statistics as a string.
        """

        avg_time = time.time() - self.start
        avg_speed = int((self.total - self.errors) / avg_time * (60 / 5))
        return f"Speed: {avg_speed}WPM", f"Time Elapsed: {int(avg_time)}s\n"

    def printStatus(self):
        """
            Prints the status of the current passage along with statistics.
        """

        def progress_bar(i) -> str:
            bars = "=" * int(i)
            return f"[{bars}{' '*(10-int(i))}]"

        # window.addstr(0, 0, self.passage[:self.last_correct_character], curses.color_pair(1) | curses.A_BOLD)
        window.erase()
        _, width = window.getmaxyx()
        offset = (len(self.passage) // width)
        if self.isOver():
            window.addstr(0, 0, self.passage, curses.color_pair(1) | curses.A_BOLD)
            window.scrollok(1)
        else:
            offset = 0
            window.addstr(0, 0, self.passage[self.last_correct_character:][:width])
            window.scrollok(1)

        if self.is_wrong:
            window.addstr(0, 0, self.passage[self.last_correct_character], curses.color_pair(2))

        speed, time_elapsed = self.statistics()
        window.addstr(2 + offset, 0, speed, curses.A_BOLD)
        window.addstr(4 + offset, 0, f"Progress: {progress_bar(self.last_correct_character*10/len(self.passage))}")
        window.addstr(6 + offset, 0, time_elapsed)
        if self.total > 0:
            window.addstr(7 + offset, 0, f"Accuracy: {int((self.total-self.errors)*100/self.total)}%")
        window.refresh()

    def isOver(self):
        """
            Returns true if the end of the passage has been reached.
        """
        return len(self.passage) == self.last_correct_character

    def serialize(self) -> str:
        return vars(self)


passage = random.choice(open("passages.txt", "r").read().split("\n"))
client = Client(passage)

window = curses.initscr()
curses.cbreak()
curses.noecho()
curses.curs_set(0)

curses.start_color()
curses.use_default_colors()
curses.init_pair(1, curses.COLOR_GREEN, -1)
curses.init_pair(2, -1, curses.COLOR_RED)
curses.init_pair(3, -1, -1)


def exit_func():
    curses.curs_set(1)
    curses.echo()
    curses.nocbreak()


atexit.register(exit_func)


def print_stats():
    thread = threading.Timer(0.08, print_stats)
    thread.start()
    client.printStatus()

    if client.isOver():
        thread.cancel()


print_stats()

while True:
    # Main loop
    char = window.getkey()

    client.printStatus()

    if ord(char) == 4:
        exit()

    if client.typeCharacter(char):
        break

client.printStatus()
