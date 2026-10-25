"""The replay dashboard as an indah app (ADR-0006, ADR-0007).

Slice 3 of PLAN.md. The clock lives in the browser: the ``hanoi-stage`` module downloads the
replay once, animates the board and the pie at the display's frame rate, and reports the playhead
to Python a few times a second (the ``tick`` event). Python follows: each tick moves the ``Player``
to that time and the charts, the Q-table and the progress readouts update from it.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import indah

from src.dashboard.bundle import build_bundle, routes
from src.dashboard.player import Player
from src.dashboard.theme import THEME
from src.replay.compact import ReplayData
from src.replay.schedule import Pacing, Schedule, build_schedule

STATIC = Path(__file__).parent / "static"

# Chart strokes must work on both schemes until Chart can read theme tokens (PLAN.md, gap G5).
ORANGE, TEAL, BLUE = "#f08a00", "#1fa99c", "#4d8fe0"


def register_components() -> None:
    indah.register_component(
        "hanoi-stage", module=STATIC / "hanoi-stage.js", events=["tick"], fallback="caption"
    )


def build_session_factory(
    replay: ReplayData, schedule: Schedule
) -> Callable[[indah.Context], indah.Session]:
    def factory(ctx: indah.Context) -> indah.Session:
        player = Player(replay, schedule)
        frame = indah.Signal(player.frame())
        episode = indah.Signal(frame.value.episode)
        step = indah.Signal(frame.value.step)
        applied = indah.Signal(frame.value.applied)

        def on_tick(detail: Any) -> None:
            """The browser's clock, in seconds. Ignore anything that is not a number."""
            t = detail.get("t") if isinstance(detail, dict) else None
            if isinstance(t, bool) or not isinstance(t, (int, float)):
                return
            player.seek(float(t))
            current = player.frame()
            frame.set(current)
            episode.set(current.episode)
            step.set(current.step)
            applied.set(current.applied)

        stage = indah.custom("hanoi-stage", caption="Board and playback", on_tick=on_tick)

        header = indah.Row(
            align="center",
            children=[
                indah.Text("Tower of Hanoi · Q-learning", variant="title"),
                indah.Spacer(),
                indah.Text(
                    lambda: f"Episode {frame.value.episode_number} / {frame.value.episode_count}",
                    variant="mono",
                ),
                indah.Progress(lambda: frame.value.episode_number / frame.value.episode_count),
                indah.Text(
                    lambda: f"Step {frame.value.step_in_episode} / {frame.value.max_steps}",
                    variant="mono",
                ),
                indah.Progress(lambda: frame.value.step_in_episode / frame.value.max_steps),
            ],
        )

        def chart(title, data, *, x_label, series, points=False, height=170):
            return indah.Card(
                children=[
                    indah.Chart(
                        data,
                        series=series,
                        title=title,
                        x_label=x_label,
                        height=height,
                        points=points,
                    )
                ]
            )

        charts = indah.Grid(
            columns=2,
            children=[
                chart(
                    "Reward per episode",
                    indah.computed(lambda: player.reward_by_episode(episode.value)),
                    x_label="episode",
                    series=[{"label": "reward", "stroke": ORANGE}],
                    points=True,
                ),
                chart(
                    "Steps per episode",
                    indah.computed(lambda: player.steps_by_episode(episode.value)),
                    x_label="episode",
                    series=[{"label": "steps", "stroke": BLUE}],
                    points=True,
                ),
                chart(
                    "Epsilon at the start of each episode",
                    player.epsilon_by_episode(),
                    x_label="episode",
                    series=[{"label": "epsilon", "stroke": ORANGE}],
                ),
                chart(
                    "Reward this episode",
                    indah.computed(lambda: player.return_in_episode(episode.value, step.value)),
                    x_label="step",
                    series=[{"label": "return", "stroke": TEAL}],
                ),
                chart(
                    "Q-value change per step",
                    indah.computed(lambda: player.q_change_in_episode(episode.value, step.value)),
                    x_label="step",
                    series=[{"label": "|change|", "stroke": ORANGE}],
                    points=True,
                ),
            ],
        )

        heatmap = indah.Card(
            children=[
                indah.Heatmap(
                    indah.computed(lambda: player.heatmap_columns(applied.value)),
                    colormap="viridis",
                    zmin=-1.3,
                    zmax=0.3,
                    height=140,
                    title="Q-table: 243 states by 6 actions (dark gap = illegal move)",
                    x_label="state",
                    y_label="action",
                )
            ]
        )

        top = indah.Row(align="start", children=[indah.Card(children=[stage]), charts])
        return indah.Session(indah.Column(children=[header, top, heatmap]))

    return factory


def create_app(replay: ReplayData, pacing: Pacing | None = None):
    register_components()
    schedule = build_schedule(replay, pacing)
    app = indah.create_app(
        session_factory=build_session_factory(replay, schedule),
        theme=THEME,
        title="Hanoi RL",
        max_width="none",
        density="compact",
        proxy_flush=False,  # no window-buffering proxy on localhost; skips ~8 KB padding per frame
    )
    app.router.routes[0:0] = routes(build_bundle(replay, schedule))
    return app
