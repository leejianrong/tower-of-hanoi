"""Convert training telemetry to the compact replay: ``python -m src.replay [telemetry] [out]``."""

import sys
from pathlib import Path

from src.core.game import RECORD_DIR
from src.replay.compact import build_replay, load_telemetry

DEFAULT_TELEMETRY = RECORD_DIR / "qlearningagent_training.json"
DEFAULT_REPLAY = RECORD_DIR / "replay.json"


def main(argv: list[str]) -> int:
    telemetry_path = Path(argv[0]) if argv else DEFAULT_TELEMETRY
    replay_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_REPLAY
    replay = build_replay(load_telemetry(telemetry_path))
    replay.save(replay_path)
    size_kb = replay_path.stat().st_size / 1024
    print(
        f"{replay.episode_count} episodes, {replay.step_count} steps "
        f"-> {replay_path} ({size_kb:.0f} KB)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
