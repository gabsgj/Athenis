# utils/sse.py
import json
from typing import Generator, Union

def sse_event(data: Union[str, dict], event: str = "message", event_id: str = None) -> str:
    """
    Format a single Server-Sent Event (SSE) message.
    """
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    lines = []
    if event_id:
        lines.append(f"id: {event_id}")
    if event:
        lines.append(f"event: {event}")
    for line in str(payload).splitlines():
        lines.append(f"data: {line}")
    return "\n".join(lines) + "\n\n"

def sse_from_text_stream(gen: Generator[str, None, None], event: str = "chunk") -> Generator[str, None, None]:
    """
    Wrap a generator[str] of text chunks into SSE frames.
    """
    for chunk in gen:
        yield sse_event(chunk, event=event)
    yield sse_event("", event="done")
