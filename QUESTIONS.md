# Questions

This register captures the planning decisions for the reinforcement-learning visualization milestone.

## Forks

### F1. First visualization target

- Status: ANSWERED
- Recommendation: Build a post-training replay explorer first, not a live training dashboard.
- Reasoning: The current code already records replay JSON, and live training couples RL timing to GUI timing too early. A post-training artifact can show learning progress across checkpoints while staying deterministic.
- User decision: Accepted. The visualization should be recorded from training telemetry and played back/exported rather than driven by a live training loop.
- Changes if different: A live dashboard needs a training loop that yields control to the renderer, explicit pause/step controls, and more care around long-running UI state.
- Lands in: `PLAN.md`, `SLICES.md`, ADR.

### F2. Agent scope for this milestone

- Status: ANSWERED
- Recommendation: Make tabular Q-learning the milestone, with DQN explicitly out of scope until the visualization data contract is stable.
- Reasoning: A Q-table is inspectable and maps directly to heatmaps; DQN visualization needs a different artifact, likely model-value probes rather than a literal table.
- User decision: Accepted.
- Changes if different: Supporting DQN now changes the storage format, UI vocabulary, tests, and the meaning of the heatmap.
- Lands in: `PLAN.md`, `SLICES.md`, ADR.

### F3. Heatmap shape

- Status: ANSWERED
- Recommendation: Use a dense state-action heatmap for all reachable states in the selected checkpoint, plus highlight the current replay state row and selected action.
- Reasoning: For 5 discs, the state space is small enough to render as 243 possible states by 6 actions, and a full heatmap shows global learning better than a tiny current-state-only panel.
- User decision: Accepted.
- Changes if different: A current-state-only heatmap is simpler and cleaner but hides learning progress; a full all-episode heatmap becomes a data-volume and interaction problem.
- Lands in: `PLAN.md`, `SLICES.md`, ADR.

### F4. Timeline granularity

- Status: ANSWERED
- Recommendation: Save visualization snapshots every 50 episodes and replay checkpoints every 200 episodes.
- Reasoning: Current checkpoints are every 200 episodes. For learning visualization, 200 is too coarse for the epsilon/reward curve, but per-episode full artifacts are unnecessary for 1000 episodes.
- User decision: Override. Record every episode, every explore/exploit decision, and each resulting reward. Stop training capture once the agent solves in the optimal 31 moves.
- Changes: The artifact format must become an event log, not checkpoint files. The replay/export renderer needs pacing/compression rules so hundreds of episodes can become a watchable video.
- Lands in: `PLAN.md`, `SLICES.md`.

### F5. UI density and visual tone

- Status: ANSWERED
- Recommendation: A single Pygame dashboard: tower on the left, q-table heatmap on the right, compact top/bottom strips for episode, reward, epsilon, exploration/exploitation, and controls.
- Reasoning: The current 1280x720 replay has a lot of empty space and Pygame is already in place. This keeps the milestone as one runnable desktop app.
- User decision: Accepted.
- Changes if different: A web UI would be easier for charts and layout but requires a new frontend stack; a multi-window or CLI+GUI split weakens the learning-demo feel.
- Lands in: `PLAN.md`, `SLICES.md`, ADR.

### F6. Exploration/exploitation representation

- Status: ANSWERED
- Recommendation: Record the actual decision mode per step (`explore` or `exploit`) and show it as both a step label and an epsilon pie/gauge.
- Reasoning: Epsilon percentage alone says probability, not what happened on this move. For teaching, showing the sampled decision is more useful.
- User decision: Record every actual explore/exploit decision. In the UI, prefer using the epsilon pie/gauge itself as the decision indicator by highlighting the selected region, with optional compact text if needed.
- Changes: `choose_action` must expose decision metadata; the renderer should treat the pie/gauge as an animated decision object rather than a static probability chart.
- Lands in: `PLAN.md`, `SLICES.md`.

### F7. Export path

