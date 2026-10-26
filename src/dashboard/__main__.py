"""Run the dashboard: ``python -m src.dashboard [replay.json] [--kiosk]``.

``--kiosk`` covers the whole window (hiding indah's header), for screen recording.
"""

import sys
from pathlib import Path

import indah

from src.core.game import RECORD_DIR
from src.dashboard.app import create_app
from src.replay.compact import ReplayData


def main(argv: list[str]) -> int:
    kiosk = "--kiosk" in argv
    paths = [a for a in argv if not a.startswith("--")]
    path = Path(paths[0]) if paths else RECORD_DIR / "replay.json"
    indah.launch(create_app(ReplayData.load(path), kiosk=kiosk))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
