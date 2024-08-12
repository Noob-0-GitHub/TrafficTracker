import json
import os
import warnings
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

data_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
allow_negative_traffic = False


def parse_json(file_path: str):
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


def save_json(file_path: str, data, indent=None):
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


def parse_data(file_name: str) -> list[dict[str, object]]:
    file_path = os.path.join(data_folder_path, file_name)
    parsed = parse_json(file_path)
    return parsed if len(parsed) else []


def save_data(file_name: str, data: list[dict[str, object]]):
    file_path = os.path.join(data_folder_path, file_name)
    save_json(file_path, data)


def list_data_file_name(keep_extension: bool = True) -> list[str]:
    return [(file.name if keep_extension else os.path.splitext(file.name)[0])
            for file in os.scandir(data_folder_path)
            if file.is_file() and file.name.endswith('.json')]


def list_data_file() -> list[os.DirEntry]:
    return [file for file in os.scandir(data_folder_path)
            if file.is_file() and file.name.endswith('.json')]


def newest_data_file(with_extension: bool = False) -> str:
    files = list_data_file()
    files.sort(key=lambda x: x.stat().st_mtime)
    return files[-1].name if with_extension else os.path.splitext(files[-1].name)[0]


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


class BaseDataPoint(ABC):
    @property
    @abstractmethod
    def url(self):
        pass

    @property
    @abstractmethod
    def date(self):
        pass

    @property
    @abstractmethod
    def date_in_str(self):
        pass

    @property
    @abstractmethod
    def date_in_ts(self):
        pass

    @property
    @abstractmethod
    def upload(self):
        pass

    @property
    @abstractmethod
    def download(self):
        pass

    @property
    @abstractmethod
    def total_traffic(self):
        pass

    @property
    @abstractmethod
    def total(self):
        pass

    @property
    @abstractmethod
    def expire(self):
        pass

    @property
    @abstractmethod
    def expire_in_ts(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass


@dataclass
class TrafficDataPoint(BaseDataPoint):
    url: str = None
    date: datetime = None
    date_in_str: str = None
    date_in_ts: float = None
    upload: int = None
    download: int = None
    total_traffic: int = None
    total: int = None
    expire: datetime = None
    expire_in_ts: (int, float) = None

    def __init__(self, data_point: dict = None, gmt_offset=0):
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
            self.date_in_ts = data_point.get("date_in_ts")
            if self.date_in_ts is None:
                warnings.warn(f"Missing information: date of {data_point}")
                # noinspection PyTypeChecker
                self.date = None
            else:
                self.date = datetime.fromtimestamp(self.date_in_ts)
                self.date_in_str = self.date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            self.date = datetime.strptime(self.date_in_str, "%Y-%m-%d %H:%M:%S")
            self.date_in_ts = self.date.timestamp()

        if self.expire_in_ts is None:
            warnings.warn(f"Missing information: expire time of {data_point}")
            # noinspection PyTypeChecker
            self.expire = None
        else:
            self.expire = datetime.fromtimestamp(self.expire_in_ts)

        self.gmt_offset = 0
        if gmt_offset:
            self.set_gmt_offset(gmt_offset)

    def set_gmt_offset(self, gmt_offset):
        if self.date:
            self.date = self.date + timedelta(hours=gmt_offset - self.gmt_offset)
            self.date_in_str = self.date.strftime("%Y-%m-%d %H:%M:%S")
            self.date_in_ts = self.date.timestamp()
        if self.expire:
            self.expire = self.expire + timedelta(hours=gmt_offset - self.gmt_offset)
            self.expire_in_ts = self.expire.timestamp()

        self.gmt_offset = gmt_offset

    def __repr__(self):
        return f"TrafficDataPoint({self.date_in_str}, {self.upload}, {self.download}, {self.total})"


@dataclass
class GranDataPoint(BaseDataPoint):
    pre_point: TrafficDataPoint
    next_point: TrafficDataPoint
    date_in_ts: float = None

    @property
    def date(self) -> datetime:
        return datetime.fromtimestamp(self.date_in_ts)

    @property
    def date_in_str(self):
        return self.date.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def url(self) -> str:
        return self.next_point.url

    @property
    def expire(self):
        return self.next_point.expire

    @property
    def expire_in_ts(self):
        return self.next_point.expire_in_ts

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

    # must be the same as TrafficDataPoint
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

    def __repr__(self):
        return f"GranDataPoint({self.date_in_str}, {self.pre_point.__repr__()}, {self.next_point.__repr__()})"


class BaseDataList(list, ABC):
    @abstractmethod
    def get_upload(self):
        pass

    @abstractmethod
    def get_download(self):
        pass

    @abstractmethod
    def get_total_traffic(self):
        pass

    @abstractmethod
    def get_additional_upload(self):
        pass

    @abstractmethod
    def get_additional_download(self):
        pass

    @abstractmethod
    def get_additional_total_traffic(self):
        pass

    @abstractmethod
    def get_attr_total(self):
        pass

    @abstractmethod
    def get_date(self) -> list[datetime]:
        pass

    @abstractmethod
    def get_date_in_str(self) -> list[str]:
        pass

    @abstractmethod
    def get_date_in_ts(self) -> list[float]:
        pass

    @abstractmethod
    def get_data_by_date_range(self, start_date: datetime = None, end_date: datetime = None) -> "BaseDataList":
        pass

    @abstractmethod
    def get_data_by_gran(self, start_date: datetime = None, end_date: datetime = None,
                         granularity_sec: (int, None) = None) -> ("GranDataList", "BaseDataList"):
        pass

    @abstractmethod
    def get_data_by_count(self, _count: int, start_date: datetime = None, end_date: datetime = None
                          ) -> ("GranDataList", "BaseDataList"):
        pass


class TrafficDataList(BaseDataList):
    def __init__(self, data_list: (Iterable, BaseDataPoint) = None, *args):
        if isinstance(data_list, TrafficDataPoint):
            data_list = [data_list]
            data_list.extend(args)
        super().__init__()
        if data_list:
            self.extend(data_list)

    @classmethod
    def from_list(cls, data_list: list, gmt_offset=0, add_original_point=True):
        data_points = [TrafficDataPoint(data_point_dict, gmt_offset=gmt_offset) for data_point_dict in data_list]
        current_month = data_points[0].date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_ts = current_month.timestamp()
        if add_original_point and not [data_point for data_point in data_points
                                       if data_point.date_in_ts == current_month_ts]:
            """
            self.url = data_point.get("url")
            self.date_in_str = data_point.get("date")
            self.upload = data_point.get("upload")
            self.download = data_point.get("download")
            self.total = data_point.get("total")
            self.expire_in_ts = data_point.get("expire")
            """
            original_point = TrafficDataPoint({
                "url": data_points[0].url,
                "date": current_month.strftime("%Y-%m-%d %H:%M:%S"),
                "upload": 0,
                "download": 0,
                "total": data_points[0].total,
                "expire": data_points[0].expire_in_ts
            })
            data_points.insert(0, original_point)
        return cls(data_points)

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
                result.append((point_total - pre_total)
                              if allow_negative_traffic or point_total > pre_total else 0)
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
                result.append((point_total - pre_total)
                              if allow_negative_traffic or point_total > pre_total else 0)
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
                result.append((point_total - pre_total)
                              if allow_negative_traffic or point_total > pre_total else 0)
            pre_total = point_total
        return result

    def get_attr_total(self):
        return [data_point.total for data_point in self]

    def get_date(self) -> list[datetime]:
        return [data_point.date for data_point in self]

    def get_date_in_str(self, date_format="%Y-%m-%d %H:%M:%S") -> list[str]:
        return [data_point.date.strftime(date_format) for data_point in self]

    def get_date_in_ts(self) -> list[float]:
        return [data_point.date_in_ts for data_point in self]

    def get_data_by_url(self, url: str) -> list[BaseDataPoint]:
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

    def get_data_by_count(self, _count: int, start_date: datetime = None, end_date: datetime = None) -> (
            "GranDataList", None):
        if _count <= 0:
            raise ValueError("count must > 0")
        if start_date is None:
            start_date = self[0].date
        if end_date is None:
            end_date = self[-1].date
        _granularity = (end_date - start_date).total_seconds() / _count
        return self.get_data_by_gran(start_date=start_date, end_date=end_date, granularity_sec=_granularity)

    def latest_month_data(self) -> BaseDataList[BaseDataPoint]:
        start_of_latest_month = self[-1].date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.get_data_by_date_range(start_date=start_of_latest_month, end_date=datetime.now())

    def latest_7days_data(self) -> BaseDataList[BaseDataPoint]:
        start_of_latest_month = self[-1].date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_latest_7days = (self[-1].date - timedelta(days=7)) if (
                (self[-1].date - start_of_latest_month).days > 7) else start_of_latest_month
        return self.get_data_by_date_range(start_date=start_of_latest_7days, end_date=datetime.now())

    def latest_24hours_data(self) -> BaseDataList[BaseDataPoint]:
        start_of_latest_month = self[-1].date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_latest_24hours = (self[-1].date - timedelta(hours=24)) if (
                (self[-1].date - start_of_latest_month).days > 1) else start_of_latest_month
        return self.get_data_by_date_range(start_date=start_of_latest_24hours, end_date=datetime.now())


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

    def get_pre_points(self) -> list[TrafficDataPoint]:
        lst = []
        for item in self:
            if isinstance(item, GranDataPoint):
                lst.append(item.pre_point)
            elif isinstance(item, TrafficDataPoint):
                lst.append(item)
        return lst

    def get_next_points(self) -> list[TrafficDataPoint]:
        lst = []
        for item in self:
            if isinstance(item, GranDataPoint):
                lst.append(item.next_point)
            elif isinstance(item, TrafficDataPoint):
                lst.append(item)
            else:
                continue
        return lst

    def get_date(self) -> list[datetime]:
        return [item.date for item in self]

    def get_date_in_str(self, date_format="%Y-%m-%d %H:%M:%S") -> list[str]:
        return [item.date.strftime(date_format) for item in self]

    def get_date_in_ts(self) -> list[float]:
        return [item.date_in_ts for item in self]

    def get_upload(self) -> list[float]:
        return [item.upload for item in self]

    def get_download(self) -> list[float]:
        return [item.download for item in self]

    def get_total_traffic(self) -> list[float]:
        return [item.total_traffic for item in self]

    def get_additional_upload(self) -> list[float]:
        if len(self) < 1:
            return []
        pre_point_upload = self[0].upload
        result = []
        for point in self:
            point_upload = point.upload
            result.append((point_upload - pre_point_upload)
                          if allow_negative_traffic or point_upload > pre_point_upload else 0)
            pre_point_upload = point_upload
        return result

    def get_additional_download(self) -> list[float]:
        if len(self) < 1:
            return []
        pre_point_download = self[0].download
        result = []
        for point in self:
            point_download = point.download
            result.append((point_download - pre_point_download)
                          if allow_negative_traffic or point_download > pre_point_download else 0)
            pre_point_download = point_download
        return result

    def get_additional_total_traffic(self) -> list[float]:
        if len(self) < 1:
            return []
        pre_point_total = self[0].total_traffic
        result = []
        for point in self:
            point_total = point.total_traffic
            result.append((point_total - pre_point_total)
                          if allow_negative_traffic or point_total > pre_point_total else 0)
            pre_point_total = point_total
        return result

    def get_upload_rate_sec(self) -> list[float]:
        if len(self) < 1:
            return []
        return [additional / self.granularity_sec for additional in self.get_additional_upload()]

    def get_download_rate_sec(self) -> list[float]:
        if len(self) < 1:
            return []
        return [additional / self.granularity_sec for additional in self.get_additional_download()]

    def get_rate_sec(self) -> list[float]:
        if len(self) < 1:
            return []
        return [additional / self.granularity_sec for additional in self.get_additional_total_traffic()]

    def get_data_by_date_range(self, start_date: datetime = None, end_date: datetime = None) -> TrafficDataList:
        """return a list of TrafficDataPoint from start_date to before end_date"""
        if start_date is None:
            start_date = self[0].date
        if end_date is None:
            end_date = self[-1].date + timedelta(microseconds=1)
        return TrafficDataList([point for point in self if start_date <= point.date < end_date])

    def get_data_by_gran(self, start_date: datetime = None, end_date: datetime = None,
                         granularity_sec: int = None) -> "GranDataList":
        points = []
        recorded_date = []
        for point in self:
            if isinstance(point, TrafficDataPoint) and point.date_in_ts not in recorded_date:
                points.append(point)
                recorded_date.append(point.date)
            elif isinstance(point, GranDataPoint) and point.date not in recorded_date:
                if point.pre_point.date_in_ts not in recorded_date:
                    points.append(point.pre_point)
                    recorded_date.append(point.pre_point.date_in_ts)
                if point.next_point.date_in_ts not in recorded_date:
                    points.append(point.next_point)
                    recorded_date.append(point.next_point.date_in_ts)
        return TrafficDataList(points).get_data_by_gran(start_date=start_date, end_date=end_date,
                                                        granularity_sec=granularity_sec)

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


def traffic_to_gb_in_str(traffic, _prec=3) -> str:
    """
    Convert traffic from bytes to gigabytes and return the result as a string.
    """
    if not isinstance(_prec, int) or _prec < 0:
        _prec = 3
    return f"{traffic / 1024 / 1024 / 1024} GB"


def traffic_to_mb_in_str(traffic, _prec=3) -> str:
    """
    Converts the given traffic value in bytes to megabytes.
    """
    if not isinstance(_prec, int) or _prec < 0:
        _prec = 3
    return f"{traffic / 1024 / 1024} MB"


def list_to_mb_in_float(data: list[float | int]):
    return [item / 1024 / 1024 for item in data]


def list_to_gb_in_float(data: list[float | int]):
    return [item / 1024 / 1024 / 1024 for item in data]


def track_group(data: (TrafficDataList[TrafficDataPoint], GranDataList[TrafficDataPoint, GranDataPoint]),
                _prec=3) -> OrderedDict[str, str]:
    """return a dict of information by the group name"""
    # collect_all data by time
    start_of_month = data[-1].date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if isinstance(data, TrafficDataList):
        data = data.latest_month_data().get_data_by_gran(granularity_sec=60 * 60)
    elif isinstance(data, GranDataList):
        data = data.latest_month_data()
    if len(data) <= 0:
        raise ValueError(f"No sufficient data in the time interval")

    # disposal data
    latest_point: BaseDataPoint = data[-1]
    latest_date = latest_point.date

    traffic_limit = latest_point.total
    expire = latest_point.expire

    total_upload = latest_point.upload
    total_download = latest_point.download
    total_traffic = latest_point.total_traffic
    available_traffic = traffic_limit - total_traffic
    used_percent = total_traffic / traffic_limit
    available_percent = available_traffic / traffic_limit

    # month additional traffic is equal to the total traffic
    month_speed_of_day = total_traffic / latest_date.day
    month_traffic_predicted = month_speed_of_day * (
            start_of_month.replace(month=start_of_month.month + 1) - start_of_month).days

    _7days_earliest_point: BaseDataPoint = data.latest_7days_data()[0]
    start_of_7days = _7days_earliest_point.date
    _7days_additional_upload_traffic = total_upload - _7days_earliest_point.upload
    _7days_additional_download_traffic = total_download - _7days_earliest_point.download
    _7days_additional_traffic = _7days_additional_upload_traffic + _7days_additional_download_traffic
    # todo: week prediction is incorrect
    if (latest_date - start_of_7days).days:
        _7days_speed_of_day = _7days_additional_traffic / (latest_date - start_of_7days).days
    elif (latest_date - start_of_7days).seconds:
        _7days_speed_of_day = _7days_additional_traffic / (latest_date - start_of_7days).seconds * 3600
    else:
        _7days_speed_of_day = 0
    _7days_traffic_predicted = (_7days_speed_of_day * 7 +
                                _7days_earliest_point.upload + _7days_earliest_point.download)

    # todo:week prediction is incorrect
    _7days_traffic_predicted_by_month = total_traffic + month_speed_of_day * (latest_date - start_of_month).days
    month_traffic_predicted_by_7days = total_traffic + _7days_speed_of_day * (start_of_month.replace(
        month=start_of_month.month + 1) - latest_date).days

    # abandon to statistics by day because of prediction inaccuracy
    # start_of_day = latest_date.replace(hour=0, minute=0, second=0, microsecond=0)
    # day_earliest_point = [point for point in data
    #                       if datetime.strptime(point.get('date'), "%Y-%m-%d %H:%M:%S") >= start_of_day][0]
    # day_additional_upload_traffic = latest_point.upload - day_earliest_point.upload
    # day_additional_download_traffic = latest_point.download - day_earliest_point.download
    # day_additional_traffic = day_additional_upload_traffic + day_additional_download_traffic
    # day_speed = day_additional_traffic / (latest_date - start_of_day).days

    track_data: OrderedDict[str, str] = OrderedDict()
    track_data['Current available traffic'] = traffic_to_gb_in_str(available_traffic, _prec=_prec)
    track_data['Traffic limitation'] = traffic_to_gb_in_str(traffic_limit, _prec=_prec)
    track_data['Total traffic used'] = traffic_to_gb_in_str(total_traffic, _prec=_prec)
    track_data['Upload traffic used'] = traffic_to_gb_in_str(total_upload, _prec=_prec)
    track_data['Download traffic used'] = traffic_to_gb_in_str(total_download, _prec=_prec)
    track_data['Total in latest 7days'] = traffic_to_gb_in_str(_7days_additional_traffic, _prec=_prec)
    track_data['Upload in latest 7days'] = traffic_to_gb_in_str(_7days_additional_upload_traffic, _prec=_prec)
    track_data['Download in latest 7days'] = traffic_to_gb_in_str(_7days_additional_download_traffic, _prec=_prec)
    track_data['Expiration time'] = expire.strftime("%Y-%m-%d %H:%M:%S")
    track_data['Available percentage'] = f"{available_percent * 100:.{_prec}f}%" \
        if _prec >= 0 else f"{available_percent * 100}%"
    track_data['Used percentage'] = f"{used_percent * 100:.{_prec}f}%" \
        if _prec >= 0 else f"{used_percent * 100}%"
    track_data[
        'Average speed of day in month'] = f"{traffic_to_gb_in_str(month_speed_of_day, _prec=_prec).rstrip()}/day"
    track_data[
        'Average speed of day in 7days'] = f"{traffic_to_gb_in_str(_7days_speed_of_day, _prec=_prec).rstrip()}/day"
    track_data['Traffic will be used by the end of the month predicted by the latest month data'] = \
        traffic_to_gb_in_str(month_traffic_predicted, _prec=_prec)
    track_data['Traffic will be used by the end of the month predicted by the latest 7 days data'] = \
        traffic_to_gb_in_str(month_traffic_predicted_by_7days, _prec=_prec)
    track_data['Traffic will be used by the end of the week predicted by the latest month data'] = \
        traffic_to_gb_in_str(_7days_traffic_predicted_by_month, _prec=_prec)
    track_data['Traffic will be used by the end of the week predicted by the latest 7 days data'] = \
        traffic_to_gb_in_str(_7days_traffic_predicted, _prec=_prec)

    return track_data


def _test():
    from rich import print

    data = parse_data([json_file for json_file in os.listdir(data_folder_path) if json_file.endswith('.json')][0])
    # print(data)

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
