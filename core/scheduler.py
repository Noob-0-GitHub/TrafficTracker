import time

import schedule as _schedule


def schedule(interval_seconds, start_callback=None, end_callback=None):
    def decorator(func):
        def wrapper():
            if callable(start_callback):
                start_callback()
            func()
            if callable(start_callback):
                end_callback()

        _schedule.every(interval_seconds).seconds.do(wrapper)
        return wrapper

    return decorator


class Scheduler:
    def __init__(self, interval_seconds=1, call_when_started=True):
        self.running = True
        self.interval_seconds = interval_seconds
        self.call_when_started = call_when_started

    def start(self):
        if self.call_when_started:
            for job in _schedule.get_jobs():
                job.run()
        while self.running:
            _schedule.run_pending()
            time.sleep(self.interval_seconds)

    def stop(self):
        self.running = False

    def is_running(self):
        return self.running
