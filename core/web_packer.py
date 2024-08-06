import csv
import os
import re
import warnings
from dataclasses import asdict

from flask import jsonify

import plot
from models import data_folder_path, parse_data, list_data_file_name, TrafficDataList, list_to_mb_in_float, \
    list_to_gb_in_float, \
    GranDataList, track_group

default_translation_table_path = os.path.join(os.path.dirname(__file__), 'translation', 'translation_table.csv')

date_label_regex = re.compile(r"\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?")


def dict_merge(*dicts):
    result = {}
    for d in dicts:
        result.update(d)
    return result


def build_translation_dict(init_language: str, target_language,
                           translation_table_path: str = default_translation_table_path) -> (dict, list):
    with open(translation_table_path, 'r', encoding='utf-8') as _f:
        trans_table_reader = csv.reader(_f)
        titles = next(trans_table_reader)
        titles_regex = [re.compile(_t, re.IGNORECASE) for _t in titles]
        init_language_index = target_language_index = -1
        for title_regex in titles_regex:
            if title_regex.match(init_language):
                init_language_index = titles.index(title_regex.pattern)
            if title_regex.match(target_language):
                target_language_index = titles.index(title_regex.pattern)
        if init_language_index == -1:
            warnings.warn(RuntimeWarning(f"init_language '{init_language}' not found in translation_table"))
            init_language_index = 0
        if target_language_index == -1:
            warnings.warn(RuntimeWarning(f"target_language '{target_language}' not found in translation_table"))
            target_language_index = 0
        trans_table: dict[str, str] = {}
        trans_re_list: list[list[re.Pattern | str]] = []
        for row in trans_table_reader:
            if row[init_language_index].startswith("re:"):
                trans_re_list.append([re.compile(row[init_language_index][3:], re.IGNORECASE),
                                      row[target_language_index]])
            else:
                trans_table[row[init_language_index].lower()] = row[target_language_index]
    return trans_table, trans_re_list


def dict_translate(_dict: dict, trans_table: dict[str, str], trans_re_list: list[re.Pattern, str]):
    new_dict = {}
    for key, value in _dict.items():
        if isinstance(key, str):
            if key.lower() in trans_table:
                key = trans_table[key.lower()]
            else:
                for trans_row in trans_re_list:
                    if trans_row[0].match(key):
                        key = trans_row[1]
                        break

        if isinstance(value, str):
            if value.lower() in trans_table:
                value = trans_table[value.lower()]
            else:
                for trans_row in trans_re_list:
                    if trans_row[0].match(value):
                        value = trans_row[1]
                        break

        new_dict[key] = value
    return new_dict


def deep_dict_translate(_dict: dict, trans_table: dict[str, str], trans_re_list: list[re.Pattern, str],
                        skip_keys: (tuple[str], list[str]) = (
                                'data', 'titleFontSize', 'titleColor', 'backgroundColor', 'borderColor',
                                'fill', 'pointRadius', 'pointBackgroundColor', 'pointBorderColor', 'tension',
                                'type', 'value', 'circumference', 'cutoutPercentage', 'rotation'
                        )):
    # return dict_merge(
    #     dict_translate({key: value for key, value in _dict.items()
    #                     if not isinstance(value, dict)}, trans_table, trans_re_list),
    #     {key: deep_dict_translate(value, trans_table, trans_re_list) for key, value in _dict.items()
    #      if isinstance(value, dict)},
    #     {key: [deep_dict_translate(i, trans_table, trans_re_list) for i in value] for key, value in _dict.items()
    #      if isinstance(value, list)}
    # ) if isinstance(_dict, dict) else _dict
    if isinstance(_dict, str) and _dict.lower() in trans_table:
        return trans_table[_dict.lower()]
    if not isinstance(_dict, dict):
        return _dict
    translatable = {}
    untranslatable = {}
    for key, value in _dict.items():
        if key in skip_keys:
            untranslatable[key] = value
            # print(f"skip {key}: {value}")
        elif isinstance(value, dict):
            untranslatable[key] = deep_dict_translate(value, trans_table, trans_re_list)
        elif isinstance(value, list):
            if value and isinstance(value[0], str) and date_label_regex.match(value[0]):
                # print(f"skip {key}: {value}")
                untranslatable[key] = value
            else:
                untranslatable[key] = [deep_dict_translate(i, trans_table, trans_re_list) for i in value]
        else:
            translatable[key] = value
    return dict_merge(
        dict_translate(translatable, trans_table, trans_re_list),
        untranslatable
    )


