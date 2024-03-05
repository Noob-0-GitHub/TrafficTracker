import json
import os
import warnings
from datetime import datetime

from alive_progress import alive_it

import collector
from scheduler import Scheduler, schedule

collector.print_out_response_headers = False
collector.print_out_response_body = False

os.chdir(os.path.dirname(__file__))
data_folder_path = os.path.abspath(os.path.join("..", "data"))


def parse_json(file_path):
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            return json_data
    except FileNotFoundError:
        log(f"file '{file_path}' not found, empty dictionary instead.")
        return {}
    except json.JSONDecodeError as e:
        warnings.warn(f"Error parsing JSON file: {e}\nempty dictionary instead")
        return {}


def save_json(file_path, data, indent=None):
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, default=handle_non_serializable, indent=indent)
    except Exception as e:
        log(f"Error saving JSON file: {e}")


def handle_non_serializable(obj):
    """处理无法序列化的对象"""
    if isinstance(obj, (set,)):
        return list(obj)
    else:
        # raise TypeError(f"无法序列化对象: {obj}")
        warnings.warn(f"无法序列化对象: {obj}", RuntimeWarning)
        return "__non_serializable__"


def parse_data(file_name):
    file_path = os.path.join(data_folder_path, file_name)
    parsed = parse_json(file_path)
    return parsed if len(parsed) else []


def save_data(file_name, data):
    file_path = os.path.join(data_folder_path, file_name)
    save_json(file_path, data)


@schedule(20 * 60)
def main():
    # log(f"\r{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: collecting...")
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
