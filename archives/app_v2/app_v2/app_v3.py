from flask import Flask, jsonify, render_template, redirect, url_for

app = Flask(__name__)


# Sample data
traffic_data = [{
    'type': 'line',
    'name': 'TrafficSampleData',
    'x-axes': {
        'name': 'Date',
        'labels': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
    },
    'y-axes': {
        'name': 'Traffic(MB)'
    },
    'lines': [
        {
            'label': 'Line1',
            'data': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        },
        {
            'label': 'Line2',
            'data': [1, 3, 2, 4, 5, 7, 6, 8, 11, 10],
            'border-color': 'coral',
            'background-color': 'coral'
        }
    ]
}]


@app.route('/get_data')
def get_data():
    print(jsonify(traffic_data))
    return jsonify(traffic_data)


@app.route('/')
def index():
    return redirect(url_for('dashboard_glance'))


@app.route('/dashboard_glance')
def dashboard_glance():
    return render_template('dashboard_glance.html')


@app.route('/dashboard_pro')
def dashboard_pro():
    return render_template('dashboard_pro.html')


if __name__ == '__main__':
    app.run(debug=True)
