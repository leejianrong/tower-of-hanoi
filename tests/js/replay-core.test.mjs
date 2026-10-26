import assert from "node:assert/strict";
import test from "node:test";

import { PHASE, boardAt, decodeState, ease, episodeOfStep, locate, pieAt } from "../../src/dashboard/static/replay-core.js";

const GEOM = { rodX: [100, 280, 460], base: 256, discH: 28, lift: 30 };

// Two episodes of a 3-disc game. Episode 0: disc 0 from rod 0 to rod 1, then disc 1 from rod 0
// to rod 2. Episode 1: disc 0 from rod 0 to rod 2. (State ids: disc d on rod r adds r * 3**d.)
const replay = {
  config: { num_discs: 3, action_map: [[0, 1], [0, 2], [1, 0], [1, 2], [2, 0], [2, 1]] },
  episodes: { start: [0, 2, 3], epsilon: [1.0, 0.5] },
  steps: {
    state: [0, 1, 0],
    action: [0, 1, 1],
    disc: [0, 1, 0],
    explore: [1, 0, 1],
  },
};
const schedule = { step_t0: [0, 1, 2.5], step_dur: [1, 1, 1], total_s: 3.5 };

test("decodeState: start state, and a state with discs on different rods", () => {
  assert.deepEqual(decodeState(0, 3), [[2, 1, 0], [], []]);
  // disc 0 on rod 2, disc 1 on rod 0, disc 2 on rod 1
  assert.deepEqual(decodeState(2 + 0 * 3 + 1 * 9, 3), [[1], [2], [0]]);
});

test("decodeState visits every state id exactly once with all discs present", () => {
  const seen = new Set();
  for (let id = 0; id < 27; id++) {
    const rods = decodeState(id, 3);
    assert.equal(rods.flat().length, 3);
    seen.add(JSON.stringify(rods));
  }
  assert.equal(seen.size, 27);
});

test("locate: step starts, the gap between episodes, before the start and the end", () => {
  assert.deepEqual(locate(schedule, 0), { step: 0, phase: 0, done: false });
  assert.equal(locate(schedule, 1.5).step, 1);
  assert.equal(locate(schedule, 1.5).phase, 0.5);
  // 2.0 is in the gap after step 1 (which ended at 2.0): a finished step
  assert.deepEqual(locate(schedule, 2.2), { step: 1, phase: 1, done: false });
  assert.equal(locate(schedule, -5).step, 0);
  assert.deepEqual(locate(schedule, 99), { step: 2, phase: 1, done: true });
});

test("episodeOfStep follows the episode boundaries", () => {
  assert.deepEqual([0, 1, 2].map((s) => episodeOfStep(replay, s)), [0, 0, 1]);
});

test("ease is monotone from 0 to 1 and clamps", () => {
  assert.equal(ease(-1), 0);
  assert.equal(ease(2), 1);
  assert.equal(ease(0.5), 0.5);
  let last = 0;
  for (let i = 1; i <= 20; i++) {
    const v = ease(i / 20);
    assert.ok(v >= last);
    last = v;
  }
});

const moving = (t) => boardAt(replay, schedule, t, GEOM).discs.find((d) => d.moving);

test("a step starts with the disc at rest on top of its rod", () => {
  // step 0: disc 0 is the top of rod 0, which holds 3 discs
  const d = moving(0);
  assert.deepEqual([d.id, d.x, d.y], [0, 100, 256 - 3 * 28]);
});

test("the disc lifts clear above the rod, travels over, then descends onto the stack", () => {
  const lifted = moving(PHASE.liftEnd * 1 + 0.001);
  assert.ok(Math.abs(lifted.y - GEOM.lift) < 1, "fully lifted before it moves sideways");
  assert.equal(lifted.x < 101, true);

  const mid = moving((PHASE.liftEnd + PHASE.travelEnd) / 2);
  assert.equal(mid.y, GEOM.lift, "travels at lift height");
  assert.ok(mid.x > 100 && mid.x < 280, "is between the rods");
  assert.ok(Math.abs(mid.x - 190) < 1, "halfway at the midpoint of the ease");

  const landed = moving(0.9999);
  assert.equal(landed.x, 280);
  assert.ok(Math.abs(landed.y - (256 - 28)) < 0.5, "lands on the empty target rod");
});

test("the disc lands on top of the stack already on the target rod", () => {
  // step 1: disc 1 moves rod 0 -> rod 2; rod 2 is empty in state id 1 (disc 0 is on rod 1)
  const near = boardAt(replay, schedule, 1.9999, GEOM).discs.find((d) => d.moving);
  assert.equal(near.x, 460);
  assert.ok(Math.abs(near.y - (256 - 28)) < 0.5);
  // step 2 (episode 1): disc 0 moves 0 -> 2 with discs 2 and 1 on rod 0 below it
  const first = boardAt(replay, schedule, 2.5, GEOM).discs.find((d) => d.moving);
  assert.equal(first.y, 256 - 3 * 28);
});

test("resting discs never overlap in a rod and the moving disc is listed once", () => {
  const { discs } = boardAt(replay, schedule, 0.5, GEOM);
  assert.equal(discs.filter((d) => d.moving).length, 1);
  assert.equal(new Set(discs.map((d) => d.id)).size, 3);
  const rest = discs.filter((d) => !d.moving);
  const ys = rest.filter((d) => d.x === 100).map((d) => d.y);
  assert.equal(new Set(ys).size, ys.length);
});

test("pieAt reports epsilon of the episode and whether the step explored", () => {
  assert.deepEqual(pieAt(replay, 0), { epsilon: 1.0, explore: true });
  assert.deepEqual(pieAt(replay, 1), { epsilon: 1.0, explore: false });
  assert.deepEqual(pieAt(replay, 2), { epsilon: 0.5, explore: true });
});
