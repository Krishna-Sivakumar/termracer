from threading import Thread, Event
from datetime import timedelta


class thread(Thread):
    def __init__(self, interval: timedelta, callback):
        Thread.__init__(self)
        self.stopped = Event()
        self.interval = interval
        self.callback = callback

    def stop(self):
        self.stopped.set()
        self.join()

    def run(self):
        while not self.stopped.wait(self.interval.total_seconds()):
            self.callback()


class runThread(Thread):
    def __init__(self, callback):
        Thread.__init__(self)
        self.callback = callback

    def stop(self):
        self.join()

    def run(self):
        self.callback()
