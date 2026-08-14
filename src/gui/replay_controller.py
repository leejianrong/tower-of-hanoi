from dataclasses import dataclass

from src.gui.training_artifact import DashboardStep, TrainingArtifact


@dataclass(frozen=True)
class TimelineItem:
    episode_index: int
    step_index: int
    step: DashboardStep


class TrainingReplayController:
    def __init__(
        self,
        artifact: TrainingArtifact,
        *,
        steps_per_second: float = 8.0,
        playing: bool = True,
    ) -> None:
        self.timeline = [
            TimelineItem(episode_index, step_index, step)
            for episode_index, step_index, step in artifact.iter_steps()
        ]
        if not self.timeline:
            raise ValueError("Training replay requires at least one telemetry step.")
        self.current_index = 0
        self.steps_per_second = steps_per_second
        self.playing = playing
        self._animation_elapsed_seconds = 0.0

    @property
    def current_step(self) -> DashboardStep:
        return self.timeline[self.current_index].step

    @property
    def progress(self) -> tuple[int, int]:
        return self.current_index + 1, len(self.timeline)

    @property
    def at_end(self) -> bool:
        return self.current_index == len(self.timeline) - 1

    @property
    def step_duration_seconds(self) -> float:
        return 1.0 / self.steps_per_second

    @property
    def animation_progress(self) -> float:
        """Return the elapsed fraction of the current step's display time."""
        return min(self._animation_elapsed_seconds / self.step_duration_seconds, 1.0)

    def toggle_playing(self) -> None:
        self.playing = not self.playing

    def set_speed(self, steps_per_second: float) -> None:
        self.steps_per_second = max(0.25, min(steps_per_second, 240.0))

    def speed_up(self) -> None:
        self.set_speed(self.steps_per_second * 2)

    def slow_down(self) -> None:
        self.set_speed(self.steps_per_second / 2)

    def next_step(self) -> None:
        self.current_index = min(self.current_index + 1, len(self.timeline) - 1)
        self._animation_elapsed_seconds = 0.0

    def previous_step(self) -> None:
        self.current_index = max(self.current_index - 1, 0)
        self._animation_elapsed_seconds = 0.0

    def jump_episode(self, delta: int) -> None:
        current_episode = self.timeline[self.current_index].episode_index
        target_episode = max(0, current_episode + delta)
        if delta >= 0:
            for idx, item in enumerate(self.timeline):
                if item.episode_index >= target_episode:
                    self.current_index = idx
                    break
        else:
            for idx in range(self.current_index, -1, -1):
                if self.timeline[idx].episode_index <= target_episode:
                    self.current_index = idx
            # The reverse scan leaves us at the first step of the target episode.
        self._animation_elapsed_seconds = 0.0

    def update(self, elapsed_seconds: float, *, animation_complete: bool = True) -> None:
        """Advance after the current step's display time and animation complete.

        ``animation_complete`` lets the Pygame view keep the telemetry timeline
        aligned with the moving disc.  The default retains a useful timer-only
        controller for headless callers.
        """
        if not self.playing or self.at_end:
            return
        self._animation_elapsed_seconds += max(0.0, elapsed_seconds)
        if (
            self._animation_elapsed_seconds >= self.step_duration_seconds
            and animation_complete
        ):
            self.current_index += 1
            self._animation_elapsed_seconds = 0.0
