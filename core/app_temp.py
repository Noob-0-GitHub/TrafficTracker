import os

from flask import Flask, jsonify, render_template, redirect, url_for

import plot
from models import parse_data, data_folder_path, TrafficDataList, GranDataList

app = Flask(__name__)


@app.route('/get_data')
def get_data():
    traffic_data: GranDataList = TrafficDataList.from_list(
        parse_data([json_file for json_file in os.listdir(data_folder_path)
                    if json_file.endswith('.json')][0])).get_data_by_gran(granularity_sec=3600)
    _plot = plot.ChartJS()
    _plot.add_line_plot(name="Traffic", labels=traffic_data.get_date_in_str(), datasets=[
        plot.ChartJS.Line(label="total", data=traffic_data.get_total_traffic(),
                          borderColor="yellow", backgroundColor="#282C34"),
        plot.ChartJS.Line(label="upload", data=traffic_data.get_upload(),
                          borderColor="lightgreen", backgroundColor="#282C34"),
        plot.ChartJS.Line(label="download", data=traffic_data.get_download(),
                          borderColor="cyan", backgroundColor="#282C34"),
    ])
    _plot.add_line_plot(name="Additional Traffic", labels=traffic_data.get_date_in_str(), datasets=[
        plot.ChartJS.Line(label="total", data=traffic_data.get_additional_total_traffic(),
                          borderColor="yellow", backgroundColor="#282C34"),
        plot.ChartJS.Line(label="upload", data=traffic_data.get_additional_upload(),
                          borderColor="lightgreen", backgroundColor="#282C34"),
        plot.ChartJS.Line(label="download", data=traffic_data.get_additional_download(),
                          borderColor="cyan", backgroundColor="#282C34"),
    ])
    _plot.add_line_plot(name="Traffic Speed", labels=traffic_data.get_date_in_str(), datasets=[
        plot.ChartJS.Line(label="total", data=traffic_data.get_rate_sec(),
                          borderColor="yellow", backgroundColor="#282C34"),
        plot.ChartJS.Line(label="upload", data=traffic_data.get_upload_rate_sec(),
                          borderColor="lightgreen", backgroundColor="#282C34"),
        plot.ChartJS.Line(label="download", data=traffic_data.get_download_rate_sec(),
                          borderColor="cyan", backgroundColor="#282C34"),
    ])
    print(_plot.json())
    _response = jsonify(_plot.asdict())
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
