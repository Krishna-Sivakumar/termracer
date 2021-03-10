from atexit import register
import curses
from prettytable import PrettyTable, PLAIN_COLUMNS
from random import randint
from time import time


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

        # If CTRL X is pressed, finish the race by returning True
        if char == '\u0018':
            return True

        # If the correct character is entered and there are no errors left
        if self.passage[self.last_correct_character] == char and self.undeleted_errors == 0:
            self.last_correct_character += 1

        # if the entered key is a backspace, delete an error if there is any
        # the backspace keypress is not counted, so total is decremented here
        elif char == '\u007f':
            self.undeleted_errors = max(self.undeleted_errors-1, 0)

            # Backspace is not counted towards the total keys pressed
            self.total -= 1

        # A wrong character was entered
        else:
            # The number of errors can only be as long as the passage left
            self.undeleted_errors = min(
                self.undeleted_errors+1, len(self.passage)-self.last_correct_character)

            # Total errors incremeneted (for statistics)
            self.total_errors += 1

        # Update the total number of characters
        self.total += 1

        return self.isOver()

    def statistics(self) -> str:
        """
            Returns current race statistics as a tuple of strings.
        """

        avg_time = time() - self.start
        avg_speed = int((self.total - self.total_errors) / avg_time * (60 / 5))
        return f"{avg_speed}WPM", f"{int(avg_time)}s"

    def printStatus(self):
        """
            Prints the status of the current passage along with statistics.
        """

        def progress_bar(percentile) -> str:
            filling_character = "●"
            filled_bars = filling_character * int(percentile*10)
            return f"({filled_bars}{'◌'*(10 - int(percentile*10))})"

        speed, time_elapsed = self.statistics()
        acc = int((self.total-self.total_errors)*100 /
                  self.total) if self.total else 100

        self.table.clear_rows()

        self.table.add_row(
            [
                speed,
                progress_bar(self.last_correct_character/len(self.passage)),
                f"{acc}%",
                time_elapsed,
                self.id,
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
            self.window.addstr(
                0, 0, self.passage[
                    self.last_correct_character:self.last_correct_character+self.undeleted_errors
                ],
                curses.color_pair(2)
            )

        row_counter = 2
        for line in self.table.get_string().split("\n"):
            self.window.addstr(row_counter + offset, 0, "\t" + line[:width])
            row_counter += 1

        row_counter += 1
        self.window.addstr(row_counter + offset, 0, "Press ^X to exit")
        row_counter += 1

        self.window.addstr(row_counter + 1 + offset, 0, "\n")
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

        self.window.nodelay(True)

        def reset_curses_settings():
            curses.curs_set(1)
            curses.echo()
            curses.noraw()

        register(reset_curses_settings)

    def serialize(self) -> str:
        """
            Serializes the client into a dictionary.
        """
        return {
            "speed": self.statistics()[0],
            "progress": self.last_correct_character/len(self.passage),
            "acc": int((self.total-self.total_errors)*100/self.total) if self.total else 100,
            "id": self.id
        }
