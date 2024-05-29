import cmd
import json
import os
import re
import warnings
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta

from rich import console, table, markdown, panel
from rich import traceback as rich_traceback

os.chdir(os.path.dirname(__file__))
vault_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'vault.json'))
data_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

precision = 5
gmt_tz = 0

console0 = console.Console(record=True, style=f"on #{'282c34'}")  # atom one dark theme
rich_traceback.install(console=console0, width=console0.width, extra_lines=8, show_locals=True, theme="one-dark")


def parse_json(file_path):
    """
    Parses a JSON file and returns the parsed data, with some error handling.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The parsed JSON data, or an empty dictionary if the file is not found or cannot be parsed.
    """
    try:
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            return json_data
    except FileNotFoundError:
        warnings.warn(f"file '{file_path}' not found, empty dictionary instead.")
        return {}
    except json.JSONDecodeError as e:
        warnings.warn(f"Error parsing JSON file: {e}\nempty dictionary instead")
        return {}


def save_json(file_path, data, indent=None):
    """
    Save JSON data to a file, with some error handling.
    """
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, default=handle_non_serializable, indent=indent)
    except Exception as e:
        warnings.warn(f"Error saving JSON file: {e}")


def handle_non_serializable(obj):
    """handle non serializable object"""
    if isinstance(obj, (set,)):
        return list(obj)
    else:
        warnings.warn(f"non serializable object: {obj}", RuntimeWarning)
        return "__non_serializable__"


def parse_data(file_name):
    """
    Parse data by group name.

    Args:
        file_name (str): The name of the file to parse.

    Returns:
        list: The parsed data, or an empty list if no data was parsed.
    """
    file_path = os.path.join(data_folder_path, file_name)
    parsed = parse_json(file_path)
    return parsed if len(parsed) else []


def save_data(file_name, data):
    """
    Save data to the default data folder.
    """
    file_path = os.path.join(data_folder_path, file_name)
    save_json(file_path, data)


# def console_input(prompt: str, _console=console0, markup=True, emoji=True, password=False, stream=None):
def console_input(prompt: str):
    """
    A function that takes a prompt as input and returns the input provided by the user.
    """
    # _r = _console.input(prompt, markup=markup, emoji=emoji, password=password, stream=stream)
    _r = input(prompt)
    return _r


def find_and_sort_substrings(target: str, string_list: (list[str], set[str], tuple[str]), ignore_case=True):
    """
    find the target in string iterable, and sort the result by the position of the target in the string
    查找列表中的字符串，并按照子串在字符串中的位置排序
    :param target: the target string
    :param string_list: the string iterable
    :param ignore_case: if ignore the case
    :return: sorted string list
    """
    result = []
    if ignore_case:
        target = target.lower()

    for string in string_list:
        if target in string.lower():
            result.append(string)

    # 按照子串在字符串中的位置排序
    result.sort(key=lambda x: x.lower().find(target))

    return result


def traffic_to_gb(traffic, _prec=None) -> str:
    """
    Convert traffic from bytes to gigabytes and return the result as a string.

    Parameters:
    - traffic: the amount of traffic in bytes (int)
    - _prec: precision for formatting the result (int, optional)

    Returns:
    - str: the traffic converted to gigabytes with the specified precision
    """
    if _prec is None:
        _prec = precision
    if _prec >= 0:
        return f"{traffic / 1024 / 1024 / 1024:.{precision}f} GB"
    else:
        return f"{traffic / 1024 / 1024 / 1024} GB"


def traffic_to_mb(traffic, _prec=None) -> str:
    """
    Converts the given traffic value in bytes to megabytes.

    Args:
        traffic: The traffic value to be converted.
        _prec: The precision of the conversion, defaulting to the global variable.

    Returns:
        str: The converted traffic value in megabytes as a string.
    """
    if _prec is None:
        _prec = precision
    if _prec >= 0:
        return f"{traffic / 1024 / 1024:.{precision}f} MB"
    else:
        return f"{traffic / 1024 / 1024} MB"


def read_vault(_path: str = None, retry_count=3) -> dict:
    """
    Reads the vault data from the specified path or the default vault path if none is provided. 
    Attempts to read the data from the specified path multiple times in case of failure up to the retry count.
    Returns the vault data as a dictionary.
    """
    if _path is None:
        _path = vault_path
    for i in range(retry_count):
        try:
            with open(_path, 'r') as f:
                vault_data = json.load(f)
        except Exception as e:
            print(f'Failed to read vault.json:\n{e}')
            if i == retry_count - 1:
                raise e
        else:
            break
    return vault_data


