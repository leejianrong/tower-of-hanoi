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


def register_components() -> None:
    indah.register_component(
        "hanoi-stage", module=STATIC / "hanoi-stage.js", events=["tick"], fallback="caption"
    )


def build_session_factory(
    replay: ReplayData, schedule: Schedule, *, kiosk: bool = False
) -> Callable[[indah.Context], indah.Session]:
    def factory(ctx: indah.Context) -> indah.Session:
        player = Player(replay, schedule)
        frame = indah.Signal(player.frame())
        episode = indah.Signal(frame.value.episode)
        step = indah.Signal(frame.value.step)
        applied = indah.Signal(frame.value.applied)
        applied_t = indah.Signal(None)  # last playhead applied; the video exporter waits on it

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
            applied_t.set(round(float(t), 3))  # last: everything above has been patched by then

        stage = indah.custom(
            "hanoi-stage", caption="Board and playback", applied_t=applied_t, on_tick=on_tick
        )

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

        episode_number = indah.computed(lambda: episode.value + 1)
        step_number = indah.computed(lambda: frame.value.step_in_episode)
        episodes = replay.episode_count
        run = {"x_range": (1, episodes), "playhead": episode_number, "shade_after": True}

        def chart(title, **options):
            legend = "labels" if len(options["series"]) > 1 else "off"
            return indah.Card(
                padding="12px 16px",
                children=[indah.Chart(title=title, height="fill", legend=legend, **options)],
            )

        charts = indah.Grid(
            columns=2,
            rows="1fr 1fr 1fr",
            gap="16px",
            children=[
                chart(
                    "Reward per episode",
                    data=indah.computed(lambda: player.reward_points(episode.value)),
                    series=[
                        {"label": "solved", "kind": "scatter", "stroke": "var(--x-pos)", "size": 4},
                        {"label": "ran out of moves", "kind": "scatter", "stroke": "var(--x-dot)", "size": 4},
                        {"label": "average", "stroke": "var(--x-gold)", "width": 2.5},
                    ],
                    y_range=(-180, 110),
                    **run,
                ),
                chart(
                    "Steps per episode",
                    data=indah.computed(lambda: player.step_points(episode.value)),
                    series=[
                        {"label": "solved", "kind": "scatter", "stroke": "var(--x-pos)", "size": 4},
                        {"label": "ran out of moves", "kind": "scatter", "stroke": "var(--x-dot)", "size": 4},
                    ],
                    y_range=(0, 160),
                    rules=[{"y": 31, "label": "optimal 31", "color": "var(--x-gold)"}],
                    **run,
                ),
                indah.Cell(
                    columns=2,
                    children=[
                        chart(
                            "Epsilon at the start of each episode",
                            data=player.epsilon_by_episode(),
                            series=[{"label": "epsilon", "kind": "bars", "stroke": "var(--x-explore)"}],
                            y_range=(0, 1),
                            highlight=episode_number,
                            highlight_color="var(--x-gold)",
                            **{**run, "x_range": (0.5, episodes + 0.5)},
                        )
                    ],
                ),
                chart(
                    "Reward this episode",
                    data=indah.computed(
                        lambda: player.return_vs_best(episode.value, step.value)
                    ),
                    series=[
                        {"label": "this episode", "stroke": "var(--x-exploit)", "width": 2.5},
                        {"label": "best so far", "stroke": "var(--muted)", "dash": [5, 4]},
                    ],
                    x_label="step",
                ),
                chart(
                    "Q-value change per step",
                    data=indah.computed(lambda: player.q_change_bars(episode.value, step.value)),
                    series=[
                        {"label": "explore", "kind": "bars", "stroke": "var(--x-explore)"},
                        {"label": "exploit", "kind": "bars", "stroke": "var(--x-exploit)"},
                    ],
                    x_label="step",
                    highlight=step_number,
                    highlight_color="var(--x-gold)",
                ),
            ],
        )

        heatmap = indah.Card(
            padding="12px 16px",
            children=[
                indah.Heatmap(
                    indah.computed(lambda: player.heatmap_columns(applied.value)),
                    colormap=["var(--x-heat-neg)", "var(--x-heat-zero)", "var(--x-heat-pos)"],
                    zmin=-1.3,
                    zmax=1.3,
                    null_color="var(--surface-2)",
                    origin="top",
                    row_labels=["0>1", "0>2", "1>0", "1>2", "2>0", "2>1"],
                    col_groups=[
                        {"start": r * 81, "end": r * 81 + 80, "label": f"largest disc on rod {r}"}
                        for r in range(3)
                    ],
                    mark_x=indah.computed(lambda: frame.value.state_id),
                    mark_y=indah.computed(lambda: frame.value.action),
                    mark_color="var(--x-gold)",
                    height="fill",
                    title="Q-table: 243 states by 6 actions (blank = illegal move)",
                )
            ],
        )

        middle = indah.Grid(
            columns="760px 1fr",
            gap="16px",
            children=[indah.Card(padding="16px 20px", children=[stage]), charts],
        )
        return indah.Session(
            indah.Frame(
                width=1920,
                height=1080,
                columns="1fr",
                rows="56px 1fr 196px",
                gap="16px",
                padding="20px",
                kiosk=kiosk,
                children=[header, middle, heatmap],
            )
        )

    return factory


def create_app(replay: ReplayData, pacing: Pacing | None = None, *, kiosk: bool = False):
    register_components()
    schedule = build_schedule(replay, pacing)
    app = indah.create_app(
        session_factory=build_session_factory(replay, schedule, kiosk=kiosk),
        theme=THEME,
        title="Hanoi RL",
        max_width="none",
        density="compact",
        proxy_flush=False,  # no window-buffering proxy on localhost; skips ~8 KB padding per frame
    )
    app.router.routes[0:0] = routes(build_bundle(replay, schedule))
    return app
