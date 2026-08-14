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
    dashboard.start_step_animation(controller.current_step, controller.step_duration_seconds)
    active_timeline_index = controller.current_index
    active_animation_duration = controller.step_duration_seconds
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

        if active_timeline_index != controller.current_index:
            dashboard.start_step_animation(controller.current_step, controller.step_duration_seconds)
            active_timeline_index = controller.current_index
            active_animation_duration = controller.step_duration_seconds
        elif active_animation_duration != controller.step_duration_seconds:
            dashboard.set_animation_duration(controller.step_duration_seconds)
            active_animation_duration = controller.step_duration_seconds

        if controller.playing:
            dashboard.update_animation()
        controller.update(elapsed_seconds, animation_complete=dashboard.animation_complete)

        if active_timeline_index != controller.current_index:
            dashboard.start_step_animation(controller.current_step, controller.step_duration_seconds)
            active_timeline_index = controller.current_index
            active_animation_duration = controller.step_duration_seconds

        dashboard.render_step(
            controller.current_step,
            timeline_progress=controller.progress,
            playing=controller.playing,
            speed=controller.steps_per_second,
            animated=True,
        )

    pygame.quit()


if __name__ == "__main__":
    main()
