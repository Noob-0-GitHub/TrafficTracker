import json
import os
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

data_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


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


# This is a data point sample
"""
  {
    "url": "https://www.example.com",
    "date": "2024-03-03 05:01:26",
    "upload": 196056440,
    "download": 33267046870,
    "total": 268435456000,
    "expire": 1719808630,
    "headers": {
      "Content-Disposition": "attachment;filename=test",
      "Content-Type": "text/html; charset=UTF-8",
      "Date": "Sun, 03 Mar 2024 05:01:26 GMT",
      "Profile-Update-Interval": "24",
      "Server": "Caddy",
      "Subscription-Userinfo": "upload=196056440; download=33267046870; total=268435456000; expire=1719808630",
      "X-Powered-By": "PHP/7.4.28",
      "Transfer-Encoding": "chunked"
    }
"""


@dataclass
class TrafficDataPoint:
    def __init__(self, data_point: dict = None):
        if data_point is None:
            data_point = dict()
        self.url = data_point.get("url")
        self.date_in_str = data_point.get("date")
        self.upload = data_point.get("upload")
        self.download = data_point.get("download")
        self.total_traffic = self.download + self.upload
        self.total = data_point.get("total")
        self.expire_in_ts = data_point.get("expire")

        if self.date_in_str is None:
            self.date = None
            self.date_in_ts = None
        else:
            self.date = datetime.strptime(self.date_in_str, "%Y-%m-%d %H:%M:%S")
            self.date_in_ts = self.date.timestamp()

        if self.expire_in_ts is None:
            self.expire = None
        else:
            self.expire = datetime.fromtimestamp(self.expire_in_ts)

    def __repr__(self):
        return f"TrafficDataPoint({self.date_in_str}, {self.upload}, {self.download}, {self.total})"


