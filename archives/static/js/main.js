// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    fetchData()
});

// static/js/main.js
function fetchData() {
    const startTime = document.getElementById('start_time').value;
    const endTime = document.getElementById('end_time').value;
    const granularity = document.getElementById('granularity').value;

    // 使用fetch API发送请求
    fetch(`/api/data?start_time=${startTime}&end_time=${endTime}&granularity=${granularity}`)
        .then(response => response.json())
        .then(data => {
            // 更新剩余流量和自动重置时间
            document.getElementById('remaining_vs_total').textContent = data.remaining_vs_total;
            document.getElementById('time_to_reset').textContent = data.time_to_reset;

            // 更新流量与时间图表
            Plotly.newPlot('traffic_vs_time', [{
                x: data.traffic_vs_time.time_intervals,
                y: data.traffic_vs_time.traffic_consumed,
                type: 'bar',
                mode: 'lines',
                marker: { color: '#ff4d4d' }
            }], {
                yaxis: {
                    title: '流量 (GB)'
                }
            });

            // 更新流量速率与时间图表
            Plotly.newPlot('rate_vs_time', [{
                x: data.rate_vs_time.time_intervals,
                y: data.rate_vs_time.traffic_rate,
                type: 'scatter',
                mode: 'lines',
                line: {
                    width: 3,
                    color: '#ff4d4d'
                }
            }], {
                yaxis: {
                    title: '速率 (Mbps)'
                }
            });
        });
}
