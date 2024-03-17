import plotly.express as px
from flask import Flask, render_template, render_template_string

app = Flask(__name__)

# Mock data for demonstration
traffic_data = {
    "dates": ["2024-03-01", "2024-03-02", "2024-03-03", "2024-03-04", "2024-03-05"],
    "visits": [100, 150, 120, 200, 180]
}


@app.route('/')
def index():
    # Create Plotly line chart with dark mode
    chart = px.line(x=traffic_data["dates"], y=traffic_data["visits"], title='Traffic Usage Over Time')
    chart.update_layout(template='plotly_dark')

    # Render the template with Plotly chart
    return render_template('index.html', chart=chart)


if __name__ == '__main__':
    app.run(debug=True)
