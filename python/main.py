import argparse
import atexit
import curses
from datetime import timedelta
import prettytable
import recur
import random
import socketio
import server
import time


class Client:
    def __init__(self, passage: str, window, socket):
        self.passage = passage

        self.socket = socket
        self.window = window
        self.state = None

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

        if self.passage[self.last_correct_character] == char:
            self.is_wrong = False
            self.last_correct_character += 1
        else:
            self.is_wrong = True
            self.errors += 1

        self.total += 1

        self.printStatus()

        if self.socket.connected:
            self.socket.send(self.serialize())

        return self.isOver()

    def statistics(self) -> str:
        """
            Returns current race statistics as a string.
        """

        avg_time = time.time() - self.start
        avg_speed = int((self.total - self.errors) / avg_time * (60 / 5))
        return f"{avg_speed}WPM", f"{int(avg_time)}s"

    def printStatus(self):
        """
            Prints the status of the current passage along with statistics.
        """

        table = prettytable.PrettyTable()
        table.field_names = ["SPEED", "PROGRESS", "ACCURACY", "TIME ELAPSED", "ID"]
        table.set_style(prettytable.PLAIN_COLUMNS)

        def progress_bar(percentile) -> str:
            filling_character = "●"
            filled_bars = filling_character * int(percentile*10)
            return f"({filled_bars}{'◌'*(10 - int(percentile*10))})"

        speed, time_elapsed = self.statistics()
        acc = int((self.total-self.errors)*100/self.total) if self.total else 100

        table.add_row(
            [
                speed,
                progress_bar(self.last_correct_character/len(self.passage)),
                f"{acc}%",
                time_elapsed,
                self.id,
            ]
        )

        if self.state is not None:
            table.add_row(
                [
                    self.state["speed"],
                    progress_bar(self.state["progress"]),
                    f"{self.state['acc']}%",
                    time_elapsed,
                    self.state["id"]
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
            # Glow in red if a wrong character was typed
            self.window.addstr(
                0, 0, self.passage[self.last_correct_character],
                curses.color_pair(2)
            )

        row_counter = 2
        for line in table.get_string().split("\n"):
            self.window.addstr(row_counter + offset, 0, "\t" + line)
            row_counter += 1

        self.window.addstr(row_counter + 1 + offset, 0, "\n")
        self.window.refresh()

    def isOver(self):
        """
            Returns true if the end of the passage has been reached.
        """
        return len(self.passage) == self.last_correct_character

    def serialize(self) -> str:
        return {
            "speed": self.statistics()[0],
            "progress": self.last_correct_character/len(self.passage),
            "acc": int((self.total-self.errors)*100/self.total) if self.total else 100,
            "id": self.id
        }

    def setState(self, data):
        if self.state is None:
            self.state = [data]
        self.state = data


# pass on instances to main()
# get the result client and do stuff with it


def setupClient():
    window = curses.initscr()
    # Picking a random line from a file
    # The lines are cleaned up
    try:
        passage = random.choice(
            [line.strip() for line in open("passages.txt", "r").read().split("\n") if line.strip()]
        )
    except IndexError:
        exit("Error: passages.txt must not be empty; include at least one line of text.\n")

    curses.cbreak()
    curses.noecho()
    curses.curs_set(0)

    curses.start_color()
    curses.use_default_colors()
    # Green text on the default background
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    # Default text on a red background
    curses.init_pair(2, -1, curses.COLOR_RED)
    # Default text and background colors
    curses.init_pair(3, -1, -1)

    def reset_curses_settings():
        curses.curs_set(1)
        curses.echo()
        curses.nocbreak()

    atexit.register(reset_curses_settings)

    client = Client(passage, window, socketio.Client())

    return window, client


def main(window, client, client_socket=socketio.Client()):
    loop = recur.thread(timedelta(seconds=0.01), client.printStatus)
    loop.start()

    @client.socket.event
    def message(data):
        client.setState(data)

    @client.socket.event
    def stop_race(data=None):
        client.socket.disconnect()
        loop.stop()

    while True:
        # Main loop
        char = window.getkey()

        if client.typeCharacter(char):
            if client.socket.connected:
                client_socket.emit("race_over", client.id)
            else:
                stop_race()
            break

        # if client.typeCharacter(char) or char == '\u0018':
        if char == '\u0018':
            if client.socket.connected:
                client_socket.emit("force_stop", "")
            else:
                stop_race()
            break

    client.printStatus()


def writeResults(client: Client):
    if not client.isOver():
        return

    lines = open("tmp.dat", "r").read()

    with open("tmp.dat", "w") as f:
        line = [
            client.id,
            *client.statistics(),
            str(int((client.total-client.errors)*100/client.total) if client.total else 100),
            client.passage
        ]
        f.write(lines + "\t".join(line)+"\n")


if __name__ == "__main__":
    cmd_args = argparse.ArgumentParser()
    cmd_args.add_argument("--practice", "-p", help="enter practice mode (default)", action="store_true")
    cmd_args.add_argument("--host", "-ho", help="host a multiplayer game", action="store_true")
    cmd_args.add_argument("--client", "-c", help="connect to a multiplayer game", action="store_true")
    cmd_args = cmd_args.parse_args()

    # initialize curses window and client instances
    window, client = setupClient()

    if cmd_args.host:
        # Host mode; Setup a server to host the game
        srv = recur.runThread(server.main)
        srv.start()

        client_socket = socketio.Client()
        client_socket.connect("http://127.0.0.1:5000")
        print("waiting for 1 player to connect...")

        @client_socket.event
        def start_game(data):
            print("the game is starting in a second!")
            time.sleep(1)
            main(window, client, client_socket)

    elif cmd_args.client:
        # Client mode; Connects to the host via websockets
        client_socket = socketio.Client()
        try:
            client_socket.connect("http://127.0.0.1:5000")
        except Exception as E:
            print("couldn't create a connection with the host.")
            time.sleep(1)
            main(window, client)

        @client_socket.event
        def start_game(data):
            print("the game is starting in a second!")
            time.sleep(1)
            main(window, client, client_socket)

    else:
        # Practice mode
        main(window, client)

    writeResults(client)
