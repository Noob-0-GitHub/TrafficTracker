import os
from datetime import datetime

from alive_progress import alive_it

import collector
from models import parse_data, save_data
from scheduler import Scheduler, schedule

collector.print_out_response_headers = False
collector.print_out_response_body = False

os.chdir(os.path.dirname(__file__))


@schedule(20 * 60)
def main():
    collect_and_save()
    log(f"\r{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: collected")


def collect_and_save():
    for group_name, traffic_data in alive_it(collector.collect().items(), title="Collecting"):
        history_data = parse_data(f"{group_name}.json")
        history_data.append(traffic_data)
        save_data(f"{group_name}.json", history_data)


def log(*args, **kwargs):
    print(*args, **kwargs)
    pass


if __name__ == '__main__':
    scheduler = Scheduler(5, call_when_started=True)
    scheduler.start()
