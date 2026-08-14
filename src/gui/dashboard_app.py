from pathlib import Path

import pygame

try:
    from .dashboard import Dashboard, SCREEN_HEIGHT, SCREEN_WIDTH
    from .replay_controller import TrainingReplayController
    from .training_artifact import TrainingArtifact
except ImportError:
    from dashboard import Dashboard, SCREEN_HEIGHT, SCREEN_WIDTH
    from replay_controller import TrainingReplayController
    from training_artifact import TrainingArtifact


def main() -> None:
    artifact_path = Path("records") / "qlearningagent_training.json"
    artifact = TrainingArtifact.load(artifact_path)

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tower of Hanoi RL Visualizer")
    dashboard = Dashboard(screen, artifact)
    controller = TrainingReplayController(artifact)
    clock = pygame.time.Clock()

    running = True
    while running:
        elapsed_seconds = clock.tick(60) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_SPACE:
                    controller.toggle_playing()
                elif event.key == pygame.K_RIGHT:
                    controller.next_step()
                elif event.key == pygame.K_LEFT:
                    controller.previous_step()
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    controller.speed_up()
                elif event.key == pygame.K_MINUS:
                    controller.slow_down()
                elif event.key == pygame.K_PAGEUP:
                    controller.jump_episode(1)
                elif event.key == pygame.K_PAGEDOWN:
                    controller.jump_episode(-1)

        controller.update(elapsed_seconds)
        dashboard.render_step(
            controller.current_step,
            timeline_progress=controller.progress,
            playing=controller.playing,
            speed=controller.steps_per_second,
        )

    pygame.quit()


if __name__ == "__main__":
    main()