class TrafficDataList(list):
    def __init__(self, data_list: (Iterable, TrafficDataPoint) = None, *args):
        if isinstance(data_list, TrafficDataPoint):
            data_list = [data_list]
            data_list.extend(args)
        super().__init__()
        if data_list:
            self.extend(data_list)

    @classmethod
    def from_list(cls, data_list: list):
        return cls(TrafficDataPoint(data_point_dict) for data_point_dict in data_list)

    def get_upload(self):
        return [data_point.upload for data_point in self]

    def get_download(self):
        return [data_point.download for data_point in self]

    def get_total_traffic(self):
        return [data_point.total_traffic for data_point in self]

    def get_additional_upload(self):
        pre_total = None
        result = []
        for data_point in self:
            point_total = data_point.get("upload")
            if pre_total is None:
                result.append(0)
            else:
                result.append(point_total - pre_total)
            pre_total = point_total
        return result

    def get_additional_download(self):
        pre_total = None
        result = []
        for data_point in self:
            point_total = data_point.get("download")
            if pre_total is None:
                result.append(0)
            else:
                result.append(point_total - pre_total)
            pre_total = point_total
        return result

    def get_additional_total_traffic(self):
        pre_total = None
        result = []
        for data_point in self:
            point_total = data_point.total_traffic
            if pre_total is None:
                result.append(0)
            else:
                result.append(point_total - pre_total)
            pre_total = point_total
        return result

    def get_attr_total(self):
        return [data_point.total for data_point in self]

    def get_date(self):
        return [data_point.date for data_point in self]

    def get_date_in_str(self, date_format="%Y-%m-%d %H:%M:%S"):
        return [data_point.date.strftime(date_format) for data_point in self]

    def get_date_in_ts(self):
        return [data_point.date_in_ts for data_point in self]

    def get_data_by_url(self, url: str) -> list[TrafficDataPoint]:
        return TrafficDataList(point for point in self if point.url == url)

    def get_data_by_date_range(self, start_date: datetime = None, end_date: datetime = None):
        """return a list of TrafficDataPoint from start_date to before end_date"""
        if start_date is None:
            start_date = self[0].date
        if end_date is None:
            end_date = self[-1].date + timedelta(microseconds=1)
        return TrafficDataList([point for point in self if start_date <= point.date < end_date])

    def get_data_by_gran(self, start_date: datetime = None, end_date: datetime = None,
                         granularity_sec: (int, None) = None) -> ("GranDataList", None):
        if start_date is None:
            start_date = self[0].date
        if end_date is None:
            end_date = self[-1].date
        result_data = list()

        if granularity_sec is None:
            return GranDataList(self.get_data_by_date_range(start_date, end_date))

        current_timestamp = start_date.timestamp()
        end_timestamp = end_date.timestamp()
        pre_point = None
        for point in self:
            if current_timestamp <= point.date_in_ts:
                # while current_timestamp < point.date_in_ts:
                while current_timestamp < point.date_in_ts and current_timestamp < end_timestamp:
                    result_data.append(GranDataPoint(pre_point, point, current_timestamp)
                                       if pre_point is not None else point)
                    current_timestamp += granularity_sec
                if current_timestamp == point.date_in_ts:
                    result_data.append(point)
                    current_timestamp += granularity_sec
                pre_point = point
            else:
                pre_point = point
                continue
            # current_timestamp += granularity_sec
            if current_timestamp >= end_timestamp:
                break

        return GranDataList(result_data, granularity_sec=granularity_sec)

    def get_data_by_count(self, _count: int, start_date: datetime = None, end_date: datetime = None) -> "GranDataList":
        if _count <= 0:
            raise ValueError("count must > 0")
        if start_date is None:
            start_date = self[0].date
        if end_date is None:
            end_date = self[-1].date
        _granularity = (end_date - start_date).total_seconds() / _count
        return self.get_data_by_gran(start_date=start_date, end_date=end_date, granularity_sec=_granularity)

    def latest_month_data(self) -> "TrafficDataList":
        start_of_latest_month = self[-1].date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.get_data_by_date_range(start_date=start_of_latest_month, end_date=datetime.now())

    def latest_7days_data(self) -> "TrafficDataList":
        start_of_latest_month = self[-1].date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_latest_7days = (self[-1].date - timedelta(days=7)) if (
                (self[-1].date - start_of_latest_month).days > 7) else start_of_latest_month
        return self.get_data_by_date_range(start_date=start_of_latest_7days, end_date=datetime.now())

    def latest_24hours_data(self) -> "TrafficDataList":
        start_of_latest_month = self[-1].date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_latest_24hours = (self[-1].date - timedelta(hours=24)) if (
                (self[-1].date - start_of_latest_month).days > 1) else start_of_latest_month
        return self.get_data_by_date_range(start_date=start_of_latest_24hours, end_date=datetime.now())


@dataclass
class GranDataPoint:
    pre_point: TrafficDataPoint
    next_point: TrafficDataPoint
    date_in_ts: float

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(self.date_in_ts)

    def get_attr_weight_average(self, attr: str):
        if getattr(self.pre_point, attr, None) is None or getattr(self.next_point, attr, None) is None:
            raise ValueError(f"{attr} not found")
        try:
            # incomplete
            # return ((getattr(self.next_point, attr) * (self.next_point.date_in_ts - self.date_in_ts)
            #          - getattr(self.pre_point, attr) * (self.date_in_ts - self.pre_point.date_in_ts))
            #         / (self.next_point.date_in_ts - self.pre_point.date_in_ts))
            x1 = getattr(self.pre_point, attr)
            x2 = getattr(self.next_point, attr)
            w1 = self.next_point.date_in_ts - self.date_in_ts
            assert w1 > 0
            w2 = self.date_in_ts - self.pre_point.date_in_ts
            assert w2 > 0
            return (x1 * w1 + x2 * w2) / (w1 + w2)
        except Exception as e:
            raise ValueError(f"{attr} not supported: {e}")

    # must be same as TrafficDataPoint
    @property
    def upload(self):
        return self.get_attr_weight_average('upload')

    @property
    def download(self):
        return self.get_attr_weight_average('download')

    @property
    def total_traffic(self):
        return self.upload + self.download

    @property
    def total(self):
        return int(self.get_attr_weight_average('total'))