def update_vault(vault_data, _path: str = None):
    """
    Update the vault with the given data.
    """
    if _path is None:
        _path = vault_path
    with open(_path, 'w') as f:
        json.dump(vault_data, f, indent=2)


def track_group(group_name) -> OrderedDict[str, str]:
    """return a dict of information by the group name"""

    with open(os.path.join(data_folder_path, f"{group_name}.json"), 'r') as f:
        _raw_data: list[dict] = json.load(f)
    assert isinstance(_raw_data, list)

    # collect_all data by time
    start_of_month = datetime.strptime(_raw_data[-1].get('date'), "%Y-%m-%d %H:%M:%S").replace(
        day=1, hour=0, minute=0, second=0, microsecond=0)
    data = [point for point in _raw_data if
            start_of_month <= datetime.strptime(point.get('date'), "%Y-%m-%d %H:%M:%S")]
    if len(data) <= 0:
        raise ValueError(f"No sufficient data of group {group_name} in the time interval")

    # disposal data
    latest_point = data[-1]
    latest_date = datetime.strptime(latest_point.get('date'), "%Y-%m-%d %H:%M:%S")

    traffic_limit = latest_point.get('total')
    expire_in_ts = latest_point.get('expire')
    expire = datetime.fromtimestamp(expire_in_ts)

    total_upload = latest_point.get('upload')
    total_download = latest_point.get('download')
    total_traffic = total_upload + total_download
    available_traffic = traffic_limit - total_traffic
    used_percent = total_traffic / traffic_limit
    available_percent = available_traffic / traffic_limit

    # month additional traffic is equal to the total traffic
    month_speed_of_day = total_traffic / latest_date.day
    month_traffic_predicted = month_speed_of_day * (
            start_of_month.replace(month=start_of_month.month + 1) - start_of_month).days

    start_of_week = (latest_date - timedelta(days=7)) if latest_date.day > 7 else start_of_month
    week_earliest_point = [point for point in data
                           if datetime.strptime(point.get('date'), "%Y-%m-%d %H:%M:%S") >= start_of_week][0]
    week_additional_upload_traffic = latest_point.get('upload') - week_earliest_point.get('upload')
    week_additional_download_traffic = latest_point.get('download') - week_earliest_point.get('download')
    week_additional_traffic = week_additional_upload_traffic + week_additional_download_traffic
    # todo: week prediction is incorrect
    week_speed_of_day = week_additional_traffic / (latest_date - start_of_week).days
    week_traffic_predicted = (week_speed_of_day * 7 +
                              week_earliest_point.get('upload') + week_earliest_point.get('download'))

    # todo:week prediction is incorrect
    week_traffic_predicted_by_month = total_traffic + month_speed_of_day * (latest_date - start_of_month).days
    month_traffic_predicted_by_week = total_traffic + week_speed_of_day * (start_of_month.replace(
        month=start_of_month.month + 1) - latest_date).days

    # abandon to statistics by day because of prediction inaccuracy
    # start_of_day = latest_date.replace(hour=0, minute=0, second=0, microsecond=0)
    # day_earliest_point = [point for point in data
    #                       if datetime.strptime(point.get('date'), "%Y-%m-%d %H:%M:%S") >= start_of_day][0]
    # day_additional_upload_traffic = latest_point.get('upload') - day_earliest_point.get('upload')
    # day_additional_download_traffic = latest_point.get('download') - day_earliest_point.get('download')
    # day_additional_traffic = day_additional_upload_traffic + day_additional_download_traffic
    # day_speed = day_additional_traffic / (latest_date - start_of_day).days

    track_data: OrderedDict[str, str] = OrderedDict()
    track_data['Group'] = group_name
    track_data['Expiration time'] = expire.strftime("%Y-%m-%d %H:%M:%S")
    track_data['Traffic limitation'] = traffic_to_gb(traffic_limit)
    track_data['Upload traffic used'] = traffic_to_gb(total_upload)
    track_data['Download traffic used'] = traffic_to_gb(total_download)
    track_data['Total traffic used'] = traffic_to_gb(total_traffic)
    track_data['Upload in latest 7days'] = traffic_to_gb(week_additional_upload_traffic)
    track_data['Download in latest 7days'] = traffic_to_gb(week_additional_download_traffic)
    track_data['Total in latest 7days'] = traffic_to_gb(week_additional_traffic)
    track_data['Current available traffic'] = traffic_to_gb(available_traffic)
    track_data['Used percentage'] = f"{used_percent * 100:.{precision}f}%" \
        if precision >= 0 else f"{used_percent * 100}%"
    track_data['Available percentage'] = f"{available_percent * 100:.{precision}f}%" \
        if precision >= 0 else f"{available_percent * 100}%"
    track_data['Average speed of day in month'] = f"{traffic_to_gb(month_speed_of_day).rstrip()}/day"
    track_data['Average speed of day in 7days'] = f"{traffic_to_gb(week_speed_of_day).rstrip()}/day"
    track_data['Traffic will be used by the end of the month predicted by the current month data'] = \
        traffic_to_gb(month_traffic_predicted)
    track_data['Traffic will be used by the end of the month predicted by the current week data'] = \
        traffic_to_gb(month_traffic_predicted_by_week)
    track_data['Traffic will be used by the end of the week predicted by the current month data'] = \
        traffic_to_gb(week_traffic_predicted_by_month)
    track_data['Traffic will be used by the end of the week predicted by the current week data'] = \
        traffic_to_gb(week_traffic_predicted)

    return track_data


