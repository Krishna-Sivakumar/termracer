'''
    __author__: Krishna Sivakumar (krishnasivaprogrammer@gmail.com)
    __description__: a CLI typeracer clone
'''

from argparse import ArgumentParser
from atexit import register
import curses
from prettytable import PrettyTable, PLAIN_COLUMNS
from random import randint
from time import time


from os import path
script_path = path.dirname(path.realpath(__file__))


class RaceClient:
    """
        Represents a Race Client.
        Encapsulates a passage and statistics relevant to the race.
    """

    def __init__(self, passage: str):
        self.passage = passage

        self.state = None

        self.total, self.total_errors = 0, 0
        self.error_string = 0
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

        # If there are no remaining errors and the correct character was entered
        if self.error_string == 0 and self.passage[self.last_correct_character] == char:
            self.last_correct_character += 1

        # if the entered key is a backspace, delete an error if there is any
        # the backspace keypress is not counted, so self.total is decremented here
        elif char == '\u007f':
            self.error_string = max(self.error_string-1, 0)

            # Backspace is not counted towards the total keys pressed
            self.total -= 1

        # A wrong character was entered
        else:
            # The number of errors can only be as long as the passage left
            self.error_string = min(
                self.error_string+1, len(self.passage)-self.last_correct_character)

            # Total errors incremeneted (for statistics)
            self.total_errors += 1

        # Update the total number of characters
        self.total += 1

        return self.isOver()

    def statistics(self) -> str:
        """
            Returns current race statistics as a string.
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

        if self.error_string > 0:
            # Glow in red if a wrong string of characters were typed
            self.window.addstr(
                0, 0, self.passage[
                    self.last_correct_character:self.last_correct_character+self.error_string
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


def getRandomLine():
    from linecache import getline
    from subprocess import run, PIPE
    lines = run(["wc", "-l", path.join(script_path, "passages.txt")],
                check=True, stdout=PIPE).stdout
    lines = int(lines.decode().split()[0])

    return getline(path.join(script_path, "passages.txt"), randint(1, lines)).strip()


def setupClient() -> RaceClient:
    # Picking a random line from a file
    # The lines are cleaned up
    '''
    try:
        passage = choice(
            [line.strip() for line in open("passages.txt", "r").read().split("\n") if line.strip()]
        )
    except IndexError:
        exit("Error: passages.txt must not be empty; include at least one line of text.\n")
    '''

    passage = getRandomLine()
    client = RaceClient(passage)

    # Return the instantiated client to play with
    return client


def startRace(client: RaceClient):
    while True:
        # Main loop

        client.printStatus()

        try:
            char = client.window.getkey()
        except curses.error:
            continue

        if client.typeCharacter(char):
            break

    client.printStatus()
    return client


def writeResultsToFile(client: RaceClient):
    if not client.isOver():
        return

    if path.exists(path.join(script_path, "tmp.dat")):
        lines = open(path.join(script_path, "tmp.dat")).read()
    else:
        lines = ""

    with open(path.join(script_path, "tmp.dat"), "w") as f:
        line = [
            client.id,
            *client.statistics(),
            str(int((client.total-client.total_errors) *
                    100/client.total) if client.total else 100),
            client.passage
        ]
        f.write(lines + "\t".join(line)+"\n")


def displayHistory(client: RaceClient):
    from subprocess import PIPE, Popen, run
    from re import split

    if path.exists(path.join(script_path, "tmp.dat")):
        table = PrettyTable()
        table.field_names = [
            "Player Name",
            "Speed",
            "Time Taken",
            "Accuracy",
            "Passage\n"
        ]
        table.align = "l"
        table.set_style(PLAIN_COLUMNS)

        speeds, previous_id = [], None

        with open(path.join(script_path, "tmp.dat")) as f:
            for line in reversed(f.readlines()):
                row = line.split("\t")
                id, speed, _, _, _ = row
                speeds.append(int(split('WPM$', speed)[0]))

                if id == previous_id:
                    row[0] = ""

                previous_id = id
                table.add_row(row)

        final_string = ""
        final_string += f"Average Speed: {sum(speeds)//len(speeds)}WPM\n"
        final_string += f"Races completed: {len(speeds)}\n\n"
        final_string += table.get_string()

        echo_proces = Popen(["echo", final_string], stdout=PIPE)
        run(["less", "-S"], stdin=echo_proces.stdout)

    else:
        print("No games have been played yet.")


if __name__ == "__main__":
    cmd_args = ArgumentParser()
    cmd_args.add_argument(
        "--practice", "-p", help="enter practice mode (default)", action="store_true")
    cmd_args.add_argument("--history", "-hi",
                          help="view race history", action="store_true")
    cmd_args.add_argument("--name", help="set your username")
    cmd_args.add_argument(
        "--host", "-ho", help="host a multiplayer game", action="store_true")
    cmd_args.add_argument(
        "--client", "-c", help="connect to a multiplayer game", action="store_true")
    cmd_args = cmd_args.parse_args()

    # initialize curses window and client instances
    race_client = setupClient()

    if cmd_args.name:
        from json import dumps
        race_client.id = cmd_args.name
        open(path.join(script_path, "session.json"), "w").write(
            dumps({"id": cmd_args.name})
        )

    else:
        from json import loads, dumps
        if path.exists(path.join(script_path, "session.json")):
            session = loads(
                open(path.join(script_path, "session.json")).read())
            race_client.id = session["id"]

    if cmd_args.host:
        # Host mode; Setup a server to host the game
        pass

    elif cmd_args.client:
        # Client mode; Connects to the host via websockets
        pass

    elif cmd_args.history:
        displayHistory(race_client)

    else:
        # Practice mode
        race_client.initWindow()
        client = startRace(race_client)
        writeResultsToFile(client)
