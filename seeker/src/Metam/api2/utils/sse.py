# api2/utils/sse.py

from flask import Response
import json

def sse_stream(generator):
    """
    将一个 Python generator（每次产出一个 dict）包装成 Server‑Sent Events 流，
    并确保输出的是 bytes，不会被 Werkzeug 拒绝。
    """
    def event_stream():
        # 首次重连指令
        yield b"retry: 1000\n\n"

        for msg in generator:
            # 构造 SSE 数据行，并编码成 bytes
            chunk = f"data: {json.dumps(msg)}\n\n".encode("utf-8")
            yield chunk

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    return Response(
        event_stream(),
        headers=headers,
        direct_passthrough=True,
    )
