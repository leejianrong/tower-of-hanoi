# Tower of Hanoi RL Visualizer: Plan

Status: agreed · Milestone: MVP

## Problem

The project can train a tabular Q-learning agent and replay selected solved runs, but the replay only shows discs moving on rods. It does not show why the agent chose an action, how the Q-table changed, whether the step was exploration or exploitation, or how reward and epsilon shaped learning.

The next milestone should turn training into a complete, inspectable, YouTube-ready learning visualization: every episode and decision is recorded, then rendered as a deterministic Pygame dashboard with synchronized game state, Q-values, rewards, epsilon, sounds, and animations.

## Solution

Build a post-training visualization pipeline. `make train` produces a complete training event log until the agent first reaches an optimal 31-move solution for 5 discs, or until the configured maximum episode count. `make replay` opens a single Pygame dashboard. A later export command renders the same dashboard offscreen to frames and uses `ffmpeg` to encode a video.

The dashboard should feel like a compact arcade explainer: Tower of Hanoi on the left, Q-table heatmap on the right, epsilon/explore/exploit gauge, reward coin animations, action arrows, per-episode summaries, and learning-curve context.

## Users and Actors

Primary user: Jian as a learner/builder making the agent's learning process understandable and publishable.

Secondary actors: coding agents, CI, and future viewers. When they conflict, the local deterministic training/replay path wins over visual polish because it is the source of truth for every animation.

## Scope

**In this milestone.**

- Record every episode, every step, the selected action, explore/exploit mode, reward, epsilon, and enough Q-table data to render a synchronized heatmap.
- Stop capture when the agent first solves 5-disc Tower of Hanoi in 31 moves.
- Render a single Pygame dashboard with tower replay, full state-action Q-table heatmap, epsilon decision gauge, reward animation, action animation, and episode timeline.
- Generate simple local sound effects programmatically and commit the generated assets.
- Export deterministic video through offscreen Pygame frames plus `ffmpeg`.
- Keep fast tests, lint, and compile checks green.

**Out.**

- Deep Q-learning. DQN needs a different value visualization model and would blur the first milestone.
- Live training UI. Training can be rendered after capture; this avoids coupling GUI timing to learning.
- Web UI. Pygame is already the rendering stack and is enough for the first video-capable dashboard.
- Online sound libraries or rights-unclear assets. YouTube upload requires license-clean audio.
- Docs site. Planning docs in-repo are enough for this milestone.

## Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| R0 | Show a complete Q-learning training run from first episode to first optimal solve. | Core goal |
| R1 | Persist a versioned, human-readable training event log with every episode and decision. | Must-have |
| R2 | Render tower movement, selected action, reward, epsilon, and Q-table state in one synchronized Pygame view. | Must-have |
| R3 | Highlight explore vs exploit on the epsilon gauge using the actual decision taken. | Must-have |
| R4 | Animate reward as positive/negative visual feedback, with a terminal-solve celebration. | Must-have |
| R5 | Generate deterministic local sound effects for decisions, rewards, penalties, and solve events. | Must-have |
| R6 | Export a watchable video by compressing repetitive training time while preserving the complete event log. | Must-have |
| R7 | Keep the fast local/CI gate passing. | Must-have |
| R8 | Leave DQN and web rendering as later milestones. | Scope guard |

## Shape

| Part | Mechanism | ADR |
|------|-----------|-----|
| Training telemetry | Instrument Q-learning to emit a schema-versioned JSON event log, not sparse checkpoint-only replay files. | ADR-0001 |
| Learning scope | Keep tabular Q-learning as the only supported algorithm for this milestone. | ADR-0002 |
| Dashboard renderer | Extend the Pygame renderer into a single dashboard with board, heatmap, gauges, timeline, and animation layers. | ADR-0003 |
| Video export | Render deterministic offscreen frames and encode with `ffmpeg`. | ADR-0004 |
| Sound generation | Add a repo-native Python sound generator for short WAV effects. | ADR-0005 |

## Affordances

**UI.**

| Affordance | Place | Wires to |
|------------|-------|----------|
| Tower replay | Left side of dashboard | Episode step events |
| Full Q-table heatmap | Right side of dashboard | Event log Q-table snapshot/current state |
| Current-state row spotlight | Heatmap overlay | Current observation |
| Chosen-action pulse | Heatmap cell overlay | Selected action and Q update |
| Epsilon gauge/pie | Top or lower control strip | Epsilon plus explore/exploit decision |
| Reward coins/ticks | Around board and HUD | Step reward and terminal reward |
| Episode summary card | Episode transition | Episode reward, step count, solved/truncated |
| Learning curve sparkline | Bottom strip | Episode history |
| Export pacing badge | Dashboard corner | Video timeline compressor |

**Non-UI.**

| Affordance | Kind | Wires to |
|------------|------|----------|
| Training event log | JSON artifact | Trainer, replay, exporter |
| Sound generator | Script | Committed WAV assets |
| Replay command | Make target | Pygame dashboard |
| Export command | Make target | Offscreen renderer and `ffmpeg` |
| Schema tests | Unit/integration tests | Event log reader/writer |

## Implementation Decisions

The trainer should separate action selection from telemetry. `QLearningAgent.choose_action` should return or expose decision metadata: action, mode, epsilon, valid action set, and optionally the random draw used for exploration. The environment remains responsible for state transition and reward.

New artifacts should use a versioned JSON envelope:

```json
{
  "schema_version": 1,
  "config": {"num_discs": 5, "max_steps": 150, "max_episodes": 1000},
  "episodes": []
}
```

Each episode records its start epsilon, per-step events, total reward, step count, and terminal status. Each step records state before action, action index, source/target rods, selected disc, decision mode, reward, next state, done flags, and enough Q-table values to render the selected episode. Store full Q-table snapshots at episode boundaries and selected per-step row updates rather than duplicating the entire table for every step if file size becomes awkward.

The visualizer should read artifacts, not import trainer internals. That keeps replay/export deterministic and testable. The renderer should draw from a pure view model computed from event log time, so interactive replay and video export share one path.

Sound effects should be generated in-repo with Python, NumPy, and stdlib WAV writing. Effects should be short, normalized, and named by semantic event: `explore.wav`, `exploit.wav`, `coin.wav`, `penalty.wav`, `solve.wav`, `episode_end.wav`.

## Testing Approach

Unit tests should cover the action-decision metadata, reward/termination semantics, event schema serialization, Q-table heatmap projection, and sound generation duration/sample bounds. Integration tests should run a tiny deterministic training capture, load the artifact, and render at least one headless Pygame frame. Export tests should verify command construction and skip actual video encoding when `ffmpeg` is missing.

## Assumed Defaults

| ID | Assumed | Cost if wrong |
|----|---------|---------------|
| A1 | JSON remains the training artifact format. | Moderate; can migrate behind schema version. |
| A3 | Training writes artifacts and visualizer is read-only. | Low; avoids conflict handling. |
| A5 | No charting dependency for first heatmap. | Low; Pygame drawing can be replaced later. |
| A6 | Local desktop/WSL is the runtime. | Low; CI can stay headless. |
| A8 | No secrets are involved. | Low; generated artifacts remain ignored by default. |

## Open Risks

- Full Q-table snapshots per step may make JSON too large; reveal in the telemetry slice.
- A raw full-training video may be boring even if complete; reveal in the pacing/export slice.
- Pygame text/charts may need layout refinement for 1080p/YouTube readability; reveal in the dashboard slice.
- Generated sounds may feel too synthetic; reveal in the sound slice, but the assets remain replaceable.
