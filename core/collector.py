import json
import os.path
from email.utils import parsedate_to_datetime

import requests

os.chdir(os.path.dirname(__file__))

default_settings_path = os.path.abspath(os.path.join("..", "config", "default_settings.json"))
with open(default_settings_path, 'r') as f:
    default_settings = json.load(f)
proxies = default_settings['proxies']
headers = default_settings['headers']

print_out_response_headers = default_settings.get('print-out-response-headers', True)
print_out_response_body = default_settings.get('print-out-response-body', True)

vault_path = os.path.abspath(os.path.join("..", "config", "vault.json"))
with open(vault_path, 'r') as f:
    vault: dict = json.load(f)


def reload_settings():
    os.chdir(os.path.dirname(__file__))

    with open(default_settings_path, 'r') as _f:
        global default_settings
        default_settings = json.load(_f)
    global proxies
    proxies = default_settings['proxies']
    global headers
    headers = default_settings['headers']
    global print_out_response_headers
    print_out_response_headers = default_settings.get('print-out-response-headers', True)
    global print_out_response_body
    print_out_response_body = default_settings.get('print-out-response-body', True)

    global vault
    with open(vault_path, 'r') as _f:
        vault = json.load(_f)


def collect(progress_wrapper=lambda _obj: _obj):
    groups_data = dict()
    for group in progress_wrapper(vault.get('groups')):
        save_headers = group.get('save-headers')
        save_body = group.get('save-body')
        for url in group.get('urls-with-token'):
            try:
                response = subscribe_get(url['url'])
            except Exception as e:
                print(e)
            else:
                break
        else:
            raise requests.exceptions.RequestException("All urls failed")
        traffic_data = dict()
        traffic_data['url'] = response.url
        traffic_data['date'] = parsedate_to_datetime(response.headers.get('Date')).strftime("%Y-%m-%d %H:%M:%S")
        subs_info = parse_subscription_userinfo(response.headers)
        traffic_data.update(subs_info)
        if save_headers:
            traffic_data['headers'] = dict(response.headers)
        if save_body:
            traffic_data['body'] = response.text
        # print(traffic_data)
        groups_data[group.get('name')] = traffic_data
    return groups_data


def subscribe_get(url):
    response = requests.get(url, headers=headers, proxies=proxies)

    # if request failed
    if response.status_code != 200:
        raise requests.exceptions.RequestException(f"Request failed with status code {response.status_code}")

    if print_out_response_headers:
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
    if print_out_response_body:
        print("\nResponse Body:")
        print(response.text)

    return response


def parse_subscription_userinfo(response_headers):
    userinfo_str: str = response_headers.get("Subscription-Userinfo")
    try:
        userinfo = {k: int(v) for session in userinfo_str.split(";") for k, v in [session.strip().split("=")]}
    except Exception as e:
        print(e)

        print("retry")
        userinfo = dict()
        try:
            for session in userinfo_str.split(";"):
                try:
                    k, v = session.strip().split("=")
                except Exception as e:
                    print(e)
                    continue
                try:
                    userinfo[k] = int(v)
                except Exception as e:
                    print(e)
        except Exception as e:
            print(e)
    return userinfo


def _test():
    _r = collect()
    print(json.dumps(_r, indent=2))
    print(_r)


if __name__ == '__main__':
    _test()
