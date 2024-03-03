def parse_traffic_to_gb(traffic):
    return f"{traffic / 1024 / 1024 / 1024}GB"


def parse_traffic_to_mb(traffic):
    return f"{traffic / 1024 / 1024}MB"


def parse_traffic_to_kb(traffic):
    return f"{traffic / 1024}KB"
