"""Bound actual ASGI request bytes before JSON/multipart parsing, including chunked bodies."""
import json

from app.backend.core.config import settings


class BodySizeLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        maximum = (settings.MAX_AUDIO_BYTES + 65536
                   if scope["path"] == "/speech/transcribe" else settings.MAX_JSON_BYTES)

        async def reject(status, detail):
            body = json.dumps({"detail": detail}).encode()
            await send({"type": "http.response.start", "status": status,
                        "headers": [(b"content-type", b"application/json"), (b"cache-control", b"no-store")]})
            await send({"type": "http.response.body", "body": body})

        lengths = [v for k, v in scope.get("headers", []) if k.lower() == b"content-length"]
        if lengths:
            try:
                if len(lengths) != 1 or int(lengths[0]) < 0:
                    raise ValueError
                if int(lengths[0]) > maximum:
                    return await reject(413, "Request body exceeds the allowed size")
            except ValueError:
                return await reject(400, "Invalid Content-Length")
        chunks = []
        total = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            total += len(chunk)
            if total > maximum:
                return await reject(413, "Request body exceeds the allowed size")
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()
        await self.app(scope, replay, send)
