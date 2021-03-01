import threading
from datetime import timedelta


class thread(threading.Thread):
    def __init__(self, interval: timedelta, callback):
        threading.Thread.__init__(self)
        self.stopped = threading.Event()
        self.interval = interval
        self.callback = callback

    def stop(self):
        self.stopped.set()
        self.join()

    def run(self):
        while not self.stopped.wait(self.interval.total_seconds()):
            self.callback()


class runThread(threading.Thread):
    def __init__(self, callback):
        threading.Thread.__init__(self)
        self.callback = callback

    def stop(self):
        self.join()

    def run(self):
        self.callback()
