from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
server = SocketIO(app, channel="websocket", async_mode="gevent")

players_online = 0
races_over = set()


@server.event
def connect():
    global players_online
    if players_online == 2:
        return SocketIO.ConnectionRefusedError("no more than two players at a time :(")
    else:
        players_online += 1
        if players_online == 2:
            server.emit("start_game", "start", broadcast=True)

    print(f"player {players_online} connected")


@server.event
def message(data):
    server.send(data, broadcast=True)


@server.event
def race_over(data):
    races_over.add(data)
    if len(races_over) == players_online:
        server.emit("stop_race", "", broadcast=True)
        server.stop()


@server.event
def force_stop(data):
    server.emit("stop_race", "", broadcast=True)


'''
@server.event
def disconnect():
    global players_online
    players_online -= 1
    if players_online == 0:
        try:
            server.stop()
        except SystemExit:
            print("f")
'''


def main():
    server.run(app, host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
