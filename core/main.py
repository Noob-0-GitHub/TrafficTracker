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
    log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: collected")


def collect(repeat=3):
    try:
        for _ in range(repeat):
            try:
                return collector.collect(progress_wrapper=lambda _obj: alive_it(_obj, title="Collecting"))
            except Exception as e:
                log(e)
        return None
    except Exception as e:
        log(e)
        return None


def collect_and_save(repeat=3):
    for group_name, traffic_data in alive_it(collect(repeat=repeat).items(), title="Saving"):
        if traffic_data:
            for _ in range(repeat):
                try:
                    history_data = parse_data(f"{group_name}.json")
                    history_data.append(traffic_data)
                    save_data(f"{group_name}.json", history_data)
                    break
                except Exception as e:
                    log(e)
            else:
                log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: failed to save {group_name}")
                return
            log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: saved {group_name}")
        else:
            log(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: failed to collect {group_name}")


def log(*args, **kwargs):  # todo: "on 0" bug fix
    print(*args, **kwargs)
    # print("1")
    # print("1")
    # print(args[1])


if __name__ == '__main__':
    scheduler = Scheduler(5, call_when_started=True)
    scheduler.start()
