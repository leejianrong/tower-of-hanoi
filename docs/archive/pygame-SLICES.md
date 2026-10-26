# Tower of Hanoi RL Visualizer: Slices

Vertical increments. Each ends in something visible or exportable.

## V1: Complete Training Telemetry

**Delivers:** R0, R1, R3

**Build Plan**

1. Add action-decision metadata to the Q-learning agent.
2. Add a schema-versioned training event writer.
3. Record every episode and step: state, action, decision mode, reward, epsilon, next state, done flags, and Q-table updates.
4. Stop capture on first optimal 31-move solve.
5. Add `make train-visualization` or update `make train` once the artifact is stable.

**Demo:** Run training and inspect a JSON artifact that contains all episode/step events up to the first optimal solve.

**Rests on assumptions:** A1, A3, A9. If JSON becomes too large, keep the schema but reduce duplication with Q-row deltas.

### Test Plan

#### End-to-End

- A deterministic short training run writes a schema-versioned artifact with explore/exploit decisions and rewards for every step.

#### Integration

- The artifact reader validates schema version and reconstructs an episode timeline.

#### Unit

- `choose_action` exposes action mode without selecting masked actions.
- The event writer serializes NumPy values into plain JSON.

## V2: Heatmap Replay Dashboard

**Delivers:** R2, R3

**Build Plan**

1. Add a replay artifact reader that produces a pure dashboard view model.
2. Extend Pygame layout: tower left, Q-table heatmap right, metadata strips.
3. Draw full state-action heatmap and highlight current state/action.
4. Draw epsilon gauge/pie and highlight actual explore/exploit decision.
5. Add keyboard controls for pause, step, speed, episode jump, and quit.

**Demo:** Open a recorded training artifact and scrub through episodes while the board, Q-table, and epsilon decision indicator stay synchronized.

**Rests on assumptions:** A5, A6.

### Test Plan

#### End-to-End

- Headless render of a selected event produces a nonblank dashboard frame with board and heatmap regions.

#### Integration

- View model maps an event's state/action/Q-values to highlighted heatmap coordinates.

#### Unit

- Heatmap color scaling handles zero, positive, negative, and masked values.
- Epsilon gauge geometry produces stable sectors for explore/exploit.

## V3: Reward, Timeline, and Learning Animations

**Delivers:** R4, R6

**Build Plan**

1. Add action arrow animation from source rod to target rod.
2. Add reward coins, penalty ticks, and terminal-solve celebration.
3. Add Q-cell pulse and TD-error flash.
4. Add episode summary cards and learning curve sparkline.
5. Add playback compression rules for failed/repetitive episodes and slowdowns for key transitions.

**Demo:** Play a full training artifact and see early failures fast-forward, meaningful updates highlighted, and the first 31-move solve celebrated.

**Rests on assumptions:** A7.

### Test Plan

#### End-to-End

- A sample artifact renders with visible reward animation, Q-cell pulse, and episode transition.

#### Integration

- Timeline compressor preserves event ordering while assigning shorter durations to repetitive sections.

#### Unit

- Animation clocks produce deterministic positions and alpha values for fixed timestamps.

## V4: Programmatic Sound Effects

**Delivers:** R5

**Build Plan**

1. Add `scripts/audio/generate_sfx.py`.
2. Generate WAV assets for explore, exploit, coin, penalty, episode end, and solve.
3. Add Pygame sound loading with graceful mute fallback.
4. Synchronize sounds with decisions, rewards, and solve events.
5. Document regeneration command and asset policy.

**Demo:** Run the replay and hear generated SFX tied to decisions and rewards.

**Rests on assumptions:** F9. If generated SFX are not polished enough, replace the assets while keeping the same semantic filenames.

### Test Plan

#### End-to-End

- The generator creates all expected WAV files and replay loads them without crashing.

#### Integration

- Audio manifest maps semantic events to asset paths.

#### Unit

- Generated WAV files have expected sample rate, duration range, and non-silent samples.

## V5: Video Export

**Delivers:** R6, R7

**Build Plan**

1. Add an offscreen render loop that writes frames for a selected artifact.
2. Compose audio timing events into a single soundtrack or mux generated sounds during encoding.
3. Add `make export-video`.
4. Use `ffmpeg` to encode a YouTube-ready MP4.
5. Add checks that fail clearly when `ffmpeg` is unavailable.

**Demo:** Run one command and produce an MP4 showing the compressed training visualization through the first optimal solve.

**Rests on assumptions:** F7, F8.

### Test Plan

#### End-to-End

- With `ffmpeg` installed, export command writes a playable MP4 for a short fixture artifact.

#### Integration

- Frame exporter renders deterministic numbered frames from the same dashboard renderer used by replay.

#### Unit

- Export command builder produces stable `ffmpeg` arguments and validates missing input paths.
