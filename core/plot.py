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
    @dataclass
    class Line:
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
        borderColor: str = None
        borderWidth: int = 1
        backgroundColor: str = None
        pointRadius: int = 0
        tension: float = 0.1

    @dataclass
    class _LinePlot:
        """
        Args:
            name: str
            datasets: list["ChartJS.Line"]  # lines
            labels: list[str] = None  # labels for main axes(input axes)
        """
        name: str
        datasets: list["ChartJS.Line"]  # lines
        labels: list[str] = None  # labels for main axes(input axes)
        # x_axes_name: str = "x"
        # y_axes_name: str = "y"
        # x_axes_labels: list = None
        # y_axes_labels: list = None

        type: str = "line"

    def __init__(self):
        self.plots = []

    def add_line_plot(self, name: str, datasets: list[Line], labels: list[str] = None):
        self.plots.append(self._LinePlot(name=name, datasets=datasets, labels=labels))

    def json(self) -> str:
        return json.dumps(self.plots, cls=JSONEncoder)

    def asdict(self):
        return json.loads(self.json())


def _test():
    chart_js_plot = ChartJS()

    chart_js_plot.add_line_plot(name="test", datasets=[
        ChartJS.Line(label="line1", data=[1, 2, 3, 4, 5], borderColor="red", borderWidth=1, backgroundColor="red",
                     pointRadius=1, tension=0.5),
    ])

    print(chart_js_plot.json())


if __name__ == '__main__':
    _test()
