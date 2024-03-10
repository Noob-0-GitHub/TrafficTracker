from math import log2

import asciichartpy as acp

from models import TrafficDataList


def plot_total_traffic(traffic_data_list: TrafficDataList):
    return acp.plot([point / (1024 ** 3) / 10 for point in traffic_data_list.get_total_traffic()][:128])


def plot_additional_total_traffic(traffic_data_list: TrafficDataList):
    return acp.plot([point / (1024 ** 3) for point in traffic_data_list.get_additional_total_traffic()][:128])


def plot_rate(traffic_data_list: TrafficDataList):
    return acp.plot(
        [int(round(log2(point // (1024 ** 1)+1))) for point in traffic_data_list.get_rate_sec()][:128])


def _test():
    from main import parse_data

    while True:
        # data = TrafficDataList.from_list(parse_data(f"{input('group name = ')}.json"))
        data = TrafficDataList.from_list(parse_data(f"TAG.json"))
        print(len(data))
        data_with_gran = data.get_data_with_gran(granularity_sec=60 * 60)
        print(len(data_with_gran))
        print(data_with_gran.get_total_traffic())
        print(data_with_gran.get_additional_total_traffic())
        # print(plot_total_traffic(data_with_gran))
        # print(plot_additional_total_traffic(data_with_gran))
        # print(data_with_gran.get_rate_sec())
        # print(plot_rate(data_with_gran))
        input()


if __name__ == '__main__':
    _test()