- Status: ANSWERED
- Recommendation: Render deterministic frames from Pygame offscreen and encode with `ffmpeg`.
- Reasoning: This keeps visual preview and video export on one rendering path. It avoids screen-capture flakiness and works in CI/headless mode if `ffmpeg` is installed.
- User decision: Accepted.
- Changes if different: Live screen recording is faster to prototype but less reproducible; a separate video library would duplicate rendering logic.
- Lands in: `PLAN.md`, `SLICES.md`, ADR.

### F8. Full training runtime in final video

- Status: ANSWERED
- Recommendation: Record every event in data, but compress the video timeline: fast-forward failed/repetitive episodes, slow down meaningful transitions, and end on the first optimal 31-move solution.
- Reasoning: A literal real-time playback of hundreds of episodes will be too long for YouTube. The event log can be complete while the video chooses pacing.
- User decision: Accepted.
- Changes if different: Literal playback is faithful but likely boring; aggressive summarization is more watchable but needs clear visual indicators that time is compressed.
- Lands in: `PLAN.md`, `SLICES.md`.

### F9. Sound and asset policy

- Status: ANSWERED
- Recommendation: Generate simple deterministic sound effects programmatically in this repo first, with generated or permissively licensed local sound effects committed under `src/gui/assets/audio/`.
- Reasoning: YouTube upload makes asset rights matter. Short local `.wav`/`.ogg` files keep playback deterministic and offline. Local synthesis is enough for beeps, boops, coin clinks, short arpeggios, reward stingers, and error/penalty ticks.
- User decision: Accepted, with interest in Codex/Claude being able to generate sound effects programmatically.
- Changes if different: Pulling sounds from online sources later can block the video on licensing cleanup.
- Lands in: `PLAN.md`, `SLICES.md`.

## Assumptions

### A1. Primary user

- Status: ASSUMED
- Answer: The primary user is you as a learner/builder inspecting how an RL agent learns Tower of Hanoi; agents are secondary users that need reliable commands and files.
- Reasoning: The project is exploratory and educational, not a packaged end-user game.

### A2. Storage format

- Status: ASSUMED
- Answer: Store training visualization data as human-diffable JSON first.
- Reasoning: The current records are JSON, the state space is small, and JSON keeps debugging easy. Compression or SQLite can wait.

### A3. Single write path

- Status: ASSUMED
- Answer: Training writes replay/learning artifacts; the visualizer is read-only.
- Reasoning: Avoids concurrency and conflict concerns for the milestone.

### A4. Failure behavior

- Status: ASSUMED
- Answer: Bad or missing replay artifacts should fail with a clear error naming the file and expected schema.
- Reasoning: Silent fallback would make recorded learning demos hard to trust.

### A5. Dependencies

- Status: ASSUMED
- Answer: Stay with `pygame`, `numpy`, `gymnasium`, `pytest`, and `ruff`; add no charting dependency for the first Pygame heatmap.
- Reasoning: Pygame can draw the heatmap and pie/gauge directly; adding matplotlib would complicate interactive rendering.

### A6. Runtime

- Status: ASSUMED
- Answer: Local desktop/WSL runtime is the supported path; CI validates non-GUI logic and import/compile safety.
- Reasoning: Headless CI can test the data contracts and rendering math without opening a window.

### A7. Success criteria

- Status: ASSUMED
- Answer: A demo is successful when `make train` produces learning artifacts, `make replay` opens a single dashboard, and the 800/1000 checkpoints show optimal 31-move solutions with synchronized q-values, rewards, epsilon, and decision mode.
- Reasoning: This is specific, checkable, and matches the current observed behavior.

### A8. Security

- Status: ASSUMED
- Answer: No secrets are involved in the app data; generated records must stay out of git by default.
- Reasoning: The only files produced are training/replay artifacts.

### A9. Versioning

- Status: ASSUMED
- Answer: Add a `schema_version` field to new learning artifacts.
- Reasoning: The current plain list-of-moves format is already too thin for q-table visualization, so the next format needs migration room.

## Deferred

### D1. Deep Q-learning

- Status: DEFERRED
- Answer: Plan as a later milestone after Q-learning visualization works.

### D2. Web or video export

- Status: DEFERRED
- Answer: Consider later after the interactive dashboard exists.

### D3. Publishable docs site

- Status: DEFERRED
- Answer: Keep planning docs in repo for now; no docs site for this milestone.
