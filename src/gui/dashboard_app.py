from pathlib import Path

import pygame

try:
    from .dashboard import Dashboard, SCREEN_HEIGHT, SCREEN_WIDTH
    from .training_artifact import TrainingArtifact
except ImportError:
    from dashboard import Dashboard, SCREEN_HEIGHT, SCREEN_WIDTH
    from training_artifact import TrainingArtifact


def main() -> None:
    artifact_path = Path("records") / "qlearningagent_training.json"
    artifact = TrainingArtifact.load(artifact_path)

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tower of Hanoi RL Visualizer")
    dashboard = Dashboard(screen, artifact)
    step = artifact.get_step(episode_index=-1, step_index=0)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        dashboard.render_step(step)

    pygame.quit()


if __name__ == "__main__":
    main()