class GranDataList(list):
    def __init__(self, items: Iterable[GranDataPoint | TrafficDataPoint],
                 granularity_sec: int = None):
        super().__init__()
        if not all(isinstance(item, (GranDataPoint, TrafficDataPoint)) for item in items):
            raise ValueError("items must be TrafficDataPoint or GranDataPoint")
        self.extend(items)
        if granularity_sec is None:
            granularity_sec = 1
        self.granularity_sec = granularity_sec

    def get_pre_points(self):
        lst = []
        for item in self:
            if isinstance(item, GranDataPoint):
                lst.append(item.pre_point)
            elif isinstance(item, TrafficDataPoint):
                lst.append(item)
        return lst

    def get_next_points(self):
        lst = []
        for item in self:
            if isinstance(item, GranDataPoint):
                lst.append(item.next_point)
            elif isinstance(item, TrafficDataPoint):
                lst.append(item)
            else:
                continue

    def get_date(self):
        return [item.date for item in self]

    def get_date_in_str(self, date_format="%Y-%m-%d %H:%M:%S"):
        return [item.date.strftime(date_format) for item in self]

    def get_date_in_ts(self):
        return [item.date_in_ts for item in self]

    def get_upload(self):
        return [item.upload for item in self]

    def get_download(self):
        return [item.download for item in self]

    def get_total_traffic(self):
        return [item.total_traffic for item in self]

    def get_additional_upload(self):
        if len(self) < 1:
            return []
        pre_point_upload = self[0].upload
        result = []
        for point in self:
            point_upload = point.upload
            result.append(point_upload - pre_point_upload)
            pre_point_upload = point_upload
        return result

    def get_additional_download(self):
        if len(self) < 1:
            return []
        pre_point_download = self[0].download
        result = []
        for point in self:
            point_download = point.download
            result.append(point_download - pre_point_download)
            pre_point_download = point_download
        return result

    def get_additional_total_traffic(self):
        if len(self) < 1:
            return []
        pre_point_total = self[0].total_traffic
        result = []
        for point in self:
            point_total = point.total_traffic
            result.append(point_total - pre_point_total)
            pre_point_total = point_total
        return result

    def get_upload_rate_sec(self):
        if len(self) < 1:
            return []
        return [additional / self.granularity_sec for additional in self.get_additional_upload()]

    def get_download_rate_sec(self):
        if len(self) < 1:
            return []
        return [additional / self.granularity_sec for additional in self.get_additional_download()]

    def get_rate_sec(self):
        if len(self) < 1:
            return []
        return [additional / self.granularity_sec for additional in self.get_additional_total_traffic()]

    def get_data_by_gran(self, granularity_sec: int):
        return GranDataList(self, granularity_sec=granularity_sec)


def list_to_mb(data: list[float | int]):
    return [item / 1024 / 1024 for item in data]


def list_to_gb(data: list[float | int]):
    return [item / 1024 / 1024 / 1024 for item in data]


def _test():
    from rich import print
    from main import parse_data

    data = parse_data([json_file for json_file in os.listdir(data_folder_path) if json_file.endswith('.json')][0])
    print(data)

    print("Get all data into data list:")
    data_list = TrafficDataList.from_list(data)
    print(data_list)

    print(data_list.get_total_traffic())
    print(data_list.get_download())
    input("Press Enter to continue...")

    gran: GranDataList = data_list.get_data_by_gran(granularity_sec=600)
    print(gran.get_total_traffic())
    print(gran.get_download())
    print(gran.get_rate_sec())
    print(data_list.get_date())
    print([gran.get_date_in_ts()[i] - gran.get_date_in_ts()[i - 1]
           for i in range(1, len(gran))])
    print(gran.granularity_sec)
    input("Press Enter to continue...")

    print("Gran with count 10:")
    gran_with_count: GranDataList = data_list.get_data_by_count(_count=10)
    print(gran_with_count.get_total_traffic())
    print(gran_with_count.get_download())
    print(gran_with_count.get_rate_sec())
    print(gran_with_count.get_date())
    print([gran_with_count.get_date_in_ts()[i] - gran_with_count.get_date_in_ts()[i - 1]
           for i in range(1, len(gran_with_count))])
    print(gran_with_count.granularity_sec)


if __name__ == '__main__':
    _test()
