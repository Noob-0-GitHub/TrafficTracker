import os
import traceback
import warnings
from datetime import datetime
from threading import Thread

from flask import request, redirect, url_for, render_template, Flask
from waitress import serve

import collector
import scheduler
from models import parse_data, save_data, newest_data_file
from web_packer import dashboard_glance_data_packer, dashboard_glance_data_list_packer

os.chdir(os.path.dirname(__file__))

collector.print_out_response_headers = False
collector.print_out_response_body = False
sche_interval = 1  # seconds

app = Flask(__name__)


class Log:
    def __init__(self, path, encoding="utf-8", auto_save=True, print_out=True):
        self.path = path
        self.encoding = encoding
        self.auto_save = auto_save
        self.print_out = print_out
        self.log_queue = list()

    @staticmethod
    def message_process(message) -> str:
        return f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message}"

    def append(self, message):
        message = self.message_process(message)
        if not isinstance(message, str):
            warnings.warn(RuntimeWarning("message is not a str"))
            message = str(message)
        self.log_queue.append(message)
        if self.auto_save:
            self.save()
        if self.print_out:
            print(message)

    def save(self):
        try:
            with open(self.path, "a" if os.path.exists("log.txt") else "w", encoding=self.encoding) as f:
                f.write("\n".join(self.log_queue) + "\n")
        except Exception as e:
            warnings.warn(RuntimeWarning(e))

    def __call__(self, *args, **kwargs):
        self.append(*args, **kwargs)


def collect_group(group_name, date: (str, datetime) = None, repeat=3):
    try:
        if isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d %H:%M:%S")
        for _ in range(repeat):
            try:
                log(f"Collecting {group_name}")
                new_data = collector.collect_group(group_name)
                if new_data:
                    log(f"Collected {group_name}")
                    if date:
                        new_data['date'] = date
                    save_new_traffic(group_name, new_data)
                else:
                    log(f"Failed to collect {group_name}")
                break
            except Exception:
                error_message = traceback.format_exc()
                log(error_message)
        return {}
    except Exception:
        error_message = traceback.format_exc()
        log(error_message)
        return {}


def save_new_traffic(group_name, data, repeat=3):
    if data:
        for _ in range(repeat):
            try:
                history_data = parse_data(f"{group_name}.{datetime.now().strftime('%Y%m')}.json")
                history_data.append(data)
                save_data(f"{group_name}.{datetime.now().strftime('%Y%m')}.json", history_data)
                break
            except Exception as e:
                log(e)
        else:
            log(f"failed to save {group_name}")
            return
        log(f"saved {group_name}")
    else:
        log(f"failed to collect_all {group_name}")


def sche_collector(repeat=3):
    """Making the schedule for collecting"""
    for group in collector.get_groups():
        scheduler.schedule(group.get('collect-every-minutes'),
                           start_on_full_hour=group.get('collect-on-full-hour')
                           )(lambda: collect_group(group.get('name'), date=datetime.now(), repeat=repeat))


def app_serve(host='0.0.0.0', port=8080, **kwargs):
    serve(app, host=host, port=port, **kwargs)


@app.route('/get_data_glance')
def get_data_glance():
    return dashboard_glance_data_packer(language=request.args.get('lang', 'en'))


@app.route('/get_data_glance/<filename>')
def get_data_glance_selected(filename):
    return dashboard_glance_data_packer(filename + '.json', language=request.args.get('lang', 'en'))


@app.route('/get_data_list')
def get_data_list():
    return dashboard_glance_data_list_packer()


@app.route('/')
def index():
    return redirect(url_for('dashboard_glance_selected', _filename=newest_data_file()))


@app.route('/dashboard_glance')
def dashboard_glance():
    return redirect(url_for('dashboard_glance_selected', _filename=newest_data_file()))


@app.route('/dashboard_glance/<_filename>')  # filename without an extension
def dashboard_glance_selected(_filename):
    return render_template('dashboard_glance.html')


# todo: add dashboard_pro.html
# @app.route('/dashboard_pro')
# def dashboard_pro():
#     return render_template('dashboard_pro.html')


if __name__ == '__main__':
    # app.debug = True

    log = Log(os.path.abspath("log.txt"), auto_save=True)
    log(f"log started, saving at {log.path}")

    app_thread = Thread(target=app_serve)
    app_thread.start()
    log(f"app started in thread {app_thread}")

    sche_collector()
    log(f"collector scheduled, {scheduler.get_jobs()}")

    collector_scheduler = scheduler.Scheduler(5)
    log(f"collector_scheduler starting {collector_scheduler}")
    collector_scheduler.start()
