import asyncio
import logging

import indah

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
    board = next(n for n in nodes if n["type"] == "hanoi-board")
    assert board["props"]["rods"] == [[2, 1, 0], [], []]
    assert board["props"]["_module"]["tag"] == "indah-x-hanoi-board"
    pie = next(n for n in nodes if n["type"] == "explore-pie")
    assert pie["props"]["epsilon"] == replay.episode_epsilon[0]
    heatmap = next(n for n in nodes if n["type"] == "heatmap")
    assert len(heatmap["props"]["z"]) == 3**replay.num_discs


def test_clock_ticks_without_errors(replay, caplog):
    async def run():
        session = _session(replay)
        await asyncio.sleep(0.45)
        return session

    with caplog.at_level(logging.ERROR, logger="indah"):
        asyncio.run(run())
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]


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


def test_create_app_serves_the_page_and_both_modules(replay):
    app = create_app(replay)

    async def run():
        return [await _get(app, "/")] + [
            await _get(app, f"/api/components/{name}.js") for name in ("hanoi-board", "explore-pie")
        ]

    page, board, pie = asyncio.run(run())
    assert page[0] == 200
    for status, text in (board, pie):
        assert status == 200
        assert "export default" in text
