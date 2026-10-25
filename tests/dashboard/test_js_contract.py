"""The browser's replay-core.js must agree with the Python rules (ADR-0008, ADR-0007)."""

import json
import shutil
import subprocess

import pytest

from src.dashboard.bundle import STATIC, build_bundle
from src.replay.encoding import decode_state, num_states
from src.replay.schedule import build_schedule

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")

PROBE = """
import { readFileSync } from "node:fs";
import { decodeState, episodeOfStep, locate } from "%(core)s";
const input = JSON.parse(readFileSync(process.argv[2], "utf8"));
const { replay, schedule } = JSON.parse(readFileSync(input.bundle, "utf8"));
const out = {
  decoded: input.state_ids.map((id) => decodeState(id, replay.config.num_discs)),
  located: input.times.map((t) => locate(schedule, t)),
  episodes: input.steps.map((s) => episodeOfStep(replay, s)),
};
process.stdout.write(JSON.stringify(out));
"""


def test_javascript_agrees_with_python(tmp_path, replay):
    schedule = build_schedule(replay)
    bundle = tmp_path / "bundle.json"
    bundle.write_bytes(build_bundle(replay, schedule).raw)
    times = [-1.0, 0.0, 0.31, 2.5, schedule.total_s / 3, schedule.total_s / 2, schedule.total_s - 1e-3]
    times += [schedule.step_t0[i] for i in (1, 40, replay.step_count - 1)]
    times += [schedule.total_s, schedule.total_s + 5]
    steps = [0, 1, replay.step_count // 2, replay.step_count - 1]
    state_ids = list(range(num_states(replay.num_discs)))
    probe = tmp_path / "probe.mjs"
    probe.write_text(PROBE % {"core": (STATIC / "replay-core.js").as_uri()})
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps({"bundle": str(bundle), "state_ids": state_ids, "times": times, "steps": steps})
    )

    result = subprocess.run(
        ["node", str(probe), str(request)], capture_output=True, text=True, check=True
    )
    js = json.loads(result.stdout)

    assert [tuple(map(tuple, rods)) for rods in js["decoded"]] == [
        decode_state(i, replay.num_discs) for i in state_ids
    ]
    for t, got in zip(times, js["located"]):
        want = schedule.locate(t)
        assert got["step"] == want.step, t
        assert got["phase"] == pytest.approx(want.phase, abs=1e-9), t
        assert got["done"] == want.done, t
    assert js["episodes"] == [replay.episode_of_step(s) for s in steps]


def test_bundle_carries_what_the_browser_needs(replay):
    bundle = build_bundle(replay, build_schedule(replay))
    document = json.loads(bundle.raw)
    assert document["format"] == 1
    assert document["replay"]["config"]["action_map"] == [
        [0, 1], [0, 2], [1, 0], [1, 2], [2, 0], [2, 1],
    ]
    assert len(document["replay"]["steps"]["disc"]) == replay.step_count
    assert len(document["schedule"]["step_t0"]) == replay.step_count
    assert len(bundle.gz) < len(bundle.raw)
