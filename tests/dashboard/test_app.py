import asyncio
import json

import indah

from indah.components import walk

from src.dashboard.app import build_session_factory, create_app, register_components
from src.replay.schedule import build_schedule


def _walk(node):
    yield node
    for child in node["children"]:
        yield from _walk(child)


def _session(replay):
    register_components()
    return build_session_factory(replay, build_schedule(replay))(indah.Context("test"))


def test_session_builds_every_panel(replay):
    async def run():
        session = _session(replay)
        return list(_walk(session.root.to_json()))

    nodes = asyncio.run(run())
    kinds = [n["type"] for n in nodes]
    assert kinds.count("chart") == 5
    assert kinds.count("heatmap") == 1
    stage = next(n for n in nodes if n["type"] == "hanoi-stage")
    assert stage["props"]["_module"]["tag"] == "indah-x-hanoi-stage"
    assert stage["props"]["_module"]["events"] == ["tick"]


def test_a_browser_tick_moves_python_to_that_time(replay):
    async def run():
        session = _session(replay)
        stage = next(n for n in walk(session.root) if n.type == "hanoi-stage")
        schedule = build_schedule(replay)
        later = schedule.step_t0[replay.episode_start[5]] + 1e-3
        result = session.dispatch(stage.id, "tick", {"detail": {"t": later, "playing": True}})
        texts = [n.to_json()["props"].get("text") for n in walk(session.root) if n.type == "text"]
        return result, texts

    _, texts = asyncio.run(run())
    assert "Episode 6 / %d" % replay.episode_count in texts


def test_a_malformed_tick_is_ignored(replay):
    async def run():
        session = _session(replay)
        stage = next(n for n in walk(session.root) if n.type == "hanoi-stage")
        for detail in ({"t": "soon"}, {"t": True}, {}, {"t": None}, [1, 2]):
            session.dispatch(stage.id, "tick", {"detail": detail})
        return [n.to_json()["props"].get("text") for n in walk(session.root) if n.type == "text"]

    texts = asyncio.run(run())
    assert "Episode 1 / %d" % replay.episode_count in texts


async def _get(app, path):
    """One GET through the ASGI interface, so the test needs no HTTP client library."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [(b"host", b"testserver")],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    status, body = 0, b""

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        nonlocal status, body
        if message["type"] == "http.response.start":
            status = message["status"]
        elif message["type"] == "http.response.body":
            body += message.get("body", b"")

    await app(scope, receive, send)
    return status, body.decode()


def test_create_app_serves_the_page_the_module_and_the_replay(replay):
    app = create_app(replay)

    async def run():
        return [
            await _get(app, path)
            for path in (
                "/",
                "/api/components/hanoi-stage.js",
                "/hanoi/replay-core.js",
                "/hanoi/replay.json",
            )
        ]

    page, module, core, bundle = asyncio.run(run())
    assert page[0] == 200
    assert module[0] == 200 and "export default" in module[1]
    assert core[0] == 200 and "export function locate" in core[1]
    assert bundle[0] == 200
    document = json.loads(bundle[1])
    assert document["replay"]["config"]["num_discs"] == replay.num_discs
