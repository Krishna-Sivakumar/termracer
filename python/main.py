from argparse import ArgumentParser
import curses
from prettytable import PrettyTable, PLAIN_COLUMNS
from RaceClient import RaceClient


from os import path
script_path = path.dirname(path.realpath(__file__))


def getRandomLine():
    """
        Picks a random line from passages.txt.
    """
    from linecache import getline
    from subprocess import run, PIPE
    from random import randint
    lines = run(["wc", "-l", path.join(script_path, "passages.txt")],
                check=True, stdout=PIPE).stdout
    lines = int(lines.decode().split()[0])

    return getline(path.join(script_path, "passages.txt"), randint(1, lines)).strip()


def setupClient() -> RaceClient:
    """
        Instantiates a RaceClient, picks a random passage, and returns it.
    """

    passage = getRandomLine()
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


def writeResultsToFile(client: RaceClient):
    """
        Writes the statistics of the finished race into tmp.dat.
    """
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
    """
        Reads racing history from tmp.dat and outputs it to less(1).
    """
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