class MainShell(cmd.Cmd):
    prompt = '(vault mgr) >> '
    intend = " " * 2

    def __init__(self):
        super().__init__()
        if not os.path.exists(vault_path):
            with open(vault_path, 'w') as f:
                json.dump({
                    'groups': []
                }, f, indent=2)
            print(f"vault.json not found, created and init at {vault_path}")
        self.vault = read_vault()

    def check_if_vault_save(self):
        """return True if saved"""
        return json.dumps(self.vault) == json.dumps(read_vault())

    def do_exit(self, _):
        """exit the vault manager"""
        if not self.check_if_vault_save():
            _r = console_input("Not saved, sure to exit? (Y/n/save)")
            if _r.lower() == "y":
                return True
            elif _r.lower() == "n":
                return False
            elif _r.lower() == "save":
                self.do_save(None)
                return True
        return True

    def emptyline(self):
        self.do_help("")

    def do_save(self, _):
        """save changes"""
        console0.print(json.dumps(self.vault, indent=2))
        _r = console_input("save? (Y/n)")
        if _r.lower() == "n":
            return
        print("saving...", end="")
        update_vault(self.vault)
        print("\rsaved successfully")

    @staticmethod
    def do_prec(_prec):
        """set the precision"""
        global precision
        if not len(_prec):
            console0.print(f"precision = {precision}")
            print("Usage: prec [precision]")
            return
        try:
            _prec = int(_prec)
        except ValueError:
            console0.print(f"precision = {precision}")
            print("precision must be an integer")
            return
        precision = _prec
        console0.print(f"precision = {precision}")

    @staticmethod
    def do_gmt(_gmt_tz):
        """set the GMT timezone"""
        global gmt_tz
        if _gmt_tz:
            if _gmt_tz.lower() in ["china", "ch", "cn", "zh"]:
                gmt_tz = 8
            else:
                try:
                    _gmt_tz = int(_gmt_tz)
                except ValueError:
                    console0.print("GMT timezone must be an integer")
                    return
                if _gmt_tz < -12 or _gmt_tz > 12:
                    console0.print("GMT timezone must be between -12 and 12")
                    return
                gmt_tz = _gmt_tz
            console0.print(f"GMT timezone = {gmt_tz}")
        else:
            console0.print(f"GMT timezone = {gmt_tz}")
            print("Usage: gmt [GMT timezone]")

    def do_list(self, _):
        """list all groups"""
        groups_table = table.Table(box=None)
        groups_table.add_column("Group Name", no_wrap=True)
        for group in self.vault.get('groups'):
            groups_table.add_row(group.get('name'))
        console0.print(groups_table)

    def do_info(self, arg):
        """show info of a group or all groups"""
        if len(arg):
            target_name = arg.lower()
            group = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}.get(target_name)
            if group is None:
                if not len(target_name):
                    print('Usage: info [group name]')
                else:
                    console0.print(f'Group {target_name} not found', no_wrap=True)
            console0.print("Group Name:", group.get('name'), no_wrap=True)
            for key in group:
                if key == 'name':
                    continue
                console0.print(self.intend + f"{key}: {json.dumps(group.get(key), indent=self.intend)}",
                               no_wrap=True)
        else:
            for group in self.vault.get('groups'):
                console0.print("Group Name:", group.get('name'), no_wrap=True)
                for key in group:
                    if key == 'name':
                        continue
                    console0.print(self.intend + f"{key}: {json.dumps(group.get(key), indent=self.intend)}",
                                   no_wrap=True)
                console0.print("---")

    def do_search(self, search_str):
        """
        search groups
        usage: search [group name]
        """
        search_str = search_str.lower()
        groups = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}
        if not search_str:
            self.do_list(None)
        else:
            group = groups.get(search_str)
            if group is None:
                similar_groups_table = table.Table(box=None)
                similar_groups_table.add_column("Group Name", no_wrap=True)
                for group_name in find_and_sort_substrings(search_str, list(groups.keys())):
                    similar_groups_table.add_row(group_name)
                console0.print(similar_groups_table)
            else:
                self.do_info(search_str)

    def do_config(self, group_name):
        """
        set config of a group
        usage: config [group name]
        """
        group_name = group_name.lower()
        groups = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}
        group = groups.get(group_name)
        group_name = group.get("name")
        if group is None:

            if not len(group_name):
                print('Usage: config [group name]')
            else:
                console0.print(f'Group {group_name} not found', no_wrap=True)
            return
        EditGroupShell(group_name, group).cmdloop()

    def do_cfg(self, arg):
        """shortcut for config"""
        self.do_config(arg)

    def do_new(self, _):
        """add a new group"""
        group_name = console_input("Name = ")
        if not len(group_name):
            console0.print("Name cannot be empty", no_wrap=True)
            return
        groups = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}
        if groups.get(group_name.lower()) is not None:
            console0.print(f'Group {group_name} already exists', no_wrap=True)
            return

        urls = list()
        i = 1
        while True:
            subscribe_name = f"subscribe{i}"
            url = console_input(f"{subscribe_name}: url = ")
            if not len(url):
                break
            url_data = {'url': url, 'name': subscribe_name, 'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            urls.append(url_data)
            i += 1
        for url in urls:
            console0.print(json.dumps(url, indent=self.intend), no_wrap=True)

        # attrs
        save_headers = True
        console0.print("save-headers =", save_headers)
        _r = console_input("save-headers? " + "(Y/n)" if save_headers else "(y/N)")
        if _r.lower() == "y":
            save_headers = True
        elif _r.lower() == "n":
            save_headers = False
        console0.print("save-headers =", save_headers)

        save_body = False
        console0.print("save-body =", save_body)
        _r = console_input("save-body? " + "(Y/n)" if save_headers else "(y/N)")
        if _r.lower() == "y":
            save_body = True
        elif _r.lower() == "n":
            save_body = False
        console0.print("save-body =", save_body)

        new_group = {
            'name': group_name,
            'urls-with-token': urls,
            'save-headers': save_headers,
            'save-body': save_body
        }
        console0.print(json.dumps(new_group, indent=self.intend), no_wrap=True)

        _r = console_input("save? (Y/n)")
        if _r.lower() != "n":
            self.vault['groups'].append(new_group)
            self.do_list(None)

    def do_del(self, group_name):
        """delete group"""
        group_name = group_name.lower()
        groups = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}
        group = groups.get(group_name)
        group_name = group.get("name")
        if group is None:

            if not len(group_name):
                print('Usage: del [group name]')
            else:
                console0.print(f'Group {group_name} not found', no_wrap=True)
            return
        self.vault['groups'].remove(group)
        self.do_list(None)

    def do_merge(self, group_name):
        """merge multiple datafiles of one group"""
        if not len(group_name):
            group_name = console_input("Name = ")
        group_name = group_name.lower()
        groups = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}
        group = groups.get(group_name)
        group_name = group.get("name")
        if group is None:

            if not len(group_name):
                print('Usage: merge | merge [group name]')
            else:
                console0.print(f'Group {group_name} not found', no_wrap=True)
            return

        datafiles = list()
        while True:
            datafile = console_input("datafile path = ")
            if not len(datafile):
                if datafiles:
                    break
                else:
                    console0.print("No datafiles input", no_wrap=True)
                    return
            if not os.path.exists(datafile):
                console0.print(f"File \"{datafile}\" not found", no_wrap=True)
                continue
            if datafile in datafiles:
                console0.print(f"Duplicate datafile \"{datafile}\"", no_wrap=True)
                continue
            datafiles.append(datafile)
        console0.print("datafiles:", no_wrap=True)
        console0.print(datafiles, no_wrap=True)
        _r = console_input("merge? (Y/n)")
        if _r.lower() == "n":
            return

        original_len = len(parse_data(group_name + ".json"))

        # merge
        datafiles.insert(0, os.path.join(data_folder_path, group_name + ".json"))
        points = list()
        recorded_date = set()
        for datafile in datafiles:
            data = parse_json(datafile)
            successful_points = 0
            for point in data:
                try:
                    point_date: float = datetime.strptime(point.get('date'), "%Y-%m-%d %H:%M:%S").timestamp()
                except Exception as e:
                    console0.print(f"Error parsing date {point['date']}: {e}", no_wrap=True)
                    continue
                else:
                    successful_points += 1
                if point_date in recorded_date:
                    continue
                recorded_date.add(point_date)
                points.append(point)
            console0.print(f"Merged datafile {datafile} into {group_name}.json: "
                           f"{successful_points} points added", no_wrap=True)
        points.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S").timestamp())

        console0.print(points, no_wrap=True)
        console0.print(f"{len(points) - original_len} points add", no_wrap=True)
        _r = console_input("save? (Y/n)")
        if _r.lower() == "n":
            return
        save_data(group_name + ".json", points)
        console0.print(f"Saved {group_name}.json successfully", no_wrap=True)

    def do_data(self, group_name):
        """show group data using table of rich"""
        group_name = group_name.lower()
        groups = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}
        group = groups.get(group_name)
        group_name = group.get("name")
        if group is None:

            if not len(group_name):
                print('Usage: data [group name]')
            else:
                console0.print(f'Group {group_name} not found', no_wrap=True)
            return
        try:
            with open(os.path.join(data_folder_path, f"{group_name}.json"), 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            console0.print(f"Data of group {group_name} not found, check if the group are collected", no_wrap=True)
            return

        # data_table = table.Table(box=None)
        data_table = table.Table(caption_justify="right", show_footer=True, width=console0.width)
        data_table.add_column("Date", "Date", style="magenta", no_wrap=True)
        data_table.add_column("Download", "Download", justify="right", style="cyan", no_wrap=True)
        data_table.add_column("Upload", "Upload", justify="right", style="green", no_wrap=True)
        # total traffic
        data_table.add_column("Total", "Total", justify="right", style="blue", no_wrap=True)
        data_table.add_column("Additional", "Additional", justify="right", style="yellow", no_wrap=True)
        # speed (total traffic in GB/total hours)
        data_table.add_column("Speed GB/h", "Speed GB/h", justify="right", style="cyan", no_wrap=True)
        # speed (total traffic in MB/total seconds)
        data_table.add_column("Speed MB/s", "Speed MB/s", justify="right", style="green", no_wrap=True)
        # percentage (total traffic/total)
        data_table.add_column("Percentage", "Percentage", justify="right", style="red", no_wrap=True)

        average_total = sum(point.get('upload') + point.get('download') for point in data) / len(data)
        average_additional = ((data[0].get('upload') - data[-1].get('upload')
                               + data[0].get('download') - data[-1].get('download')) / len(data)) if len(
            data) > 1 else 0

        last_traffic = None
        last_date_ts = None
        for point in data:
            total_traffic = point.get('download') + point.get('upload')
            additional_traffic = (total_traffic - last_traffic) if last_traffic is not None else None
            date_ts = datetime.strptime(point.get('date'), "%Y-%m-%d %H:%M:%S").timestamp()
            additional_time_ts = (date_ts - last_date_ts) if last_date_ts is not None else None
            data_table.add_row(
                datetime.fromtimestamp(date_ts).strftime(f"%Y-%m-%d %H:%M:%S") if gmt_tz == 0 else
                (datetime.fromtimestamp(date_ts) + timedelta(hours=gmt_tz))
                .strftime(f"%Y-%m-%d %H:%M:%S GMT+{gmt_tz:0>2d}00") if gmt_tz > 0 else
                (datetime.fromtimestamp(date_ts) - timedelta(hours=-gmt_tz))
                .strftime(f"%Y-%m-%d %H:%M:%S GMT-{gmt_tz:0>2d}00"),
                traffic_to_gb(point.get('download')) if average_total > 1024 ** 3
                else traffic_to_mb(point.get('download')),
                traffic_to_gb(point.get('upload')) if average_total > 1024 ** 3 else traffic_to_mb(point.get('upload')),
                traffic_to_gb(total_traffic) if average_total > 1024 ** 3 else traffic_to_mb(total_traffic),
                (traffic_to_gb(additional_traffic) if average_additional > 1024 ** 3
                 else traffic_to_mb(additional_traffic)) if additional_traffic is not None else "N/A",
                (f"{additional_traffic / additional_time_ts * 3600 / (1024 ** 3) :.{precision}f} GB/h"
                 if precision >= 0 else f"{additional_traffic / additional_time_ts * 3600 / (1024 ** 3)} GB/h")
                if additional_traffic is not None else "N/A",
                (f"{additional_traffic / additional_time_ts / (1024 ** 2) :.{precision}f} MB/s"
                 if precision >= 0 else f"{additional_traffic / additional_time_ts / (1024 ** 2)} MB/s")
                if additional_traffic is not None else "N/A",
                f"{total_traffic / point.get('total') :.{precision}%}"
                if precision >= 0 else f"{total_traffic / point.get('total') * 100}%",
            )
            last_traffic = total_traffic
            last_date_ts = date_ts
        console0.print(data_table)

    def do_addl(self, group_name):
        """show additional traffic by group name and date"""
        group_name = group_name.lower()
        groups = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}
        group = groups.get(group_name)
        group_name = group.get("name")
        if group is None:
            if not len(group_name):
                print('Usage: addl [group name]')
            else:
                console0.print(f'Group {group_name} not found', no_wrap=True)
            return
        try:
            with open(os.path.join(data_folder_path, f"{group_name}.json"), 'r') as f:
                _raw_data = json.load(f)
        except FileNotFoundError:
            console0.print(f"Data of group {group_name} not found, check if the group are collected", no_wrap=True)
            return
        if len(_raw_data) <= 0:
            console0.print(f"No sufficient data of group {group_name} for statistics, check if the group are collected",
                           no_wrap=True)
            return

        start_date = console_input("Start time (YYYY-MM-DD HH:MM:SS): ")
        if len(start_date):
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        else:
            start_date = datetime.strptime(_raw_data[-1].get('date'), "%Y-%m-%d %H:%M:%S").replace(
                day=1, hour=0, minute=0, second=0, microsecond=0)

        end_date = console_input("End time (YYYY-MM-DD HH:MM:SS): ")
        if len(end_date):
            end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
        else:
            end_date = datetime.strptime(_raw_data[-1].get('date'), "%Y-%m-%d %H:%M:%S") + timedelta(microseconds=1)

        data = [point for point in _raw_data if
                start_date <= datetime.strptime(point.get('date'), "%Y-%m-%d %H:%M:%S") <= end_date]
        if len(data) <= 0:
            console0.print(f"No sufficient data of group {group_name} for statistics, check if the group are collected",
                           no_wrap=True)
            return

        additional_upload = data[-1].get('upload') - data[0].get('upload')
        additional_download = data[-1].get('download') - data[0].get('download')
        additional_total = additional_upload + additional_download
        additional_days = (datetime.strptime(data[-1].get('date'), "%Y-%m-%d %H:%M:%S")
                           - datetime.strptime(data[0].get('date'), "%Y-%m-%d %H:%M:%S")).days
        speed_upload = additional_upload / additional_days
        speed_download = additional_download / additional_days
        speed_total = additional_total / additional_days

        console0.print(markdown.Markdown(f"# Group {group.get('name')} additional traffic "
                                         f"from {data[0].get('date')} to {data[-1].get('date')}"))
        if additional_total > 1024 ** 3:
            console0.print(f"[magenta]Additional upload[/]   = [cyan]{traffic_to_gb(additional_upload)}[/]")
            console0.print(f"[magenta]Additional download[/] = [cyan]{traffic_to_gb(additional_download)}[/]")
            console0.print(f"[magenta]Additional total[/]    = [cyan]{traffic_to_gb(additional_total)}[/]")
        else:
            console0.print(f"[magenta]Additional upload[/]   = [cyan]{traffic_to_mb(additional_upload)}[/]")
            console0.print(f"[magenta]Additional download[/] = [cyan]{traffic_to_mb(additional_download)}[/]")
            console0.print(f"[magenta]Additional total[/]    = [cyan]{traffic_to_mb(additional_total)}[/]")
        if speed_total > 1024 ** 3:
            console0.print(f"[magenta]Upload speed[/]   = [cyan]{traffic_to_gb(speed_upload).strip()}/day[/]")
            console0.print(f"[magenta]Download speed[/] = [cyan]{traffic_to_gb(speed_download).strip()}/day[/]")
            console0.print(f"[magenta]Total speed[/]    = [cyan]{traffic_to_gb(speed_total).strip()}/day[/]")
        else:
            console0.print(f"[magenta]Upload speed[/]   = [cyan]{traffic_to_mb(speed_upload).strip()}/day[/]")
            console0.print(f"[magenta]Download speed[/] = [cyan]{traffic_to_mb(speed_download).strip()}/day[/]")
            console0.print(f"[magenta]Total speed[/]    = [cyan]{traffic_to_mb(speed_total).strip()}/day[/]")

        start_of_month = datetime.strptime(data[-1].get('date'), "%Y-%m-%d %H:%M:%S").replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        days_of_month = (start_of_month.replace(month=start_of_month.month + 1) - start_of_month).days
        console0.print(
            f"[magenta]Predicted by the speed "
            f"to the period([cyan]{data[0].get('date')}[/] ~ [cyan]{data[-1].get('date')}[/]), "
            f"by the end of the month([cyan]{start_of_month.strftime('%Y-%m')}[/]), "
            f"the traffic used in total will be[/]\n [cyan]{traffic_to_gb(speed_total * days_of_month).strip()}[/]",
            no_wrap=False)

    def do_track(self, group_name):
        """show group statistics of the current month, week, and day"""
        group_name = group_name.lower()
        groups = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}
        group = groups.get(group_name)
        group_name = group.get("name")
        if group is None:
            if not len(group_name):
                print('Usage: track [group name]')
            else:
                console0.print(f'Group {group_name} not found', no_wrap=True)
            return

        try:
            track_data = track_group(group.get('name') if group.get('name') else group_name)
        except FileNotFoundError as e:
            console0.print(f"Data of group {group_name} not found, check if the group are collected: {e}",
                           no_wrap=True)
            return
        except json.JSONDecodeError as e:
            console0.print(f"Data of group {group_name} is invalid, check if the group are collected: {e}",
                           no_wrap=True)
            return
        except KeyError as e:
            console0.print(f"Data of group {group_name} is invalid, check if the group are collected: {e}",
                           no_wrap=True)
            return
        except ValueError as e:
            console0.print(f"Data of group {group_name} is invalid, check if the group are collected: {e}",
                           no_wrap=True)
            return
        max_key_len = max(len(k) for k in track_data.keys() if len(k) <= 30)
        # console0.print(markdown.Markdown(f"# Group {group.get('name')} track info"))
        track_output: str = ""
        for k, v in track_data.items():
            track_output += (f"[magenta]{k.ljust(max_key_len)}[/] = [cyan]{v}[/]"
                             if len(k) <= 30 else f"[magenta]{k}[/] =\n [cyan]{v}[/]")
            track_output += "\n"

        console0.print(panel.Panel.fit(track_output, title=f"# Group {group.get('name')} track info"), no_wrap=True)


