import os
from dataclasses import asdict

from flask import Flask, jsonify, render_template, redirect, url_for

import plot
from models import parse_data, data_folder_path, TrafficDataList, list_to_mb, list_to_gb, GranDataList

app = Flask(__name__)


@app.route('/get_data_glance')
def get_data():
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
                            plot.ChartJS.Line(name="upload", data=list_to_gb(month_traffic_data.get_upload()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download", data=list_to_gb(month_traffic_data.get_download()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total", data=list_to_gb(month_traffic_data.get_total_traffic()),
                                              border_color="coral", background_color="#282C34")
                        ])
    _plot.add_line_plot(title="Traffic Speed", x_axis_name="Date", y_axis_name="Traffic(MB/s)",
                        labels=month_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload", data=list_to_mb(month_traffic_data.get_upload_rate_sec()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download",
                                              data=list_to_mb(month_traffic_data.get_download_rate_sec()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total", data=list_to_mb(month_traffic_data.get_rate_sec()),
                                              border_color="coral", background_color="#282C34"),
                        ])
    _7days_traffic_data: GranDataList = raw_traffic_data.latest_7days_data().get_data_by_gran(granularity_sec=60 * 60)
    _plot.add_line_plot(title="Traffic in latest 7 days", x_axis_name="Date", y_axis_name="Traffic(GB)",
                        labels=_7days_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload", data=list_to_gb(_7days_traffic_data.get_upload()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download", data=list_to_gb(_7days_traffic_data.get_download()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total", data=list_to_gb(_7days_traffic_data.get_total_traffic()),
                                              border_color="coral", background_color="#282C34"),
                        ])
    _plot.add_line_plot(title="Traffic Speed in latest 7 days", x_axis_name="Date", y_axis_name="Traffic(MB/s)",
                        labels=_7days_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload", data=list_to_mb(_7days_traffic_data.get_upload_rate_sec()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download",
                                              data=list_to_mb(_7days_traffic_data.get_download_rate_sec()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total", data=list_to_mb(_7days_traffic_data.get_rate_sec()),
                                              border_color="coral", background_color="#282C34"),
                        ])
    _24hours_traffic_data: GranDataList = raw_traffic_data.latest_24hours_data().get_data_by_gran(
        granularity_sec=60 * 10)
    _plot.add_line_plot(title="Traffic in latest 24 hours", x_axis_name="Date", y_axis_name="Traffic(GB)",
                        labels=_24hours_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload", data=list_to_gb(_24hours_traffic_data.get_upload()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download", data=list_to_gb(_24hours_traffic_data.get_download()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total", data=list_to_gb(_24hours_traffic_data.get_total_traffic()),
                                              border_color="coral", background_color="#282C34"),
                        ])
    _plot.add_line_plot(title="Traffic Speed in latest 24 hours", x_axis_name="Date", y_axis_name="Traffic(MB/s)",
                        labels=_24hours_traffic_data.get_date_in_str(),
                        lines=[
                            plot.ChartJS.Line(name="upload",
                                              data=list_to_mb(_24hours_traffic_data.get_upload_rate_sec()),
                                              border_color="lightgreen", background_color="#282C34"),
                            plot.ChartJS.Line(name="download",
                                              data=list_to_mb(_24hours_traffic_data.get_download_rate_sec()),
                                              border_color="cyan", background_color="#282C34"),
                            plot.ChartJS.Line(name="total", data=list_to_mb(_24hours_traffic_data.get_rate_sec()),
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
        title="Available Traffic", labels=["Upload", "Download", "Available"], cutoutPercentage="18%", datasets=[
            plot.ChartJS.Pie(name="Traffic(GB)", background_colors=["#84a729", "#004c6d", "coral"], data=[
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
    # _response = jsonify(_plot.asdict())
    _response = jsonify(dict(row=_plot.asdict(), percentageAvailableChart=asdict(percentage_available_chart)))
    return _response


@app.route('/')
def index():
    return redirect(url_for('dashboard_glance'))


@app.route('/dashboard_glance')
def dashboard_glance():
    return render_template('dashboard_glance.html')


@app.route('/dashboard_pro')
def dashboard_pro():
    return render_template('dashboard_pro.html')  # todo: add dashboard_pro.html


if __name__ == '__main__':
    app.run(debug=True)
