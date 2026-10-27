"""Shared fixtures: an in-process fake HTTP server and an item factory for the adapter tests."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from cleanupbench.canary import CANARY
from cleanupbench.items import Item


@dataclass
class Recorded:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes

    @property
    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8")) if self.body else None


Responder = Callable[[Recorded], tuple[int, Any]]


@dataclass
class FakeServer:
    """`responder(request) -> (status, body)`; a dict body is sent as JSON, bytes or str as-is."""

    base_url: str = ""
    requests: list[Recorded] = field(default_factory=list)
    responder: Responder | None = None
    _server: ThreadingHTTPServer | None = None
    _thread: threading.Thread | None = None

    def start(self) -> None:
        state = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:  # noqa: D401 - quiet
                pass

            def _handle(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                rec = Recorded(self.command, self.path, {k.lower(): v for k, v in self.headers.items()}, body)
                state.requests.append(rec)
                if state.responder is None:
                    status, payload = 500, {"error": "no responder"}
                else:
                    status, payload = state.responder(rec)
                if isinstance(payload, bytes):
                    data, ctype = payload, "application/octet-stream"
                elif isinstance(payload, str):
                    data, ctype = payload.encode("utf-8"), "text/plain; charset=utf-8"
                else:
                    data, ctype = json.dumps(payload).encode("utf-8"), "application/json"
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = _handle
            do_POST = _handle

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base_url = f"http://127.0.0.1:{self._server.server_port}"
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        if self._thread:
            self._thread.join(timeout=5)

    @property
    def last(self) -> Recorded:
        return self.requests[-1]


@pytest.fixture
def fake_server() -> Iterator[FakeServer]:
    server = FakeServer()
    server.start()
    try:
        yield server
    finally:
        server.stop()


def item_json(
    id_: str,
    category: str,
    input_: str,
    refs: list[str],
    *,
    must: tuple[str, ...] = (),
    must_not: tuple[str, ...] = (),
    slice_: str | None = None,
    vocabulary: tuple[str, ...] = (),
    **extra: Any,
) -> dict[str, Any]:
    obj: dict[str, Any] = {"id": id_, "category": category}
    if slice_:
        obj["slice"] = slice_
    obj.update(
        {
            "input": input_,
            "input_form": "lowercase-unpunctuated",
            "vocabulary": list(vocabulary),
            "references": list(refs),
            "slots": {"must_contain": list(must), "must_not_contain": list(must_not)},
            "source": {
                "type": "synthetic",
                "method": "hand-written",
                "origin": "test",
                "license": "CC-BY-4.0",
                "attribution": "",
            },
            "notes": "test item",
            "taxonomy": [],
            "released": "2026-10-27",
            "status": "active",
            "scored": True,
        }
    )
    obj.update(extra)
    return obj


def make_item(id_: str = "fillers-core-0001", input_: str = "um so let's go", vocabulary: tuple[str, ...] = ()) -> Item:
    return Item.from_json(item_json(id_, id_.split("-")[0], input_, ["Let's go."], vocabulary=vocabulary))


def write_items_dir(root: Path, files: dict[str, list[dict[str, Any]]]) -> Path:
    d = root / "items"
    d.mkdir(exist_ok=True)
    for name, objs in files.items():
        (d / name).write_text("# " + CANARY + "\n" + "\n".join(json.dumps(o) for o in objs) + "\n", "utf-8")
    return d
