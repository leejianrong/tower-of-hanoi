// The browser's side of the replay contract (ADR-0007, ADR-0008). Pure functions, no DOM, so Node
// can test them (tests/js) and Python can check them against its own rules
// (tests/dashboard/test_js_contract.py). Timing is decided in Python; this file only looks things
// up in the schedule it is given and interpolates inside one step.

// How far through a step the disc has finished lifting, and finished travelling. The rest is the
// descent onto the target stack. The Q update shows up when the disc lands (UPDATE_PHASE in
// src/dashboard/player.py is kept equal to travelEnd + most of the descent).
export const PHASE = { liftEnd: 0.28, travelEnd: 0.72 };

const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);
const lerp = (a, b, k) => a + (b - a) * k;

// Smoothstep: starts and ends gently, so a disc eases off the stack and onto the next.
export function ease(x) {
  const k = clamp(x, 0, 1);
  return k * k * (3 - 2 * k);
}

// State id -> three stacks of disc ids, bottom to top. Disc d on rod r contributes r * 3**d.
export function decodeState(id, discs) {
  const rods = [[], [], []];
  for (let d = discs - 1; d >= 0; d--) rods[Math.floor(id / 3 ** d) % 3].push(d);
  return rods;
}

// Largest index whose start is <= value (like Python's bisect_right(a, v) - 1), at least 0.
function floorIndex(starts, value, last) {
  let lo = 0;
  let hi = last;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (starts[mid] <= value) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

// Where the playhead is at time t (seconds): a global step and how far through it (0..1).
export function locate(schedule, t) {
  const last = schedule.step_t0.length - 1;
  if (t >= schedule.total_s) return { step: last, phase: 1, done: true };
  const step = floorIndex(schedule.step_t0, t, last);
  const phase = clamp((t - schedule.step_t0[step]) / schedule.step_dur[step], 0, 1);
  return { step, phase, done: false };
}

export function episodeOfStep(replay, step) {
  const starts = replay.episodes.start;
  return floorIndex(starts, step, starts.length - 2);
}

// Every disc's position at time t. Resting discs sit on their rod; the moving disc lifts clear
// above its rod, travels over to the target rod, then descends onto the top of that stack.
// geom = {rodX: [x0, x1, x2], base, discH, lift}; y is the top of a disc's slot.
export function boardAt(replay, schedule, t, geom) {
  const position = locate(schedule, t);
  const { step, phase } = position;
  const steps = replay.steps;
  const rods = decodeState(steps.state[step], replay.config.num_discs);
  const moving = steps.disc[step];
  const [source, target] = replay.config.action_map[steps.action[step]];
  const { rodX, base, discH, lift } = geom;

  const discs = [];
  rods.forEach((stack, rod) => {
    stack.forEach((id, level) => {
      if (id !== moving) discs.push({ id, x: rodX[rod], y: base - (level + 1) * discH, moving: false });
    });
  });

  const restY = base - rods[source].length * discH; // the moving disc is the top of its rod
  const landY = base - (rods[target].length + 1) * discH; // target stack, without the moving disc
  let x;
  let y;
  if (phase < PHASE.liftEnd) {
    x = rodX[source];
    y = lerp(restY, lift, ease(phase / PHASE.liftEnd));
  } else if (phase < PHASE.travelEnd) {
    x = lerp(rodX[source], rodX[target], ease((phase - PHASE.liftEnd) / (PHASE.travelEnd - PHASE.liftEnd)));
    y = lift;
  } else {
    x = rodX[target];
    y = lerp(lift, landY, ease((phase - PHASE.travelEnd) / (1 - PHASE.travelEnd)));
  }
  discs.push({ id: moving, x, y, moving: true });
  return { position, discs, episode: episodeOfStep(replay, step) };
}

// The decision at this step, for the pie: epsilon of the episode and whether it explored.
export function pieAt(replay, step) {
  const episode = episodeOfStep(replay, step);
  return { epsilon: replay.episodes.epsilon[episode], explore: replay.steps.explore[step] === 1 };
}

// The cues passed as the clock moves from ``from`` to ``to``: indices [lo, hi) of the cue list
// with from < t <= to (like Python's Cues.between). The cue list is sorted by time.
export function cuesBetween(cues, from, to) {
  const upper = (value) => {
    let lo = 0;
    let hi = cues.t.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (cues.t[mid] <= value) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  };
  return [upper(from), upper(to)];
}
