import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

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
      "Content-Disposition": "attachment;filename=TAG",
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
        return [data_point.upload + data_point.download for data_point in self]

    def get_attr_total(self):
        return [data_point.total for data_point in self]

    def get_date(self):
        return [data_point.date for data_point in self]

    def get_date_in_ts(self):
        return [data_point.date_in_ts for data_point in self]

    def get_data_by_url(self, url: str) -> list[TrafficDataPoint]:
        return TrafficDataList(point for point in self if point.url == url)

    def get_data_by_date_range(self, start_date: datetime = None, end_date: datetime = None):
        if start_date is None:
            start_date = self[0].date
        if end_date is None:
            end_date = self[-1].date
        return TrafficDataList([point for point in self if start_date <= point.date <= end_date])

    def get_data_with_gran(self, start_date: datetime = None, end_date: datetime = None,
                           granularity_sec: (int, None) = None) -> ("_GranDataList", None):
        if start_date is None:
            start_date = self[0].date
        if end_date is None:
            end_date = self[-1].date
        selected_data = self.get_data_by_date_range(start_date, end_date)
        result_data = []

        if not selected_data:
            return None

        if granularity_sec is None:
            return _GranDataList(TrafficDataList([point]) for point in selected_data)
        current_timestamp = start_date.timestamp()
        end_timestamp = end_date.timestamp()
        while current_timestamp <= end_timestamp:
            data_points_in_range = TrafficDataList([point for point in selected_data if
                                                    current_timestamp <= point.date_in_ts
                                                    < current_timestamp + granularity_sec])
            if not data_points_in_range:
                warnings.warn(f"Data not found for timestamp "
                              f"{datetime.fromtimestamp(current_timestamp)} ~ "
                              f"{datetime.fromtimestamp(current_timestamp + granularity_sec)}")
                continue
            result_data.append(data_points_in_range)
            current_timestamp += granularity_sec

        return _GranDataList(result_data, granularity_sec)


class _GranDataList(list):
    def __init__(self, items: Iterable[TrafficDataList[TrafficDataPoint]], granularity_sec: int = None):
        super().__init__()
        self.extend(items)
        if granularity_sec is None:
            granularity_sec = 1
        self.granularity_sec = granularity_sec

    def get_upload(self):
        return [sum(data_list.get_upload()) for data_list in self]

    def get_download(self):
        return [sum(data_list.get_download()) for data_list in self]

    def get_date(self):
        return [data_list[0].date for data_list in self]

    def get_date_in_ts(self):
        return [data_list[0].date_in_ts for data_list in self]

    def get_total_traffic(self):
        return [sum(data_list.get_total_traffic()) for data_list in self]

    def get_rate_sec(self):
        return [sum(data_list.get_total_traffic()) / self.granularity_sec for data_list in self]


def _test():
    from rich import print
    from main import parse_data

    data = parse_data("TAG.json")
    print(data)

    data_list = TrafficDataList.from_list(data)
    print(data_list)

    print(data_list.get_total_traffic())

    gran: _GranDataList = data_list.get_data_with_gran(granularity_sec=600)
    print(gran.get_total_traffic())
    print(gran.get_rate_sec())


if __name__ == '__main__':
    _test()
