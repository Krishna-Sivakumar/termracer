from atexit import register
import curses
from typing import Dict
from prettytable import PrettyTable, PLAIN_COLUMNS
from random import randint
from time import time


BACKSPACE = "\u007f"
CTRLW = "\u0017"
CTRLC = "\u0003"


def counter(init: int = 0, step: int = 1):
    while True:
        yield init
        init += step


class RaceClient:
    """
        Represents a Race Client.
        Encapsulates a passage and statistics relevant to the race.
    """

    def __init__(self, passage: str):
        self.passage = passage

        self.state = None

        self.total, self.total_errors = 0, 0
        self.undeleted_errors = 0
        self.last_correct_character = 0
        self.id = f"player{randint(1, 1000)}"
        self.start = time()

        self.table = PrettyTable()
        self.table.field_names = [
            "SPEED", "PROGRESS", "ACCURACY", "TIME ELAPSED", "ID"]
        self.table.set_style(PLAIN_COLUMNS)

    def typeCharacter(self, char: str) -> bool:
        """
            Enters a character into the passage,
            and checks if the correct character has been entered.
            Returns True if the end of the passage has been reached.
        """

        # If the passage has been completed, return True
        if self.isOver():
            return True

        # If CTRL C is pressed, finish the race by returning True
        if char == CTRLC:
            return True

        # If the correct character is entered and there are no errors left
        if self.passage[self.last_correct_character] == char and self.undeleted_errors == 0:
            self.last_correct_character += 1

        # if the entered key is a backspace, delete an error if there is any
        # the backspace keypress is not counted, so total is decremented here
        elif char == BACKSPACE:
            self.undeleted_errors = max(self.undeleted_errors-1, 0)

            # Backspace is not counted towards the total keys pressed
            self.total -= 1

        # All undeleted errors are cleared with the CTRLW keypress
        elif char == CTRLW:
            self.undeleted_errors = 0
            self.total -= 1

        # A wrong character was entered
        else:
            # The number of errors can only be as long as the passage left
            self.undeleted_errors = min(
                self.undeleted_errors+1,
                len(self.passage) - self.last_correct_character
            )

            # Total errors incremeneted (for statistics)
            self.total_errors += 1

        # Update the total number of characters
        self.total += 1

        return self.isOver()

    def statistics(self) -> Dict[str, int]:
        """
            Returns the current race statistics.
            Dict Keys:
            {
                speed
                time_elapsed
                total_errors
                total_characters_typed
                accuracy
            }
        """

        avg_time = time() - self.start
        avg_speed = int((self.total - self.total_errors) / avg_time * (60 / 5))

        if self.total:
            accuracy = int((self.total-self.total_errors)*100/self.total)
        else:
            accuracy = 100
        result = {
            "speed": avg_speed,
            "time_elapsed": int(avg_time),
            "total_errors": self.total_errors,
            "total_characters_typed": self.total,
            "accuracy": accuracy
        }
        return result

    def printStatus(self):
        """
            Prints the status of the current passage along with statistics.
        """

        def progress_bar(percentile) -> str:
            filling_character = "●"
            filled_bars = filling_character * int(percentile*10)
            return f"({filled_bars}{'◌'*(10 - int(percentile*10))})"

        statistics = self.statistics()
        speed = statistics["speed"]
        time_elapsed = statistics["time_elapsed"]
        acc = statistics["accuracy"]

        self.table.clear_rows()

        self.table.add_row(
            [
                f"{speed}WPM",
                progress_bar(self.last_correct_character/len(self.passage)),
                f"{acc}%",
                f"{time_elapsed}s",
                self.id,
            ]
        )

        if self.state is not None:
            for key, val in self.state.items():
                if not key == self.id:
                    self.table.add_row(
                        [
                            f"{val['speed']}WPM",
                            progress_bar(val['progress']),
                            f"{val['accuracy']}%",
                            f"{val['time_elapsed']}s",
                            key
                        ]
                    )

        # Clear the screen
        self.window.erase()

        # Get terminal window dimensions
        _, width = self.window.getmaxyx()

        # Calculate the offset of stats
        offset = (len(self.passage) // width)

        if self.isOver():
            # Print the full passage on screen
            self.window.addstr(0, 0, self.passage,
                               curses.color_pair(1) | curses.A_BOLD)
            self.window.scrollok(1)
        else:
            # Print only a section of the text, as long as the terminal's width
            offset = 0
            self.window.addstr(
                0, 0, self.passage[self.last_correct_character:][:width])
            self.window.scrollok(1)

        if self.undeleted_errors > 0:
            # Glow in red if a wrong string of characters were typed
            lcc, ude = self.last_correct_character, self.undeleted_errors
            self.window.addstr(
                0, 0, self.passage[lcc:lcc+ude],
                curses.color_pair(2)
            )

        # Initialize row counter
        row_counter = counter(2, 2)
        for line in self.table.get_string().split("\n"):
            self.window.addstr(next(row_counter) + offset,
                               0, f"{' ' * 4}{line}"[:width])

        self.window.addstr(next(row_counter) + offset, 0,
                           "Press ^W to clear errors")

        self.window.addstr(next(row_counter) + offset, 0, "Press ^C to exit")

        self.window.addstr(next(row_counter) + offset, 0, "\n")
        self.window.refresh()

    def isOver(self):
        """
            Returns true if the end of the passage has been reached.
        """
        return len(self.passage) == self.last_correct_character

    def initWindow(self):
        """
            Initializes a curses window with raw mode and colors.
        """
        self.window = curses.initscr()

        # sets raw and noecho modes to the terminal
        curses.raw()
        curses.noecho()
        curses.curs_set(0)

        # starts color configuration (I presume?)
        curses.start_color()
        curses.use_default_colors()
        # Green text on the default background
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        # Default text on a red background
        curses.init_pair(2, -1, curses.COLOR_RED)
        # Default text and background colors
        curses.init_pair(3, -1, -1)
        # Default text on a cyan background
        curses.init_pair(4, -1, curses.COLOR_BLUE)

        self.window.nodelay(True)

        def reset_curses_settings():
            curses.curs_set(1)
            curses.echo()
            curses.noraw()

        register(reset_curses_settings)

    def serialize(self):
        """
            Serializes the statistical info into a dictionary.
            {
                speed
                time_elapsed
                total_errors
                total_characters_typed
                accuracy

                progress
                id
            }
        """

        serial_result = self.statistics()
        serial_result.update({
            "progress": self.last_correct_character/len(self.passage),
            "id": self.id,
        })

        return serial_result

    def setSocket(self, socket):
        pass

    def dumpDataToServer(self):
        pass

    def sendTerminationMessage(self):
        pass
