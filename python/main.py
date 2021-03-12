from argparse import ArgumentParser
import curses
from prettytable import PrettyTable, PLAIN_COLUMNS
from RaceClient import RaceClient


from os import path

# Geting the file path of this script
script_path = path.dirname(path.realpath(__file__))

# Path to the tmp storage file
temp_file_path = "tmp.dat"

# Path to the passages file
passages_file_path = path.join(script_path, "passages.txt")


def getRandomLine(file_path):
    """
        Picks a random line from passages.txt.
    """
    from linecache import getline
    from subprocess import run, PIPE
    from random import randint
    lines = run(["wc", "-l", file_path],
                check=True, stdout=PIPE).stdout
    lines = int(lines.decode().split()[0])

    if lines == 0:
        raise FileNotFoundError(
            "Given file is empty. (Check if the lines are separated by newline characters)")

    return getline((file_path), randint(1, lines)).strip()


def setupClient() -> RaceClient:
    """
        Instantiates a RaceClient, picks a random passage, and returns it.
    """

    passage = getRandomLine(passages_file_path)
    client = RaceClient(passage)

    return client


def startRace(client: RaceClient):
    """
        Starts the race with the passed Race Client
    """
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


def getRacesFromFile(file_name: str):
    """
        Returns lines from a file as a list of strings.
        The default file specified is tmp.dat.
    """
    lines = []
    if path.exists(path.join(script_path, file_name)):
        with open(path.join(script_path, file_name)) as f:
            lines = f.readlines()
    return lines


def writeResultsToFile(client: RaceClient):
    """
        Writes the statistics of the finished race into tmp.dat.
    """
    if not client.isOver():
        return

    client_statistics = client.statistics()

    line = [
        client.id,
        f"{client_statistics['speed']}WPM",
        f"{client_statistics['time_elapsed']}s",
        f"{client_statistics['accuracy']}%",
        client.passage
    ]

    file_path = path.join(script_path, temp_file_path)

    if path.exists(file_path):
        with open(file_path, "a+") as f:
            f.write("\t".join(line)+"\n")
    else:
        with open(file_path, "w+") as f:
            f.write("\t".join(line)+"\n")


def displayHistory(client: RaceClient):
    """
        Reads racing history from tmp.dat and outputs it to less(1).
    """
    lines = getRacesFromFile(temp_file_path)

    if len(lines) > 0:
        # Importing relevant functions and constants
        from subprocess import PIPE, Popen, run
        from re import split

        # Setting up the table to display
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

        for line in reversed(lines):
            row = line.split("\t")
            id, speed, _, _, passage = row
            speeds.append(int(split('WPM$', speed)[0]))

            if id == previous_id:
                row[0] = ""

            previous_id = id
            table.add_row(row)

        final_string = ""
        final_string += f"Average Speed: {sum(speeds)//len(speeds)}WPM\n"
        final_string += f"Races completed: {len(speeds)}\n\n"
        final_string += table.get_string()

        echo_process = Popen(["echo", final_string], stdout=PIPE)
        run(["less", "-S"], stdin=echo_process.stdout)

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
        "--file", "-f", help="Choose lines from a custom file")
    cmd_args.add_argument(
        "--host", "-ho", help="host a multiplayer game", action="store_true")
    cmd_args.add_argument(
        "--client", "-c", help="connect to a multiplayer game", action="store_true")
    cmd_args = cmd_args.parse_args()

    if cmd_args.file:
        file = cmd_args.file
        if not path.isabs(file):
            file = path.abspath(cmd_args.file)

        if path.isfile(file):
            passages_file_path = file
        else:
            raise FileNotFoundError(
                f"{file}: No such file")

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
