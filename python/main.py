import argparse
import atexit
import curses
import random
import socketio
import time
import threading


class Client:
    def __init__(self, passage: str, window, socket):
        self.passage = passage

        self.socket = socket
        self.window = window

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

        if self.isOver():
            return True

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
        return f"Speed: {avg_speed}WPM", f"Time Elapsed: {int(avg_time)}s\n"

    def printStatus(self):
        """
            Prints the status of the current passage along with statistics.
        """

        def progress_bar(percentile) -> str:
            filling_character = "▓"
            filled_bars = filling_character * 2 * int(percentile*10)
            return f"|{filled_bars}{' '*(20 - 2 * int(percentile*10))}|"

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

        speed, time_elapsed = self.statistics()
        self.window.addstr(2 + offset, 0, speed, curses.A_BOLD)

        # Print progress bar on screen
        p_bar = f"{self.id}: {progress_bar(self.last_correct_character/len(self.passage))}"
        self.window.addstr(4 + offset, 0, p_bar)

        self.window.addstr(6 + offset, 0, time_elapsed)
        if self.total > 0:
            self.window.addstr(7 + offset, 0, f"Accuracy: {int((self.total-self.errors)*100/self.total)}%\n")
        self.window.refresh()

    def isOver(self):
        """
            Returns true if the end of the passage has been reached.
        """
        return len(self.passage) == self.last_correct_character

    def serialize(self) -> str:
        return {
            "id": self.id,
            "progress": self.last_correct_character*10/len(self.passage),
            "speed": self.statistics()[0]
        }


passage = random.choice(open("passages.txt", "r").read().split("\n"))


def main(client_socket=socketio.Client()):
    window = curses.initscr()
    curses.cbreak()
    curses.noecho()
    curses.curs_set(0)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, -1, curses.COLOR_RED)
    curses.init_pair(3, -1, -1)

    client = Client(passage, window, client_socket)

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
            client.socket.disconnect()
            break

    client.printStatus()


if __name__ == "__main__":
    cmd_args = argparse.ArgumentParser()
    cmd_args.add_argument("--practice", "-p", help="enter practice mode (default)", action="store_true")
    cmd_args.add_argument("--host", "-ho", help="host a multiplayer game", action="store_true")
    cmd_args.add_argument("--client", "-c", help="connect to a multiplayer game", action="store_true")
    cmd_args = cmd_args.parse_args()

    # Check if the user wants to practice
    if cmd_args.practice:
        main()

    # Setup a server if user chooses to host a multiplayer game
    if cmd_args.host:
        print("Hosting a game...")
        print(f"IP/Port: {123213}:{324}")
        input()
    elif cmd_args.client:
        client_socket = socketio.Client()
        try:
            client_socket.connect("http://127.0.0.1:5000")
        except:
            pass
        main(client_socket)
        # Else connect to a host if the user chooses to be a client
        # Exit if the client can't connect to the host
        pass
    else:
        main()
