# 前端
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# 测试样例
sample_data = {
    'remaining_vs_total': '100G/250G 40%',
    'time_to_reset': '3天',
    'traffic_vs_time': {
        'time_intervals': ['0-10', '10-20', '20-30', '30-40', '40-50', "50-60"],
        'traffic_consumed': [100, 150, 80, 60, 80, 70]
    },
    'rate_vs_time': {
        'time_intervals': ['0-10', '10-20', '20-30', '30-40', '40-50', "50-60"],
        'traffic_rate': [10, 15, 8, 6, 8, 7]
    }
}
sample_data2 = {
    'remaining_vs_total': '125G/250G 50%',
    'time_to_reset': '4天',
    'traffic_vs_time': {
        'time_intervals': ['0-10', '10-20', '20-30'],
        'traffic_consumed': [100, 150, 80]
    },
    'rate_vs_time': {
        'time_intervals': ['0-10', '10-20', '20-30'],
        'traffic_rate': [10, 15, 8]
    }
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/data', methods=['GET'])
def get_data():
    global a
    # 获取查询参数
    start_time = request.args.get('start_time', '默认起始时间')
    end_time = request.args.get('end_time', '默认结束时间')
    granularity = request.args.get('granularity', '默认颗粒度')
    print(start_time,end_time,granularity)
    # 基于查询参数处理数据（这里仅返回示例数据）
    data,a = (sample_data,1) if a==0 else (sample_data2,0)
    return jsonify(data)


if __name__ == "__main__":
    a=0
    app.run(host="0.0.0.0", port=5000, debug="True")
