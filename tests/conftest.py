import json

import pytest

from src.replay.compact import build_replay
from train import train


@pytest.fixture(scope="session")
def telemetry(tmp_path_factory):
    """A real (small) training run: 3 discs, so the whole state space is 27 states."""
    path = train(
        tmp_path_factory.mktemp("run") / "training.json",
        num_discs=3,
        max_steps=40,
        max_episodes=300,
        seed=7,
        log_every=1000,
    )
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def replay(telemetry):
    return build_replay(telemetry)
