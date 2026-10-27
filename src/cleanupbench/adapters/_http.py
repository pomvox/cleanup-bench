"""A small JSON-over-HTTP client on urllib for the network adapters.

No third-party HTTP package, no retries, no redirects followed silently into
a different host: a failed request is an `AdapterError` with a short message
that never contains a credential.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from cleanupbench.adapters.base import AdapterError

LOOPBACK_HOSTS: frozenset[str] = frozenset({"127.0.0.1", "localhost", "::1"})


@dataclass(frozen=True, slots=True)
class HttpResult:
    status: int
    body: str
    latency_ms: float

    def json(self) -> Any:
        try:
            return json.loads(self.body)
        except json.JSONDecodeError as exc:
            raise AdapterError(f"response is not valid JSON ({exc.msg} at char {exc.pos})") from exc


def is_loopback(url: str) -> bool:
    host = urllib.parse.urlsplit(url).hostname or ""
    return host.lower() in LOOPBACK_HOSTS


def _read(resp: Any) -> str:
    return resp.read().decode("utf-8", errors="replace")


def request_json(
    url: str,
    *,
    method: str = "POST",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout_s: float = 120.0,
) -> HttpResult:
    """Send one request and return the body text. Any transport or non-2xx status raises AdapterError.

    `headers` may carry a credential; it is sent and never echoed in an error.
    """
    data = None
    hdrs = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 - the URL is the operator's config
            text = _read(resp)
            status = int(resp.status)
    except urllib.error.HTTPError as exc:
        try:
            detail = _read(exc)[:200].replace("\n", " ")
        except OSError:
            detail = ""
        raise AdapterError(f"HTTP {exc.code} from {url}" + (f": {detail}" if detail else "")) from None
    except urllib.error.URLError as exc:
        raise AdapterError(f"cannot reach {url}: {exc.reason}") from None
    except (TimeoutError, OSError) as exc:
        raise AdapterError(f"transport error talking to {url}: {exc.__class__.__name__}") from None
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return HttpResult(status=status, body=text, latency_ms=latency_ms)


def today_utc() -> str:
    import datetime as dt

    return dt.datetime.now(dt.UTC).date().isoformat()
