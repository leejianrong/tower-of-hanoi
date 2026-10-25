"""The replay dashboard as an indah app (ADR-0006).

Slice 2 of PLAN.md: the whole layout built from indah's existing components plus two small
browser modules, driven by a server-side clock that ticks at 10 Hz. A frame is still a pure
function of the clock (``Player.frame``), which is what lets the clock move into the browser
later without touching any of this. The gaps this version shows are listed in PLAN.md.
"""

from collections.abc import Callable
from pathlib import Path

import indah

from src.dashboard.player import Player
from src.dashboard.theme import THEME
from src.replay.compact import ReplayData
from src.replay.schedule import Pacing, Schedule, build_schedule

STATIC = Path(__file__).parent / "static"
TICK_S = 0.1
SPEEDS = (("1", "1x"), ("4", "4x"), ("16", "16x"), ("64", "64x"))

# Chart strokes must work on both schemes until Chart can read theme tokens (PLAN.md, gap G8).
ORANGE, TEAL, BLUE = "#f08a00", "#1fa99c", "#4d8fe0"


def register_components() -> None:
    indah.register_component("hanoi-board", module=STATIC / "hanoi-board.js", fallback="caption")
    indah.register_component("explore-pie", module=STATIC / "explore-pie.js", fallback="caption")


def build_session_factory(
    replay: ReplayData, schedule: Schedule
) -> Callable[[indah.Context], indah.Session]:
    num_discs = replay.num_discs

    def factory(ctx: indah.Context) -> indah.Session:
        player = Player(replay, schedule)
        frame = indah.Signal(player.frame())
        episode = indah.Signal(frame.value.episode)
        step = indah.Signal(frame.value.step)
        applied = indah.Signal(frame.value.applied)
        playing = indah.Signal(True)
        speed = indah.Signal("1")

        def refresh() -> None:
            current = player.frame()
            frame.set(current)
            episode.set(current.episode)
            step.set(current.step)
            applied.set(current.applied)

        def tick() -> None:
            player.playing = playing.value
            player.speed = float(speed.value)
            player.advance(TICK_S)
            refresh()

        def toggle() -> None:
            playing.set(not playing.value)

        def restart() -> None:
            player.seek(0)
            refresh()

        ctx.every(TICK_S, tick)

        board = indah.custom(
            "hanoi-board",
            caption="Board",
            discs=num_discs,
            rods=indah.computed(lambda: [list(r) for r in frame.value.rods]),
            move=indah.computed(
                lambda: {
                    "disc": frame.value.disc,
                    "source": frame.value.source,
                    "target": frame.value.target,
                }
            ),
        )
        pie = indah.custom(
            "explore-pie",
            caption="Explore or exploit",
            epsilon=indah.computed(lambda: frame.value.epsilon),
            explore=indah.computed(lambda: frame.value.explore),
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
                indah.Progress(
                    lambda: frame.value.episode_number / frame.value.episode_count,
                ),
                indah.Text(
                    lambda: f"Step {frame.value.step_in_episode} / {frame.value.max_steps}",
                    variant="mono",
                ),
                indah.Progress(lambda: frame.value.step_in_episode / frame.value.max_steps),
                indah.Button(lambda: "Pause" if playing.value else "Play", on_click=toggle),
                indah.Button("Restart", on_click=restart, variant="ghost"),
                indah.Segmented(
                    speed, options=[{"value": v, "label": label} for v, label in SPEEDS]
                ),
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
                    indah.computed(
                        lambda: player.return_in_episode(episode.value, step.value)
                    ),
                    x_label="step",
                    series=[{"label": "return", "stroke": TEAL}],
                ),
                chart(
                    "Q-value change per step",
                    indah.computed(
                        lambda: player.q_change_in_episode(episode.value, step.value)
                    ),
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

        top = indah.Row(
            align="start",
            children=[
                indah.Column(children=[indah.Card(children=[board]), indah.Card(children=[pie])]),
                charts,
            ],
        )
        return indah.Session(indah.Column(children=[header, top, heatmap]))

    return factory


def create_app(replay: ReplayData, pacing: Pacing | None = None):
    register_components()
    schedule = build_schedule(replay, pacing)
    return indah.create_app(
        session_factory=build_session_factory(replay, schedule),
        theme=THEME,
        title="Hanoi RL",
        max_width="none",
        density="compact",
        proxy_flush=False,  # no window-buffering proxy on localhost; skips ~8 KB padding per frame
    )
