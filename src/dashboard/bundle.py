"""What the browser downloads once: the replay, the timeline, and the pure JavaScript core.

``/hanoi/replay.json`` is the compact replay (ADR-0008) plus the schedule (ADR-0007) in one
document, gzipped once at startup. ``/hanoi/cues.json`` and ``/hanoi/audio/<name>.wav`` carry the
sound cues and the sound effects (ADR-0010); the browser fetches them only when sound is on. ``/hanoi/replay-core.js`` is the browser's side of the
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

from src.audio.cues import Cues
from src.replay.compact import ReplayData
from src.replay.schedule import Schedule

BUNDLE_FORMAT = 1
STATIC = Path(__file__).parent / "static"
REPLAY_PATH = "/hanoi/replay.json"
CORE_PATH = "/hanoi/replay-core.js"
CUES_PATH = "/hanoi/cues.json"
AUDIO_DIR = STATIC / "audio"


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


def build_cues_bundle(cues: Cues) -> Bundle:
    raw = json.dumps(cues.to_json(), separators=(",", ":")).encode()
    return Bundle(raw, gzip.compress(raw, 6), hashlib.sha1(raw).hexdigest()[:16])


def routes(bundle: Bundle, cues: Bundle | None = None) -> list[Route]:
    core = (STATIC / "replay-core.js").read_bytes()
    core_etag = hashlib.sha1(core).hexdigest()[:16]

    def respond(request: Request, body: bytes, media_type: str, etag: str) -> Response:
        headers = {"ETag": f'"{etag}"', "Cache-Control": "no-cache"}
        if request.headers.get("if-none-match") == headers["ETag"]:
            return Response(status_code=304, headers=headers)
        return Response(body, media_type=media_type, headers=headers)

    def json_route(document: Bundle):
        async def handler(request: Request) -> Response:
            if "gzip" in request.headers.get("accept-encoding", ""):
                response = respond(request, document.gz, "application/json", document.etag)
                if response.status_code == 200:
                    response.headers["Content-Encoding"] = "gzip"
                response.headers["Vary"] = "Accept-Encoding"
                return response
            return respond(request, document.raw, "application/json", document.etag)

        return handler

    sounds = {path.stem: path.read_bytes() for path in sorted(AUDIO_DIR.glob("*.wav"))}

    async def sound(request: Request) -> Response:
        name = request.path_params["name"]
        body = sounds.get(name)
        if body is None:
            return Response(status_code=404)
        return respond(request, body, "audio/wav", hashlib.sha1(body).hexdigest()[:16])

    async def core_js(request: Request) -> Response:
        return respond(request, core, "text/javascript", core_etag)

    found = [
        Route(REPLAY_PATH, json_route(bundle)),
        Route(CORE_PATH, core_js),
        Route("/hanoi/audio/{name:str}.wav", sound),
    ]
    if cues is not None:
        found.append(Route(CUES_PATH, json_route(cues)))
    return found
