"""Run the dashboard: ``python -m src.dashboard [replay.json]``."""

import sys
from pathlib import Path

import indah

from src.core.game import RECORD_DIR
from src.dashboard.app import create_app
from src.replay.compact import ReplayData


def main(argv: list[str]) -> int:
    path = Path(argv[0]) if argv else RECORD_DIR / "replay.json"
    indah.launch(create_app(ReplayData.load(path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
