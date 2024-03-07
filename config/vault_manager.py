import cmd
import json
import os
import re
import warnings
from datetime import datetime
from datetime import timedelta

from rich import console
from rich import table

os.chdir(os.path.dirname(__file__))
vault_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'vault.json'))

data_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

precision = 5
gmt_tz = 0

console0 = console.Console()


def parse_json(file_path):
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
    file_path = os.path.join(data_folder_path, file_name)
    parsed = parse_json(file_path)
    return parsed if len(parsed) else []


def save_data(file_name, data):
    file_path = os.path.join(data_folder_path, file_name)
    save_json(file_path, data)


# def console_input(prompt: str, _console=console0, markup=True, emoji=True, password=False, stream=None):
def console_input(prompt: str):
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
    if _prec is None:
        _prec = precision
    if _prec >= 0:
        return f"{traffic / 1024 / 1024 / 1024:.{precision}f} GB"
    else:
        return f"{traffic / 1024 / 1024 / 1024} GB"


def traffic_to_mb(traffic, _prec=None) -> str:
    if _prec is None:
        _prec = precision
    if _prec >= 0:
        return f"{traffic / 1024 / 1024:.{precision}f} MB"
    else:
        return f"{traffic / 1024 / 1024} MB"


def read_vault(_path: str = None, retry_count=3) -> dict:
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
    if _path is None:
        _path = vault_path
    with open(_path, 'w') as f:
        json.dump(vault_data, f, indent=2)


class MainCmd(cmd.Cmd):
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
            _r = console_input("not saved, sure to exit? (Y/n/save)")
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
        if group is None:
            if not len(group_name):
                print('Usage: config [group name]')
            else:
                console0.print(f'Group {group_name} not found', no_wrap=True)
            return
        EditGroupCmd(group_name, group).cmdloop()

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
        if _r.lower() != "n":
            return

        # merge
        datafiles.insert(0, os.path.join(data_folder_path, group_name + ".json"))
        points = list()
        recorded_date = set()
        for datafile in datafiles:
            data = parse_json(datafile)
            for point in data:
                try:
                    point_date: float = datetime.strptime(groups.get(point['date']), "%Y-%m-%d %H:%M:%S").timestamp()
                except Exception as e:
                    console0.print(f"Error parsing date {point['date']}: {e}", no_wrap=True)
                    continue
                if point_date in recorded_date:
                    continue
                recorded_date.add(point_date)
                points.append(point)
        points.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d %H:%M:%S").timestamp())

        save_data(group_name + ".json", points)

    def do_data(self, group_name):
        """show group data using table of rich"""
        group_name = group_name.lower()
        groups = {_g.get('name').lower(): _g for _g in self.vault.get('groups')}
        group = groups.get(group_name)
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
        data_table = table.Table()
        data_table.add_column("Date", no_wrap=True)
        data_table.add_column("Download", no_wrap=True)
        data_table.add_column("Upload", no_wrap=True)
        # total traffic
        data_table.add_column("Total", no_wrap=True)
        data_table.add_column("Additional", no_wrap=True)
        # speed (total traffic in GB/total hours)
        data_table.add_column("Speed GB/h", no_wrap=True)
        # speed (total traffic in MB/total seconds)
        data_table.add_column("Speed MB/s", no_wrap=True)
        # percentage (total traffic/total)
        data_table.add_column("Percentage", no_wrap=True)

        average_total = sum(point.get('upload') + point.get('download') for point in data) / len(data)
        average_additional = ((data[0].get('upload') - data[-1].get('upload')
                              + data[0].get('download') - data[-1].get('download')) / len(data)) if len(data) > 1 else 0
        print(average_total, 1024 ** 3)

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
                (f"{additional_traffic / additional_time_ts * 3600 / 1024 / 1024 / 1024 :.{precision}f} GB/h"
                 if precision >= 0 else f"{additional_traffic / additional_time_ts * 3600 / 1024 / 1024 / 1024} GB/h")
                if additional_traffic is not None else "N/A",
                (f"{additional_traffic / additional_time_ts / 1024 / 1024 :.{precision}f} MB/s"
                 if precision >= 0 else f"{additional_traffic / additional_time_ts / 1024 / 1024} MB/s")
                if additional_traffic is not None else "N/A",
                f"{total_traffic / point.get('total') :.{precision}%}"
                if precision >= 0 else f"{total_traffic / point.get('total') * 100}%",
            )
            last_traffic = total_traffic
            last_date_ts = date_ts
        console0.print(data_table)


class EditGroupCmd(cmd.Cmd):
    intend = MainCmd.intend

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
        for key in self.group:
            console0.print(f"{key}: {json.dumps(self.group.get(key), indent=self.intend)}", no_wrap=True)

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
            print(f"{key} = {value}")
            console0.print("---")

    def add_url(self, url):
        i = 1
        name = f"subscribe{i}"
        while name in self.group.get('urls-with-token'):
            i += 1
            name = f"subscribe{i}"
        url_data = {'url': url, 'name': name, 'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self.group['urls-with-token'].append(url_data)
        console0.print(json.dumps(url_data, indent=self.intend), no_wrap=True)

    def reset_url(self):
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


if __name__ == '__main__':
    main_cmd = MainCmd()
    main_cmd.cmdloop()
