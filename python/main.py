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


class Client:
    def __init__(self, passage: str):
        self.passage = passage

        self.state = None

        self.total, self.errors = 0, 0
        self.error_string = 0
        self.last_correct_character = 0
        self.is_wrong = False
        self.id = f"player{randint(1, 1000)}"
        self.start = time()

        self.table = PrettyTable()
        self.table.field_names = ["SPEED", "PROGRESS", "ACCURACY", "TIME ELAPSED", "ID"]
        self.table.set_style(PLAIN_COLUMNS)

    def typeCharacter(self, char: str) -> bool:
        """
            Checks the typed character w.r.t the passage.
            Returns true if the end of the passage has been reached.
        """

        if char == '\u0018':
            # If ctrl + x is pressed, stop the race
            return True

        if self.passage[self.last_correct_character] == char and self.error_string == 0:
            # if there are no errors remaining and the entered key is correct
            self.is_wrong = False
            self.last_correct_character += 1
        elif char == '\u007f':
            # if the entered key is backspace, delete an error if there is any
            self.error_string = max(self.error_string-1, 0)
            if self.error_string == 0:
                # If there are no errors left, reset the wrong status
                self.is_wrong = False

            # Backspace is not counted towards the total keys pressed
            self.total -= 1
        else:
            # A string of wrong characters have been typed
            self.is_wrong = True

            # The number of errors can only be as long as the passage left
            self.error_string = min(self.error_string+1, len(self.passage)-self.last_correct_character)

            # Total errors incremeneted (for statistics)
            self.errors += 1

        self.total += 1

        self.printStatus()

        return self.isOver()

    def statistics(self) -> str:
        """
            Returns current race statistics as a string.
        """

        avg_time = time() - self.start
        avg_speed = int((self.total - self.errors) / avg_time * (60 / 5))
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
        acc = int((self.total-self.errors)*100/self.total) if self.total else 100

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
            self.window.addstr(0, 0, self.passage, curses.color_pair(1) | curses.A_BOLD)
            self.window.scrollok(1)
        else:
            # Print only a section of the text, as long as the terminal's width
            offset = 0
            self.window.addstr(0, 0, self.passage[self.last_correct_character:][:width])
            self.window.scrollok(1)

        if self.is_wrong:
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
        self.window = curses.initscr()

        # sets cbreak and noecho modes to the terminal
        curses.cbreak()
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
            curses.nocbreak()

        register(reset_curses_settings)

    def serialize(self) -> str:
        return {
            "speed": self.statistics()[0],
            "progress": self.last_correct_character/len(self.passage),
            "acc": int((self.total-self.errors)*100/self.total) if self.total else 100,
            "id": self.id
        }


def getRandomLine():
    from linecache import getline
    from subprocess import run, PIPE
    lines = run(["wc", "-l", path.join(script_path, "passages.txt")], check=True, stdout=PIPE).stdout
    lines = int(lines.decode().split()[0])

    return getline(path.join(script_path, "passages.txt"), randint(1, lines)).strip()


def setupClient() -> Client:
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
    client = Client(passage)

    # Return the instantiated client to play with
    return client


def main(client: Client):
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


def writeResults(client: Client):
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
            str(int((client.total-client.errors)*100/client.total) if client.total else 100),
            client.passage
        ]
        f.write(lines + "\t".join(line)+"\n")


if __name__ == "__main__":
    cmd_args = ArgumentParser()
    cmd_args.add_argument("--practice", "-p", help="enter practice mode (default)", action="store_true")
    cmd_args.add_argument("--history", "-hi", help="view race history", action="store_true")
    cmd_args.add_argument("--name", help="set your username")
    cmd_args.add_argument("--host", "-ho", help="host a multiplayer game", action="store_true")
    cmd_args.add_argument("--client", "-c", help="connect to a multiplayer game", action="store_true")
    cmd_args = cmd_args.parse_args()

    # initialize curses window and client instances
    client = setupClient()

    if cmd_args.name:
        from json import dumps
        client.id = cmd_args.name
        open(path.join(script_path, "session.json"), "w").write(
            dumps({"id": cmd_args.name})
        )

    else:
        from json import loads, dumps
        if path.exists(path.join(script_path, "session.json")):
            session = loads(open(path.join(script_path, "session.json")).read())
            client.id = session["id"]

    if cmd_args.host:
        # Host mode; Setup a server to host the game
        pass

    elif cmd_args.client:
        # Client mode; Connects to the host via websockets
        pass

    elif cmd_args.history:
        from subprocess import Popen, run, PIPE
        from re import split
        if path.exists(path.join(script_path, "tmp.dat")):
            table = PrettyTable()
            table.field_names = ["Player Name", "Speed", "Time Taken", "Accuracy", "Passage\n"]
            table.align = "l"
            table.set_style(PLAIN_COLUMNS)

            speeds, previous_id = [], None

            with open(path.join(script_path, "tmp.dat")) as f:
                for line in reversed(f.readlines()):
                    id, speed, tm, acc, ps = line.split("\t")
                    speeds.append(int(split("WPM$", speed)[0]))
                    if id == previous_id:
                        table.add_row(["", speed, tm, acc, ps])
                    else:
                        table.add_row([id, speed, tm, acc, ps])
                    previous_id = id
                
                stats_string = f"Average speed: {sum(speeds)//len(speeds)}WPM\nNo. of completed races: {len(speeds)}\n\n"

            cat_process = Popen(["echo", stats_string + table.get_string()], stdout=PIPE)
            run(["less", "-S"], stdin=cat_process.stdout)
        else:
            print("You haven't played any games yet.")

    else:
        # Practice mode
        client.initWindow()
        client = main(client)
        writeResults(client)

    raise SystemExit