class EditGroupShell(cmd.Cmd):
    intend = MainShell.intend

    def __init__(self, group_name: str, group: dict):
        super().__init__()
        self.group_name = group_name
        self.group = group
        self.prompt = f'({self.group_name}) >> '

    def emptyline(self):
        return self.do_save(None)

    def do_save(self, _):
        """save changes"""
        self.do_list(None)
        return True

    def do_list(self, _):
        """list all configs"""
        list_output = ""
        for key in self.group:
            list_output += f"{key}: {json.dumps(self.group.get(key), indent=self.intend)}"
            list_output += "\n"

        console0.print(panel.Panel(list_output), no_wrap=True)

    def do_name(self, new_name):
        """set group name"""
        if len(new_name):
            self.group['name'] = new_name
        else:
            console0.print(f"name = {self.group['name']}", no_wrap=True)
            _r = console_input("name = ")
            if len(_r):
                self.group['name'] = _r
        console0.print(f"name = {self.group['name']}", no_wrap=True)

    def do_attr(self, _):
        """set group attributes"""
        for key, value in self.group.items():
            if key in ['name', 'urls-with-token']:
                continue
            print(f"{key} = {value}")
            _r = console_input(f"{key} = ")
            if len(_r):
                if _r.lower() == "false":
                    _r = False
                elif _r.lower() == "true":
                    _r = True
                elif _r.lower() == "none":
                    _r = None
                self.group[key] = _r
            print(f"{key} = {self.group[key]}")
            console0.print("---")

    def add_url(self, url):
        """
        Add a URL to the group's 'urls-with-token' list with a unique name, and print the URL data in JSON format.
        
        Parameters:
            url (str): The URL to be added.
            
        Returns:
            None
        """
        i = 1
        name = f"subscribe{i}"
        while name in self.group.get('urls-with-token'):
            i += 1
            name = f"subscribe{i}"
        url_data = {'url': url, 'name': name, 'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self.group['urls-with-token'].append(url_data)
        console0.print(json.dumps(url_data, indent=self.intend), no_wrap=True)

    def reset_url(self):
        """
        Reset the URL and clear the 'urls-with-token' group. 
        Prompt the user to input a URL with a name, and append the URL data to the 'urls-with-token' group. 
        """
        self.group['urls-with-token'].clear()
        i = 1
        while True:
            name = f"subscribe{i}"
            url = console_input(f"{name}: url = ")
            if not len(url):
                return
            url_data = {'url': url, 'name': name, 'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            self.group['urls-with-token'].append(url_data)
            console0.print(json.dumps(url_data, indent=self.intend), no_wrap=True)
            i += 1

    def do_urls(self, args: str):
        """
        set urls
        usage: urls [add [url]|del [url|url code]|reset]
        urls: list urls
        urls add [url]: add url
            example: urls add https://www.example.com/api/client/subscribe?token=HelloWorld
        urls del [url|url code]: delete url
            example1: urls del subscribe1
            example2: urls del 1
        urls reset: reset urls
        """
        if args.split(" ")[0] == "add":
            if len(args.split(" ")) == 2:
                if not re.match(
                        r"(((ht|f)tps?)://)?"
                        r"([^!@#$%^&*?.\s-]([^!@#$%^&*?.\s]{0,63}[^!@#$%^&*?.\s])?\.)+[a-z]{2,6}/?/",
                        args.split(" ")[1]):
                    _r = console_input("invalid url, sure to add? (n/y)")
                    if _r.lower() != "y":
                        return
                self.add_url(args.split(" ")[1])
            else:
                print("usage: urls add [url]")
        elif args.split(" ")[0] == "del":
            if len(args.split(" ")) == 2:
                name = args.split(" ")[1]
                if not len(name):
                    print("usage: urls del [url]")
                elif name in self.group.get('urls-with-token'):
                    self.group['urls-with-token'].remove(name)
                else:
                    console0.print(f"{name} not found", no_wrap=True)
            else:
                print("usage: urls del [url]")
        elif args.split(" ")[0] == "reset":
            self.reset_url()
        for url in self.group.get('urls-with-token'):
            console0.print(f"{url.get('name')}: {url.get('url')}", no_wrap=True)

    def do_url(self, arg):
        """shortcut for urls"""
        self.do_urls(arg)

    def do_raw(self, _):
        """show raw data"""
        try:
            console0.print(parse_data(f"{self.group.get('name')}.json"), no_wrap=True)
        except FileNotFoundError:
            console0.print(f"{self.group.get('name')}.json not found.Please check if it is collected", no_wrap=True)
        except json.decoder.JSONDecodeError:
            console0.print(f"The data in {self.group.get('name')}.json is invalid", no_wrap=True)

    def do_rmd(self, _):
        """remove duplication points in raw data"""
        data = parse_data(f"{self.group.get('name')}.json")
        recorded_date = set()
        new_data = []
        for point in data:
            if point.get('date') not in recorded_date:
                new_data.append(point)
                recorded_date.add(point.get('date'))
                console0.print("Removed point:", point, no_wrap=True)

        console0.print(json.dumps(new_data, indent=self.intend), no_wrap=True)
        console0.print(f"{len(data)} data points -> {len(new_data)} data points, "
                       f"removed {len(data) - len(new_data)} duplicates", no_wrap=True)
        _r = console_input("Sure to save? (Y/n)")
        if _r.lower() == "n":
            return
        save_data(f"{self.group.get('name')}.json", new_data)
        console0.print(f"Saved {self.group.get('name')}.json successfully", no_wrap=True)


if __name__ == '__main__':
    main_shell = MainShell()
    main_shell.cmdloop()
