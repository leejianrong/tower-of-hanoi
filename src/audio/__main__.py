"""Regenerate the sound effects: ``python -m src.audio`` (writes src/dashboard/static/audio/)."""

from src.audio.synth import write_all

if __name__ == "__main__":
    for path in write_all():
        print(path)
