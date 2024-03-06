import cmd
import json
import os
import re
from datetime import datetime

from rich import console
from rich import table

os.chdir(os.path.dirname(__file__))
vault_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'vault.json'))
data_folder_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'))

precision = 5

console0 = console.Console()


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
        # percentage (total traffic/total)
        data_table.add_column("Percentage", no_wrap=True)
        for point in data:
            data_table.add_row(
                point.get('date'),
                traffic_to_gb(point.get('download')),
                traffic_to_gb(point.get('upload')),
                traffic_to_gb(point.get('download') + point.get('upload')),
                f"{(point.get('download') + point.get('upload')) / point.get('total') * 100 :.{precision}f} %"
                if precision >= 0 else f"{(point.get('download') + point.get('upload')) / point.get('total') * 100} %",
            )
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