def dashboard_glance_data_packer(filename: str = None, language: str = "en"):
    if filename:
        raw_traffic_data: TrafficDataList = TrafficDataList.from_list(parse_data(filename))
    else:
        raw_traffic_data: TrafficDataList = TrafficDataList.from_list(
            parse_data([json_file for json_file in os.listdir(data_folder_path)
                        if json_file.endswith('.json')][0]))

    month_traffic_data: GranDataList = raw_traffic_data.latest_month_data(
    ).get_data_by_gran(granularity_sec=60 * 60, start_date=raw_traffic_data.get_date()[-1].replace(
        day=1, hour=0, minute=0, second=0, microsecond=0))
    _plot = plot.ChartJS()
    # noinspection PyTypeChecker
    _plot.add_line_plot(title="Traffic", x_axis_name="Date", y_axis_name="Traffic(GB)",
                        labels=month_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload", data=list_to_gb_in_float(month_traffic_data.get_upload()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download",
                                              data=list_to_gb_in_float(month_traffic_data.get_download()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total",
                                              data=list_to_gb_in_float(month_traffic_data.get_total_traffic()),
                                              border_color="coral", background_color="#282C34")
                        ])
    _plot.add_line_plot(title="Traffic Speed", x_axis_name="Date", y_axis_name="Traffic(MB/s)",
                        labels=month_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload",
                                              data=list_to_mb_in_float(month_traffic_data.get_upload_rate_sec()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download",
                                              data=list_to_mb_in_float(month_traffic_data.get_download_rate_sec()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total", data=list_to_mb_in_float(month_traffic_data.get_rate_sec()),
                                              border_color="coral", background_color="#282C34"),
                        ])
    _7days_traffic_data: GranDataList = raw_traffic_data.latest_7days_data().get_data_by_gran(granularity_sec=60 * 60)
    _plot.add_line_plot(title="Traffic in latest 7 days", x_axis_name="Date", y_axis_name="Traffic(GB)",
                        labels=_7days_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload", data=list_to_gb_in_float(_7days_traffic_data.get_upload()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download",
                                              data=list_to_gb_in_float(_7days_traffic_data.get_download()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total",
                                              data=list_to_gb_in_float(_7days_traffic_data.get_total_traffic()),
                                              border_color="coral", background_color="#282C34"),
                        ])
    _plot.add_line_plot(title="Traffic Speed in latest 7 days", x_axis_name="Date", y_axis_name="Traffic(MB/s)",
                        labels=_7days_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload",
                                              data=list_to_mb_in_float(_7days_traffic_data.get_upload_rate_sec()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download",
                                              data=list_to_mb_in_float(_7days_traffic_data.get_download_rate_sec()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total",
                                              data=list_to_mb_in_float(_7days_traffic_data.get_rate_sec()),
                                              border_color="coral", background_color="#282C34"),
                        ])
    _24hours_traffic_data: GranDataList = raw_traffic_data.latest_24hours_data().get_data_by_gran(
        granularity_sec=60 * 10)
    _plot.add_line_plot(title="Traffic in latest 24 hours", x_axis_name="Date", y_axis_name="Traffic(GB)",
                        labels=_24hours_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload",
                                              data=list_to_gb_in_float(_24hours_traffic_data.get_upload()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download",
                                              data=list_to_gb_in_float(_24hours_traffic_data.get_download()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total",
                                              data=list_to_gb_in_float(_24hours_traffic_data.get_total_traffic()),
                                              border_color="coral", background_color="#282C34"),
                        ])
    _plot.add_line_plot(title="Traffic Speed in latest 24 hours", x_axis_name="Date", y_axis_name="Traffic(MB/s)",
                        labels=_24hours_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload",
                                              data=list_to_mb_in_float(_24hours_traffic_data.get_upload_rate_sec()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download",
                                              data=list_to_mb_in_float(_24hours_traffic_data.get_download_rate_sec()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total",
                                              data=list_to_mb_in_float(_24hours_traffic_data.get_rate_sec()),
                                              border_color="coral", background_color="#282C34"),
                        ])
    # _plot.add_pie_plot(title="Traffic(GB)", cutout_percentage="20%",
    #                    area_names=["Upload", "Download", "Available"], areas_data=[
    #         plot.ChartJS.Pie(name="Traffic(GB)", background_colors=["#84a729", "#004c6d", "coral"], data=[
    #             month_traffic_data.get_upload()[-1] / 1024 / 1024 / 1024,
    #             month_traffic_data.get_download()[-1] / 1024 / 1024 / 1024,
    #             (month_traffic_data[-1].total - month_traffic_data.get_total_traffic()[-1]) / 1024 / 1024 / 1024
    #         ], ),
    #         plot.ChartJS.Pie(name="Traffic in last 7 days(GB)", background_colors=["#9ebc19", "#0582b3"], data=[
    #             sum(_7days_traffic_data.get_additional_upload()) / 1024 / 1024 / 1024,
    #             sum(_7days_traffic_data.get_additional_download()) / 1024 / 1024 / 1024,
    #         ], ),
    #         plot.ChartJS.Pie(name="Traffic in last 24 hours(GB)", background_colors=["#b7d332", "#00bdff"], data=[
    #             sum(_24hours_traffic_data.get_additional_upload()) / 1024 / 1024 / 1024,
    #             sum(_24hours_traffic_data.get_additional_download()) / 1024 / 1024 / 1024,
    #         ], ),
    #     ])

    percentage_available_chart = plot.ChartJS.PiePlot(
        title="Available Traffic", labels=["Total upload(GB)", "Total download(GB)", "Available(GB)"],
        cutoutPercentage="18%", datasets=[
            plot.ChartJS.Pie(name="Traffic total(GB)", background_colors=["#84a729", "#004c6d", "coral"], data=[
                month_traffic_data.get_upload()[-1] / 1024 / 1024 / 1024,
                month_traffic_data.get_download()[-1] / 1024 / 1024 / 1024,
                (month_traffic_data[-1].total - month_traffic_data.get_total_traffic()[-1]) / 1024 / 1024 / 1024
            ], ),
            plot.ChartJS.Pie(name="Traffic in last 7 days(GB)", background_colors=["#9ebc19", "#0582b3"], data=[
                sum(_7days_traffic_data.get_additional_upload()) / 1024 / 1024 / 1024,
                sum(_7days_traffic_data.get_additional_download()) / 1024 / 1024 / 1024,
            ], ),
            plot.ChartJS.Pie(name="Traffic in last 24 hours(GB)", background_colors=["#b7d332", "#00bdff"], data=[
                sum(_24hours_traffic_data.get_additional_upload()) / 1024 / 1024 / 1024,
                sum(_24hours_traffic_data.get_additional_download()) / 1024 / 1024 / 1024,
            ], ),
        ]
    )
    data_panel_info_table = [{"name": _k, "value": _v} for _k, _v in track_group(month_traffic_data).items()]
    response_dict = dict(row=_plot.asdict(), percentageAvailableChart=asdict(percentage_available_chart),
                         infoTable=data_panel_info_table, filename=filename)
    if language == 'zh':
        trans_table, trans_re_list = en_to_zh_trans_table, en_to_zh_trans_re_list
    else:
        trans_table, trans_re_list = build_translation_dict("en", language)
    response_dict = deep_dict_translate(response_dict, trans_table, trans_re_list)
    _response = jsonify(response_dict)
    return _response


def dashboard_glance_data_list_packer():
    data_list = list_data_file_name(keep_extension=False)
    _response = jsonify(data_list)
    return _response


en_to_zh_trans_table, en_to_zh_trans_re_list = build_translation_dict('en', 'zh')

if __name__ == '__main__':
    # translation test
    print(deep_dict_translate({'traffic': 20, 'lines': {'upload': 10, 'download': 10}},
                              en_to_zh_trans_table, en_to_zh_trans_re_list))
