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
        fill: bool
        pointRadius: int
        tension: float

    @classmethod
    def Line(cls, name: str, data: list[float | int], border_color: str = None, border_width: int = 1,
             background_color: str = None, fill: bool = False, point_radius: int = 0, tension: float = 0.1) -> _Line:
        return cls._Line(label=name, data=data, borderColor=border_color, borderWidth=border_width,
                         backgroundColor=background_color, fill=fill, pointRadius=point_radius, tension=tension)

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
        titleFontSize: int = 20
        xAxisName: str = None
        xAxisColor: str = None
        xAxisFontSize: int = None
        yAxisName: str = None
        yAxisColor: str = None
        yAxisFontSize: int = None

        type: str = "line"

    @dataclass
    class _Pie:
        name: str
        data: list[float | int]
        borderColor: str
        borderWidth: int
        borderDash: int
        backgroundColor: list[str]

    @classmethod
    def Pie(cls, name: str, data: list[float | int], border_color: str = None, border_width: int = 1,
            border_dash: int = None, background_colors: list[str] = None) -> _Pie:
        return cls._Pie(name=name, data=data, borderColor=border_color, borderWidth=border_width,
                        borderDash=border_dash, backgroundColor=background_colors)

    @dataclass
    class PiePlot:
        """
        Args:
            title: str
            datasets: list["ChartJS.PolarAreas"]  # lines
            labels: list[str] = None  # labels for main axis(input axis)
        """
        datasets: list["ChartJS.PolarAreas"]  # lines
        labels: list[str] = None  # labels for each polar area
        title: str = None
        titleColor: str = None
        titleFontSize: int = 20
        cutoutPercentage: str = "0%"
        rotation: int = 0
        circumference: int = 360

        type: str = "pie"

    @dataclass
    class _PolarAreas:
        name: str
        data: list[float | int]
        borderColor: str
        borderWidth: int
        borderDash: int
        backgroundColor: str

    @classmethod
    def PolarAreas(cls, name: str, data: list[float | int], border_color: str = None, border_width: int = 1,
                   border_dash: int = None, background_color: str = None) -> _PolarAreas:
        return cls._PolarAreas(name=name, data=data, borderColor=border_color, borderWidth=border_width,
                               borderDash=border_dash, backgroundColor=background_color)

    @dataclass
    class PolarAreaPlot:
        """
        Args:
            title: str
            datasets: list["ChartJS.PolarAreas"]  # lines
            labels: list[str] = None  # labels for main axis(input axis)
        """
        datasets: list["ChartJS.PolarAreas"]  # lines
        labels: list[str] = None  # labels for each polar area
        title: str = None
        titleColor: str = None
        titleFontSize: int = 20

        type: str = "polarArea"

    def __init__(self):
        self.plots = []

    def add_line_plot(self, title: str, lines: list[Line], labels: list[str] = None,
                      title_color: str = None, title_font_size: int = 20,
                      x_axis_name: str = None, x_axis_color: str = None, x_axis_font_size: int = None,
                      y_axis_name: str = None, y_axis_color: str = None, y_axis_font_size: int = None):
        self.plots.append(self.LinePlot(title=title, datasets=lines, labels=labels,
                                        titleColor=title_color, titleFontSize=title_font_size,
                                        xAxisName=x_axis_name, xAxisColor=x_axis_color, xAxisFontSize=x_axis_font_size,
                                        yAxisName=y_axis_name, yAxisColor=y_axis_color, yAxisFontSize=y_axis_font_size))

    def add_pie_plot(self, title: str, areas_data: list[PolarAreas], cutout_percentage: str = "0%",
                     title_color: str = None, title_font_size: int = 20, area_names: list[str] = None):
        self.plots.append(self.PiePlot(title=title, datasets=areas_data, cutoutPercentage=cutout_percentage,
                                       titleColor=title_color, titleFontSize=title_font_size, labels=area_names))

    def add_polar_area_plot(self, title: str, areas_data: list[PolarAreas],
                            title_color: str = None, title_font_size: int = 20, area_names: list[str] = None):
        self.plots.append(self.PolarAreaPlot(title=title, datasets=areas_data,
                                             titleColor=title_color, titleFontSize=title_font_size, labels=area_names))

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
