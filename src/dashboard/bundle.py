"""What the browser downloads once: the replay, the timeline, and the pure JavaScript core.

``/hanoi/replay.json`` is the compact replay (ADR-0008) plus the schedule (ADR-0007) in one
document, gzipped once at startup. ``/hanoi/replay-core.js`` is the browser's side of the
contract: the same state-id rules and the same timeline lookup, with no DOM in it, so it can be
tested under Node and checked against the Python rules (``tests/dashboard/test_js_contract.py``).
"""

import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from src.replay.compact import ReplayData
from src.replay.schedule import Schedule

BUNDLE_FORMAT = 1
STATIC = Path(__file__).parent / "static"
REPLAY_PATH = "/hanoi/replay.json"
CORE_PATH = "/hanoi/replay-core.js"


@dataclass(frozen=True)
class Bundle:
    raw: bytes
    gz: bytes
    etag: str


def build_bundle(replay: ReplayData, schedule: Schedule) -> Bundle:
    document = {
        "format": BUNDLE_FORMAT,
        "replay": replay.to_json(),
        "schedule": schedule.to_json(),
    }
    raw = json.dumps(document, separators=(",", ":")).encode()
    return Bundle(raw, gzip.compress(raw, 6), hashlib.sha1(raw).hexdigest()[:16])


def routes(bundle: Bundle) -> list[Route]:
    core = (STATIC / "replay-core.js").read_bytes()
    core_etag = hashlib.sha1(core).hexdigest()[:16]

    def respond(request: Request, body: bytes, media_type: str, etag: str) -> Response:
        headers = {"ETag": f'"{etag}"', "Cache-Control": "no-cache"}
        if request.headers.get("if-none-match") == headers["ETag"]:
            return Response(status_code=304, headers=headers)
        return Response(body, media_type=media_type, headers=headers)

    async def replay(request: Request) -> Response:
        if "gzip" in request.headers.get("accept-encoding", ""):
            response = respond(request, bundle.gz, "application/json", bundle.etag)
            if response.status_code == 200:
                response.headers["Content-Encoding"] = "gzip"
            response.headers["Vary"] = "Accept-Encoding"
            return response
        return respond(request, bundle.raw, "application/json", bundle.etag)

    async def core_js(request: Request) -> Response:
        return respond(request, core, "text/javascript", core_etag)

    return [Route(REPLAY_PATH, replay), Route(CORE_PATH, core_js)]
