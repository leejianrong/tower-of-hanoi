import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.gui.dashboard import render_dashboard_frame


def test_render_dashboard_frame_writes_nonblank_image(tmp_path):
    artifact_path = tmp_path / "training.json"
    image_path = tmp_path / "frame.png"
    artifact_path.write_text(json.dumps({
        "schema_version": 1,
        "config": {"num_discs": 5},
        "summary": {},
        "episodes": [{
            "episode_number": 1,
            "total_reward": 100,
            "step_count": 1,
            "steps": [{
                "step_index": 0,
                "state": [[4, 3, 2, 1, 0], [], []],
                "next_state": [[4, 3, 2, 1], [], [0]],
                "action": 1,
                "decision_mode": "explore",
                "epsilon": 1.0,
                "source_rod_idx": 0,
                "target_rod_idx": 2,
                "disc_id": 0,
                "reward": -1,
                "q_values_before": [0, 0, 0, 0, 0, 0],
                "q_values_after": [0, -0.5, 0, 0, 0, 0],
            }],
            "q_table": [
                {"state": [[4, 3, 2, 1, 0], [], []], "values": [0, -0.5, 0, 0, 0, 0]},
                {"state": [[4, 3, 2, 1], [], [0]], "values": [0, 0, 0, 0, 0, 0]},
            ],
        }],
    }))

    output_path = render_dashboard_frame(artifact_path, image_path)

    assert output_path == image_path
    assert image_path.exists()

    surface = pygame.image.load(image_path)
    pixels = pygame.surfarray.array3d(surface)
    assert pixels.var() > 0
