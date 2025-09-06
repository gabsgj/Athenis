def sse_format(event: str, data):
    if not isinstance(data, str):
        import json
        data = json.dumps(data)
    return f"event: {event}\ndata: {data}\n\n"
