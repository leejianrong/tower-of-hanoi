import math
from pathlib import Path

import pygame

try:
    from .color import Color
    from .disc import Y_COORD_LATERAL_MOVEMENT
    from .tower import Tower
    from .training_artifact import DashboardStep, TrainingArtifact
except ImportError:
    from color import Color
    from disc import Y_COORD_LATERAL_MOVEMENT
    from tower import Tower
    from training_artifact import DashboardStep, TrainingArtifact


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BOARD_WIDTH = 720
PANEL_X = 760
PANEL_Y = 72
PANEL_WIDTH = 470
PANEL_HEIGHT = 430


class Dashboard:
    def __init__(self, screen: pygame.Surface, artifact: TrainingArtifact) -> None:
        self.screen = screen
        self.artifact = artifact
        self.background_color = Color.PASTEL_WHITE.value
        self.text_color = Color.DAVYS_GREY.value
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 18)
        self.title_font = pygame.font.SysFont(None, 32)
        self.tower = Tower(
            screen_width=BOARD_WIDTH,
            screen_height=SCREEN_HEIGHT,
            num_discs=int(artifact.data["config"]["num_discs"]),
        )
        self.current_step = artifact.get_step(episode_index=-1, step_index=0)
        self._animated_disc_id: int | None = None
        self._animation_duration_seconds = 1.0
        self._animation_elapsed_seconds = 0.0

    @property
    def animation_complete(self) -> bool:
        return self._animated_disc_id is None or not self.tower.discs[self._animated_disc_id].is_moving

    @property
    def animation_phase(self) -> str:
        if self._animated_disc_id is None:
            return "READY"
        disc = self.tower.discs[self._animated_disc_id]
        if not disc.is_moving:
            return "SET"
        if disc.rect.centerx == disc.source_x and disc.rect.centery > Y_COORD_LATERAL_MOVEMENT:
            return "LIFT"
        if disc.rect.centerx != disc.target_x:
            return "CROSS"
        return "SET"

    @property
    def animation_progress(self) -> float:
        return min(self._animation_elapsed_seconds / self._animation_duration_seconds, 1.0)

    @property
    def action_progress(self) -> float:
        """Map the disc's lift-slide-drop position onto its action-path arrow."""
        if self._animated_disc_id is None:
            return 1.0
        disc = self.tower.discs[self._animated_disc_id]
        if not disc.is_moving:
            return 1.0
        source_x, source_y = disc.source_x, disc.source_y
        target_x, target_y = disc.target_x, disc.target_y
        if disc.rect.centerx == source_x:
            lift_distance = max(source_y - Y_COORD_LATERAL_MOVEMENT, 1)
            return 0.16 * (source_y - disc.rect.centery) / lift_distance
        if disc.rect.centerx != target_x:
            cross_distance = max(abs(target_x - source_x), 1)
            return 0.16 + 0.68 * abs(disc.rect.centerx - source_x) / cross_distance
        set_distance = max(target_y - Y_COORD_LATERAL_MOVEMENT, 1)
        return 0.84 + 0.16 * (disc.rect.centery - Y_COORD_LATERAL_MOVEMENT) / set_distance

    @property
    def feedback_pulse(self) -> float:
        """A deterministic early-step pulse for Q and reward feedback."""
        return math.sin(math.pi * min(self.animation_progress / 0.45, 1.0))

    def start_step_animation(self, step: DashboardStep, duration_seconds: float) -> None:
        """Place a step at its source state and prepare its moved disc to travel."""
        self.current_step = step
        self._animation_duration_seconds = max(duration_seconds, 1 / 240)
        self._animation_elapsed_seconds = 0.0
        self.tower.set_state(step.state)
        target_x, target_y = self.tower.compute_disc_positions_from_state(step.next_state)[step.disc_id]
        disc = self.tower.discs[step.disc_id]
        disc.set_target(target_x, target_y)
        disc.speed = self._animation_speed(disc, duration_seconds)
        self._animated_disc_id = step.disc_id

    def update_animation(self, elapsed_seconds: float = 1 / 60) -> None:
        self._animation_elapsed_seconds += max(0.0, elapsed_seconds)
        if not self.animation_complete:
            self.tower.update()

    def set_animation_duration(self, duration_seconds: float) -> None:
        """Retiming an active move keeps the speed controls visually responsive."""
        self._animation_duration_seconds = max(duration_seconds, 1 / 240)
        if not self.animation_complete:
            disc = self.tower.discs[self._animated_disc_id]
            disc.speed = self._animation_speed(disc, duration_seconds)

    def _animation_speed(self, disc, duration_seconds: float) -> int:
        """Choose a per-frame speed that completes the lift-slide-drop path on time."""
        source_x, source_y = disc.rect.center
        target_x, target_y = disc.target_x, disc.target_y
        travel_distance = (
            max(source_y - Y_COORD_LATERAL_MOVEMENT, 0)
            + abs(target_x - source_x)
            + max(target_y - Y_COORD_LATERAL_MOVEMENT, 0)
        )
        frames = max(1, round(duration_seconds * 60))
        return max(1, math.ceil(travel_distance / frames))

    def render_step(
        self,
        step: DashboardStep,
        *,
        timeline_progress: tuple[int, int] | None = None,
        playing: bool | None = None,
        speed: float | None = None,
        animated: bool = False,
    ) -> None:
        self.current_step = step
        if not animated:
            self.tower.set_state(step.state)
            self._animated_disc_id = None
        self.screen.fill(self.background_color)
        self._render_header(step, timeline_progress=timeline_progress, playing=playing, speed=speed)
        self._render_board_region(step)
        if animated:
            self._render_transition_rail(step)
        self._render_heatmap(step)
        self._render_epsilon_gauge(step)
        self._render_reward_badge(step)
        self._render_episode_context(step)
        self._render_solve_celebration(step)
        pygame.display.flip()

    def _render_header(
        self,
        step: DashboardStep,
        *,
        timeline_progress: tuple[int, int] | None = None,
        playing: bool | None = None,
        speed: float | None = None,
    ) -> None:
        title = self.title_font.render("Tower of Hanoi Q-Learning", True, self.text_color)
        self.screen.blit(title, (48, 28))
        subtitle = (
            f"Episode {step.episode_number}/{step.episode_count}  "
            f"Step {step.step_number}/{step.step_count}  "
            f"Action {step.action}: {step.source_rod_idx}->{step.target_rod_idx}"
        )
        self.screen.blit(self.font.render(subtitle, True, self.text_color), (48, 58))
        if timeline_progress is not None:
            current, total = timeline_progress
            state = "PLAY" if playing else "PAUSE"
            speed_text = f"{speed:.1f} steps/s" if speed is not None else ""
            timeline = f"{state}  Timeline {current}/{total}  {speed_text}"
            self.screen.blit(self.small_font.render(timeline, True, self.text_color), (500, 84))

    def _render_transition_rail(self, step: DashboardStep) -> None:
        """Show the real lift-slide-drop phase of the active physical move."""
        phases = ("LIFT", "CROSS", "SET")
        phase_index = phases.index(self.animation_phase)
        x, y, width, gap = 48, 592, 432, 8
        segment_width = (width - gap * (len(phases) - 1)) // len(phases)
        label = self.small_font.render(f"DISC {step.disc_id} MOVE", True, self.text_color)
        self.screen.blit(label, (x, y - 22))
        for index, phase in enumerate(phases):
            segment_x = x + index * (segment_width + gap)
            color = Color.LIGHT_GRAY.value
            if index < phase_index:
                color = Color.INCHWORM.value
            elif index == phase_index:
                color = Color.PASTEL_AMBER.value
            pygame.draw.rect(self.screen, color, pygame.Rect(segment_x, y, segment_width, 8), border_radius=4)
            text_color = self.text_color if index <= phase_index else Color.PASTEL_GRAY.value
            label = self.small_font.render(phase, True, text_color)
            self.screen.blit(label, label.get_rect(center=(segment_x + segment_width // 2, y + 24)))

    def _render_board_region(self, step: DashboardStep) -> None:
        self.tower.render(self.screen)
        source_x = self.tower.rods[step.source_rod_idx].rect.centerx
        target_x = self.tower.rods[step.target_rod_idx].rect.centerx
        y = 92
        pygame.draw.line(self.screen, Color.LIGHT_GRAY.value, (source_x, y), (target_x, y), 2)
        arrow_x = round(source_x + (target_x - source_x) * self.action_progress)
        pygame.draw.line(self.screen, Color.INCHWORM.value, (source_x, y), (arrow_x, y), 4)
        direction = 1 if target_x >= source_x else -1
        arrow_tip = (arrow_x, y)
        pygame.draw.polygon(
            self.screen,
            Color.INCHWORM.value,
            [
                arrow_tip,
                (arrow_x - direction * 14, y - 8),
                (arrow_x - direction * 14, y + 8),
            ],
        )

    def _render_heatmap(self, step: DashboardStep) -> None:
        pygame.draw.rect(
            self.screen,
            pygame.Color("#ffffff"),
            pygame.Rect(PANEL_X - 16, PANEL_Y - 18, PANEL_WIDTH + 32, PANEL_HEIGHT + 62),
            border_radius=6,
        )
        label = self.title_font.render("Q-table heatmap", True, self.text_color)
        self.screen.blit(label, (PANEL_X, PANEL_Y - 50))
        q_before = step.q_values_before[step.action]
        q_after = step.q_values_after[step.action]
        q_delta = q_after - q_before
        delta_color = Color.INCHWORM.value if q_delta >= 0 else pygame.Color("#d96c6c")
        label_y = PANEL_Y - 40 - round(self.feedback_pulse * 4)
        update_label = self.small_font.render(
            f"Q(a) {q_before:.2f} → {q_after:.2f}  ({q_delta:+.2f})",
            True,
            delta_color,
        )
        self.screen.blit(update_label, (PANEL_X + 250, label_y))

        q_table = step.q_table
        if not q_table:
            return

        values = [value for _, row in q_table for value in row if math.isfinite(value)]
        max_abs = max(max(abs(value) for value in values), 1.0)
        rows = len(q_table)
        cols = len(q_table[0][1])
        cell_w = PANEL_WIDTH / cols
        cell_h = min(18, PANEL_HEIGHT / rows)
        visible_rows = min(rows, int(PANEL_HEIGHT / cell_h))
        current_state = step.state

        start_row = self._centered_start_row(q_table, current_state, visible_rows)
        visible_q_table = q_table[start_row:start_row + visible_rows]

        for row_idx, (state, row_values) in enumerate(visible_q_table):
            y = PANEL_Y + row_idx * cell_h
            is_current_state = state == current_state
            for col_idx, value in enumerate(row_values):
                x = PANEL_X + col_idx * cell_w
                rect = pygame.Rect(round(x), round(y), math.ceil(cell_w), math.ceil(cell_h))
                pygame.draw.rect(self.screen, self._heat_color(value, max_abs), rect)
                if is_current_state and col_idx == step.action:
                    pygame.draw.rect(self.screen, Color.INCHWORM.value, rect, width=3)
                    if self.feedback_pulse:
                        flash_color = Color.INCHWORM.value if q_delta >= 0 else pygame.Color("#d96c6c")
                        flash = rect.inflate(round(self.feedback_pulse * 8), round(self.feedback_pulse * 8))
                        pygame.draw.rect(self.screen, flash_color, flash, width=2)
                elif is_current_state:
                    pygame.draw.rect(self.screen, pygame.Color("#222222"), rect, width=1)

        action_labels = ["0->1", "0->2", "1->0", "1->2", "2->0", "2->1"]
        for idx, action_label in enumerate(action_labels):
            x = PANEL_X + idx * cell_w + 6
            y = PANEL_Y + visible_rows * cell_h + 8
            self.screen.blit(self.small_font.render(action_label, True, self.text_color), (x, y))

        row_text = f"showing rows {start_row + 1}-{start_row + visible_rows} of {rows}"
        self.screen.blit(
            self.small_font.render(row_text, True, self.text_color),
            (PANEL_X, PANEL_Y + visible_rows * cell_h + 30),
        )

    def _centered_start_row(self, q_table, current_state, visible_rows: int) -> int:
        current_idx = next((idx for idx, (state, _) in enumerate(q_table) if state == current_state), 0)
        return max(0, min(current_idx - visible_rows // 2, len(q_table) - visible_rows))

    def _heat_color(self, value: float, max_abs: float) -> pygame.Color:
        normalized = max(-1.0, min(1.0, value / max_abs))
        if normalized >= 0:
            base = 245 - int(normalized * 120)
            return pygame.Color(base, 225, 145)
        base = 245 - int(abs(normalized) * 100)
        return pygame.Color(245, base, base)

    def _render_epsilon_gauge(self, step: DashboardStep) -> None:
        center = (PANEL_X + 70, 650)
        radius = 42
        pygame.draw.circle(self.screen, pygame.Color("#e8e5dd"), center, radius)
        explore_angle = 2 * math.pi * step.epsilon
        points = [center]
        for idx in range(32):
            angle = -math.pi / 2 + explore_angle * idx / 31
            points.append((center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)))
        if len(points) > 2:
            pygame.draw.polygon(self.screen, Color.PASTEL_AMBER.value, points)
        ring_color = Color.INCHWORM.value if step.decision_mode == "exploit" else Color.PASTEL_AMBER.value
        pygame.draw.circle(self.screen, ring_color, center, radius, width=4)
        mode = step.decision_mode.upper()
        self.screen.blit(self.font.render(mode, True, self.text_color), (PANEL_X + 132, 630))
        self.screen.blit(
            self.small_font.render(f"epsilon {step.epsilon:.3f}", True, self.text_color),
            (PANEL_X + 132, 656),
        )

    def _render_reward_badge(self, step: DashboardStep) -> None:
        x = PANEL_X + 300
        y = 622
        color = Color.PASTEL_AMBER.value if step.reward > 0 else pygame.Color("#d96c6c")
        pulse = self.feedback_pulse
        radius = 28 + round(pulse * 6)
        center = (x, y + 28)
        pygame.draw.circle(self.screen, color, center, radius)
        pygame.draw.circle(self.screen, pygame.Color("#ffffff"), center, radius, width=2)
        if step.reward > 0:
            pygame.draw.circle(self.screen, pygame.Color("#fff0bd"), center, max(8, radius - 12), width=2)
        else:
            tick_radius = radius + 10 + round(pulse * 6)
            for angle in (-2.3, -1.57, -0.84):
                start = (
                    x + round(math.cos(angle) * tick_radius),
                    y + 28 + round(math.sin(angle) * tick_radius),
                )
                end = (
                    x + round(math.cos(angle) * (tick_radius + 7)),
                    y + 28 + round(math.sin(angle) * (tick_radius + 7)),
                )
                pygame.draw.line(self.screen, color, start, end, 3)
        reward_text = self.font.render(f"{step.reward:+.0f}", True, pygame.Color("#ffffff"))
        self.screen.blit(reward_text, reward_text.get_rect(center=center))
        total = self.small_font.render(f"episode reward {step.total_reward:.0f}", True, self.text_color)
        self.screen.blit(total, (x + 44, y + 20))

    def _render_episode_context(self, step: DashboardStep) -> None:
        x, y, width, height = 500, 570, 210, 112
        pygame.draw.rect(
            self.screen,
            pygame.Color("#ffffff"),
            pygame.Rect(x, y, width, height),
            border_radius=6,
        )
        heading = self.small_font.render(f"EPISODE {step.episode_number}", True, self.text_color)
        self.screen.blit(heading, (x + 12, y + 10))
        status = "IN PROGRESS"
        if step.terminated and step.episode_optimal:
            status = "OPTIMAL SOLVE"
        elif step.terminated and step.episode_solved:
            status = "SOLVED"
        elif step.truncated:
            status = "TRUNCATED"
        summary = self.small_font.render(
            f"{status}  ·  {step.step_count} moves  ·  {step.total_reward:.0f} reward",
            True,
            self.text_color,
        )
        self.screen.blit(summary, (x + 12, y + 30))
        self._render_learning_curve(x + 12, y + 58, width - 24, 40, step)

    def _render_learning_curve(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        step: DashboardStep,
    ) -> None:
        rewards = [float(episode["total_reward"]) for episode in self.artifact.data["episodes"]]
        history = rewards[:step.episode_number][-16:]
        if not history:
            return
        minimum, maximum = min(history), max(history)
        if minimum == maximum:
            minimum -= 1
            maximum += 1
        points = [
            (
                x + round(index * width / max(len(history) - 1, 1)),
                y + height - round((reward - minimum) * height / (maximum - minimum)),
            )
            for index, reward in enumerate(history)
        ]
        pygame.draw.line(self.screen, Color.LIGHT_GRAY.value, (x, y + height), (x + width, y + height), 1)
        if len(points) == 1:
            pygame.draw.circle(self.screen, Color.INCHWORM.value, points[0], 3)
        else:
            pygame.draw.lines(self.screen, Color.INCHWORM.value, False, points, 2)
            pygame.draw.circle(self.screen, Color.PASTEL_AMBER.value, points[-1], 4)

    def _render_solve_celebration(self, step: DashboardStep) -> None:
        if not (step.terminated and step.episode_optimal):
            return
        rect = pygame.Rect(48, 132, 360, 42)
        pygame.draw.rect(self.screen, Color.PASTEL_LIME.value, rect, border_radius=8)
        message = self.font.render("OPTIMAL SOLVE · 31 MOVES", True, self.text_color)
        self.screen.blit(message, message.get_rect(center=rect.center))
        for index in range(7):
            confetti_x = 428 + index * 28
            confetti_y = 140 + (index % 3) * 12
            pygame.draw.circle(self.screen, Color.PASTEL_AMBER.value, (confetti_x, confetti_y), 4)


def render_dashboard_frame(
    artifact_path: str | Path,
    output_path: str | Path,
    *,
    episode_index: int = -1,
    step_index: int = 0,
    size: tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT),
) -> Path:
    pygame.init()
    screen = pygame.display.set_mode(size)
    artifact = TrainingArtifact.load(artifact_path)
    dashboard = Dashboard(screen, artifact)
    dashboard.render_step(artifact.get_step(episode_index=episode_index, step_index=step_index))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(screen, output)
    pygame.quit()
    return output


def render_dashboard_animation_frame(
    artifact_path: str | Path,
    output_path: str | Path,
    *,
    episode_index: int = -1,
    step_index: int = 0,
    animation_frame: int = 0,
    steps_per_second: float = 8.0,
    size: tuple[int, int] = (SCREEN_WIDTH, SCREEN_HEIGHT),
) -> Path:
    """Render one deterministic lift-slide-drop frame for a telemetry step."""
    if animation_frame < 0:
        raise ValueError("animation_frame must be non-negative.")
    if steps_per_second <= 0:
        raise ValueError("steps_per_second must be positive.")

    pygame.init()
    screen = pygame.display.set_mode(size)
    artifact = TrainingArtifact.load(artifact_path)
    dashboard = Dashboard(screen, artifact)
    step = artifact.get_step(episode_index=episode_index, step_index=step_index)
    dashboard.start_step_animation(step, duration_seconds=1 / steps_per_second)
    for _ in range(animation_frame):
        dashboard.update_animation()
    dashboard.render_step(step, speed=steps_per_second, animated=True)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(screen, output)
    pygame.quit()
    return output
