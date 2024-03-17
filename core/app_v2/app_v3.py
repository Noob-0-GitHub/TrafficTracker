from flask import Flask, jsonify, render_template, redirect, url_for

app = Flask(__name__)

"""
            if graphInfo['type'] == 'line'{
                var xAxes = graphInfo['x-axes'];
                var yAxes = graphInfo['y-axes'];
                var lines = graphInfo['lines'];

                datasets = [];
                lines.forEach(function(line) {
                    var backgroundColor = line['background-color'];
                    if (!backgroundColor) {
                        backgroundColor = 'rgba(75, 192, 192, 0.2)';
                    }
                    var borderColor = line['border-color'];
                    if (!borderColor) {
                        borderColor = 'rgba(75, 192, 192, 1)';
                    }
                    var borderWidth = line['border-width'];
                    if (!borderWidth) {
                        borderWidth = 1
                    }
                    datasets.push({
                        label: line['label'],
                        data: line['data'],
                        backgroundColor: backgroundColor,
                        borderColor: borderColor,
                        borderWidth: borderWidth
                    })
                })

                var ctx = document.getElementById('chart').getContext('2d');
                var newChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: xAxes['labels'],
                        datasets: datasets
                    }
                } 
                options: {
                    scales: {
                        xAxes: [{
                            scaleLabel: {
                                display: true,
                                labelString: xAxes['name']
                            }
                        }],
                        yAxes: [{
                            scaleLabel: {
                                display: true,
                                labelString: yAxes['name']
                            }
                        }]
                    }
                });
"""
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
            'data': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
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
    return render_template('dashboard_pro.html')  # todo: add dashboard_pro.html


if __name__ == '__main__':
    app.run(debug=True)
