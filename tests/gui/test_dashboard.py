import json
import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.gui.dashboard import (
    Dashboard,
    render_dashboard_animation_frame,
    render_dashboard_frame,
)
from src.gui.training_artifact import TrainingArtifact


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


def test_dashboard_animates_only_the_telemetry_move(tmp_path):
    artifact_path = tmp_path / "training.json"
    artifact_path.write_text(json.dumps({
        "schema_version": 1,
        "config": {"num_discs": 2},
        "summary": {},
        "episodes": [{
            "episode_number": 1,
            "total_reward": 100,
            "step_count": 1,
            "steps": [{
                "step_index": 0,
                "state": [[1, 0], [], []],
                "next_state": [[1], [], [0]],
                "action": 1,
                "decision_mode": "explore",
                "epsilon": 1.0,
                "source_rod_idx": 0,
                "target_rod_idx": 2,
                "disc_id": 0,
                "reward": 100,
                "q_values_before": [0, 0, 0, 0, 0, 0],
                "q_values_after": [0, 50, 0, 0, 0, 0],
            }],
            "q_table": [{"state": [[1, 0], [], []], "values": [0, 50, 0, 0, 0, 0]}],
        }],
    }))
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    artifact = TrainingArtifact.load(artifact_path)
    dashboard = Dashboard(screen, artifact)
    step = artifact.get_step()

    dashboard.start_step_animation(step, duration_seconds=1)
    assert dashboard.tower.discs[0].rect.center == (90, 445)
    assert dashboard.tower.discs[0].target_x == 450
    assert dashboard.tower.discs[1].rect.center == (90, 495)
    assert not dashboard.tower.discs[1].is_moving
    assert not dashboard.animation_complete
    assert dashboard.animation_phase == "LIFT"

    while dashboard.tower.discs[0].rect.centery > 100:
        dashboard.update_animation()
    assert dashboard.animation_phase == "CROSS"

    while dashboard.tower.discs[0].rect.centerx != 450:
        dashboard.update_animation()
    assert dashboard.animation_phase == "SET"

    for _ in range(math.ceil(1 * 60) + 3):
        dashboard.update_animation()

    assert dashboard.animation_complete
    assert dashboard.tower.discs[0].rect.center == (450, 495)
    assert dashboard.tower.discs[1].rect.center == (90, 495)
    pygame.quit()


def test_render_dashboard_animation_frame_is_deterministic(tmp_path):
    artifact_path = tmp_path / "training.json"
    output_one = tmp_path / "animation-one.png"
    output_two = tmp_path / "animation-two.png"
    artifact_path.write_text(json.dumps({
        "schema_version": 1,
        "config": {"num_discs": 1},
        "summary": {},
        "episodes": [{
            "episode_number": 1,
            "total_reward": 100,
            "step_count": 1,
            "steps": [{
                "step_index": 0,
                "state": [[0], [], []],
                "next_state": [[], [], [0]],
                "action": 1,
                "decision_mode": "explore",
                "epsilon": 1.0,
                "source_rod_idx": 0,
                "target_rod_idx": 2,
                "disc_id": 0,
                "reward": 100,
                "q_values_before": [0, 0, 0, 0, 0, 0],
                "q_values_after": [0, 50, 0, 0, 0, 0],
            }],
            "q_table": [{"state": [[0], [], []], "values": [0, 50, 0, 0, 0, 0]}],
        }],
    }))

    render_dashboard_animation_frame(artifact_path, output_one, animation_frame=1)
    render_dashboard_animation_frame(artifact_path, output_two, animation_frame=1)

    assert output_one.read_bytes() == output_two.read_bytes()
