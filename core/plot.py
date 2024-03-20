import json
from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime


def del_null_in_dict(d: dict):
    for k, v in list(d.items()):
        if v is None:
            del d[k]
        elif isinstance(v, dict):
            del_null_in_dict(v)
    return d


class JSONEncoder(json.JSONEncoder):
    del_null = True

    def default(self, obj):
        if is_dataclass(obj):
            return del_null_in_dict(asdict(obj)) if JSONEncoder.del_null else asdict(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class ChartJS:
    """
    Interface for Chart.js
    """

    @dataclass
    class _Line:
        """
        Args:
            label: str # line name
            data: list[float | int]
            borderColor: str
            borderWidth: int
            backgroundColor: str
            pointRadius: int
            tension: float
        """
        label: str  # line name
        data: list[float | int]
        borderColor: str
        borderWidth: int
        backgroundColor: str
        pointRadius: int
        tension: float

    @classmethod
    def Line(cls, name: str, data: list[float | int], border_color: str = None, border_width: int = 1,
             background_color: str = None, point_radius: int = 0, tension: float = 0.1) -> _Line:
        return cls._Line(label=name, data=data, borderColor=border_color, borderWidth=border_width,
                         backgroundColor=background_color, pointRadius=point_radius, tension=tension)

    @dataclass
    class LinePlot:
        """
        Args:
            title: str
            datasets: list["ChartJS.Line"]  # lines
            labels: list[str] = None  # labels for main axis(input axis)
        """
        datasets: list["ChartJS.Line"]  # lines
        labels: list[str] = None  # labels for main axis(input axis)
        title: str = None
        titleColor: str = None
        titleFontSize: int = None
        xAxisName: str = None
        xAxisColor: str = None
        xAxisFontSize: int = None
        yAxisName: str = None
        yAxisColor: str = None
        yAxisFontSize: int = None

    def __init__(self):
        self.plots = []

    def add_line_plot(self, title: str, lines: list[Line], labels: list[str] = None,
                      title_color: str = None, title_font_size: int = None,
                      x_axis_name: str = None, x_axis_color: str = None, x_axis_font_size: int = None,
                      y_axis_name: str = None, y_axis_color: str = None, y_axis_font_size: int = None):
        self.plots.append(self.LinePlot(title=title, datasets=lines, labels=labels,
                                        titleColor=title_color, titleFontSize=title_font_size,
                                        xAxisName=x_axis_name, xAxisColor=x_axis_color, xAxisFontSize=x_axis_font_size,
                                        yAxisName=y_axis_name, yAxisColor=y_axis_color, yAxisFontSize=y_axis_font_size))

    def json(self) -> str:
        return json.dumps(self.plots, cls=JSONEncoder)

    def asdict(self):
        return json.loads(self.json())


class PlotlyJS:
    """
    Interface for Plotly.js
    """

    def __init__(self):
        self.plots = []


def _test():
    chart_js_plot = ChartJS()

    chart_js_plot.add_line_plot(title="test", lines=[
        ChartJS.Line(name="line1", data=[1, 2, 3, 4, 5], border_color="red", border_width=1, background_color="red",
                     point_radius=1, tension=0.5),
    ])

    print(chart_js_plot.json())


if __name__ == '__main__':
    _test()
