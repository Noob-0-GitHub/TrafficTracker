import functools
import time
from typing import Callable

import schedule as schedule_lib


def get_jobs() -> list:
    return list(schedule_lib.get_jobs())


def schedule(interval_minutes, start_on_full_hour=False, start_callback=None, end_callback=None) -> Callable:
    def decorator(func) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if callable(start_callback):
                start_callback()
            _return = func(*args, **kwargs)
            if callable(start_callback):
                end_callback()
            return _return

        if start_on_full_hour:
            for i in range(59 // interval_minutes + 1):
                schedule_lib.every().hour.at(f":{str(i * interval_minutes).zfill(2)}").do(wrapper)
        else:
            schedule_lib.every(interval_minutes).minutes.do(wrapper)
        return wrapper

    return decorator


class Scheduler:
    def __init__(self, interval_seconds=1, call_when_started=False):
        self.running = True
        self.interval_seconds = interval_seconds
        self.call_when_started = call_when_started

    def start(self):
        if self.call_when_started:
            for job in schedule_lib.get_jobs():
                job.run()
        while self.running:
            schedule_lib.run_pending()
            time.sleep(self.interval_seconds)

    def stop(self):
        self.running = False

    def is_running(self):
        return self.running


if __name__ == '__main__':
    schedule(20, start_on_full_hour=True)(time.time)
    print(*[a + b for a, b in zip(*[iter(str(schedule_lib.get_jobs()).strip("[]").split(", "))] * 2)], sep="\n")
    # Scheduler(1).start()
