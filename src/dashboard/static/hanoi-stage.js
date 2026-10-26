// <indah-x-hanoi-stage>: the board, the explore/exploit pie and the transport controls, driven by
// a clock that runs in the browser (ADR-0007).
//
// The page downloads the replay and its timeline once, then every frame is a pure function of the
// clock (replay-core.js). Python is told where the playhead is, a few times a second, through the
// `tick` event, so the charts and the Q-table follow this clock rather than lead it.
//
// URL parameters: ?t=<seconds> starts there, ?paused=1 starts paused, and ?record=1 is the video
// exporter's mode (ADR-0009): the clock never advances by itself, the controls are hidden, nothing
// animates in real time, and `window.hanoiRecorder.seek(t)` moves the clock and resolves once the
// board and Python's charts show that exact time.
const NS = "http://www.w3.org/2000/svg";
const BASE_URL = new URL("../../hanoi/", import.meta.url);
const GEOM = { rodX: [100, 280, 460], base: 256, discH: 28, lift: 30 };
const ROD_TOP = 66;
const SPEEDS = [1, 4, 16, 64];
const TICK_EVERY_MS = 200; // at 1x and 4x; faster playback reports more often so the charts keep up
const MIN_TICK_MS = 50;
const MAX_FRAME_S = 0.1; // a throttled background tab must not jump the clock

const CSS = `
:host { display: block; color: var(--text); font-family: var(--font-body); }
.stage { display: flex; flex-direction: column; gap: 14px; }
svg.board { width: 100%; height: auto; display: block; }
.row { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
.pie { display: flex; align-items: center; gap: 14px; font-family: var(--font-mono); font-size: 0.95rem; }
.pie svg { width: 132px; height: 132px; overflow: visible; }
.pie .label { min-width: 8.5em; transition: opacity 150ms; }
.pie .explore { color: var(--x-explore); text-align: right; }
.pie .exploit { color: var(--x-exploit); }
.pie .dim { opacity: 0.4; }
:host([record]) * { transition: none !important; }
:host([record]) .transport { visibility: hidden; }
.pie path { transition: opacity 150ms, transform 150ms; }
.transport { flex: 1 1 360px; display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
button { min-width: 44px; height: 44px; border-radius: var(--radius-sm); border: 1px solid var(--outline);
  background: var(--surface-2); color: var(--text); cursor: pointer; font: 500 0.85rem var(--font-mono); padding: 0 12px;
  display: inline-flex; align-items: center; justify-content: center; }
button:hover { filter: brightness(1.15); }
button:focus-visible, input:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }
button.main { background: var(--primary); border-color: var(--primary); color: var(--on-primary); }
button[aria-pressed="true"] { background: var(--surface-3); border-color: var(--text); }
.speeds { display: flex; gap: 4px; margin-left: auto; }
.scrub { display: flex; align-items: center; gap: 12px; }
.scrub input { flex: 1; accent-color: var(--primary); height: 24px; }
.time { font: 0.8rem var(--font-mono); color: var(--muted); white-space: nowrap; }
.note { color: var(--muted); font-size: 0.9rem; }
`;

const el = (tag, attrs = {}, style = {}) => {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, String(v));
  for (const [k, v] of Object.entries(style)) node.style.setProperty(k, v);
  return node;
};
const html = (tag, props = {}, ...children) => {
  const node = document.createElement(tag);
  Object.assign(node, props);
  node.append(...children);
  return node;
};
const icon = (path) => {
  const svg = el("svg", { width: 20, height: 20, viewBox: "0 0 24 24", "aria-hidden": "true" }, { fill: "currentColor" });
  svg.append(el("path", { d: path }));
  return svg;
};
const ICONS = {
  prevEpisode: "M5 6h2v12H5zM19 6v12l-9-6z",
  stepBack: "M17 6v12l-8-6z",
  play: "M8 5v14l11-7z",
  pause: "M7 5h3.5v14H7zM13.5 5H17v14h-3.5z",
  stepForward: "M7 6v12l8-6z",
  nextEpisode: "M17 6h2v12h-2zM5 6l9 6-9 6z",
  soundOn: "M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0 0 14 7.97v8.05c1.48-.73 2.5-2.25 2.5-4.02z",
  soundOff:
    "M16.5 12A4.5 4.5 0 0 0 14 7.97v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51A8.8 8.8 0 0 0 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06a8.99 8.99 0 0 0 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z",
};
const SOUND_KEY = "hanoi-sound";
const MAX_SOUND_SPEED = 4; // faster playback drops the sounds (src/audio/cues.py CueSettings)
const MAX_CUES_PER_FRAME = 6; // after a stall, play none rather than a burst
const readPreference = () => {
  try {
    return localStorage.getItem(SOUND_KEY) !== "off";
  } catch {
    return true;
  }
};
const writePreference = (on) => {
  try {
    localStorage.setItem(SOUND_KEY, on ? "on" : "off");
  } catch {
    /* private window: the choice just does not persist */
  }
};
const clock = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

export default class HanoiStage extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
    this._data = null;
    this._t = 0;
    this._playing = true;
    this._speed = 1;
    this._scrubbing = false;
    this._raf = 0;
    this._lastNow = 0;
    this._lastTick = 0;
    this._drawn = { t: NaN, pie: "" };
    this._appliedT = null;
    this._waiter = null;
    this._sound = readPreference();
    this._audio = null; // { ctx, cues, buffers } once the sounds are loaded
    this._audioLoading = false;
    this._skipCues = true; // the frame after a seek or a pause must not play the cues it jumped over
    this._onGesture = () => this._wakeAudio();
    this._onKey = (e) => this._key(e);
  }

  connectedCallback() {
    this.style.display = "block";
    this._build();
    window.addEventListener("keydown", this._onKey);
    window.addEventListener("pointerdown", this._onGesture);
    window.addEventListener("keydown", this._onGesture);
    this._load();
  }

  disconnectedCallback() {
    cancelAnimationFrame(this._raf);
    window.removeEventListener("keydown", this._onKey);
    window.removeEventListener("pointerdown", this._onGesture);
    window.removeEventListener("keydown", this._onGesture);
    this._audio?.ctx.close();
  }

  async _load() {
    try {
      const [core, response] = await Promise.all([
        import(new URL("replay-core.js", BASE_URL).href),
        fetch(new URL("replay.json", BASE_URL)),
      ]);
      if (!response.ok) throw new Error(`replay.json: ${response.status}`);
      const bundle = await response.json();
      this._core = core;
      this._data = bundle;
      this._note.remove();
      this._slider.max = String(bundle.schedule.total_s);
      const params = new URLSearchParams(location.search);
      if (params.has("t")) this._t = Math.min(Math.max(Number(params.get("t")) || 0, 0), bundle.schedule.total_s);
      if (params.get("paused") === "1") this._playing = false;
      this._buildPie();
      this._syncControls();
      this._emitTick();
      if (params.has("record")) {
        this._startRecorder();
        return;
      }
      this._lastNow = performance.now();
      this._raf = requestAnimationFrame((now) => this._frame(now));
    } catch (error) {
      this._note.textContent = "The replay could not be loaded. Run `make train`, then restart the dashboard.";
      console.error(error);
    }
  }

  // ---- recording -------------------------------------------------------------------------

  /** Python sets this to the playhead it last applied; the recorder waits for it to match. */
  set applied_t(value) {
    this._appliedT = value;
    this._settle();
  }

  get applied_t() {
    return this._appliedT;
  }

  _startRecorder() {
    this.setAttribute("record", "");
    this._playing = false;
    this._render();
    window.hanoiRecorder = {
      totalS: this._data.schedule.total_s,
      seek: (t) => this._recordSeek(t),
    };
  }

  /** Show time ``t`` everywhere, then resolve after the page has painted it. */
  async _recordSeek(t) {
    this._t = Math.min(Math.max(Number(t) || 0, 0), this._data.schedule.total_s);
    this._render();
    const sent = Math.round(this._t * 1000) / 1000;
    const acknowledged = new Promise((resolve) => {
      this._waiter = { t: sent, resolve };
    });
    this._emitTick();
    this._settle();
    await acknowledged;
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  }

  _settle() {
    if (this._waiter && this._appliedT === this._waiter.t) {
      const { resolve } = this._waiter;
      this._waiter = null;
      resolve();
    }
  }

  // ---- layout ----------------------------------------------------------------------------

  _build() {
    const sheet = new CSSStyleSheet();
    sheet.replaceSync(CSS);
    this._root.adoptedStyleSheets = [sheet];

    this._svg = el("svg", { class: "board", viewBox: "0 0 560 310", role: "img" });
    this._note = html("div", { className: "note", textContent: "Loading the replay..." });
    this._pieHost = html("div", { className: "pie" });
    this._transport = this._buildTransport();
    this._root.replaceChildren(
      html("div", { className: "stage" }, this._svg, this._note, html("div", { className: "row" }, this._pieHost, this._transport)),
    );
    this._buildBoard();
  }

  _buildTransport() {
    const button = (label, path, onClick, cls = "") => {
      const b = html("button", { type: "button", className: cls, onclick: onClick });
      b.setAttribute("aria-label", label);
      b.append(icon(path));
      return b;
    };
    this._playButton = button("Pause", ICONS.pause, () => this._toggle(), "main");
    this._soundButton = button("Sound", ICONS.soundOn, () => this._toggleSound(), "sound");
    this._speedButtons = SPEEDS.map((s) => {
      const b = html("button", { type: "button", textContent: `${s}x`, onclick: () => this._setSpeed(s) });
      b.setAttribute("aria-label", `Speed ${s} times`);
      return b;
    });
    this._slider = html("input", { type: "range", min: "0", max: "1", step: "0.01", value: "0" });
    this._slider.setAttribute("aria-label", "Playback position");
    this._slider.addEventListener("pointerdown", () => (this._scrubbing = true));
    this._slider.addEventListener("pointerup", () => (this._scrubbing = false));
    this._slider.addEventListener("input", () => this._seek(Number(this._slider.value)));
    this._time = html("span", { className: "time" });

    const controls = html(
      "div",
      { className: "controls" },
      button("Previous episode", ICONS.prevEpisode, () => this._jumpEpisode(-1)),
      button("Previous step", ICONS.stepBack, () => this._jumpStep(-1)),
      this._playButton,
      button("Next step", ICONS.stepForward, () => this._jumpStep(1)),
      button("Next episode", ICONS.nextEpisode, () => this._jumpEpisode(1)),
      html("div", { className: "speeds" }, this._soundButton, ...this._speedButtons),
    );
    return html("div", { className: "transport" }, controls, html("div", { className: "scrub" }, this._slider, this._time));
  }

  _buildBoard() {
    const svg = this._svg;
    svg.append(el("rect", { x: 16, y: GEOM.base, width: 528, height: 10, rx: 5 }, { fill: "var(--x-base)" }));
    GEOM.rodX.forEach((x, rod) => {
      svg.append(el("rect", { x: x - 4, y: ROD_TOP, width: 8, height: GEOM.base - ROD_TOP + 2, rx: 4 }, { fill: "var(--x-rod)" }));
      const label = el("text", { x, y: 293, "text-anchor": "middle", "font-size": 13 }, { fill: "var(--muted)", "font-family": "var(--font-mono)" });
      label.textContent = `rod ${rod}`;
      svg.append(label);
    });
    this._discEls = new Map();
  }

  _discEl(id, count) {
    let node = this._discEls.get(id);
    if (!node) {
      const width = count < 2 ? 172 : 52 + (id * 120) / (count - 1);
      node = el("g");
      node.append(
        el("rect", { x: -width / 2, y: 2, width, height: GEOM.discH - 4, rx: 9 }, { fill: `var(--x-disc-${id % 5})` }),
      );
      const text = el("text", { x: 0, y: GEOM.discH / 2 + 5, "text-anchor": "middle", "font-size": 13, "font-weight": 500 }, { fill: "#0b1020", "font-family": "var(--font-mono)" });
      text.textContent = String(id);
      node.append(text);
      this._svg.append(node);
      this._discEls.set(id, node);
    }
    return node;
  }

  _buildPie() {
    const NSV = (tag, attrs) => el(tag, attrs);
    const svg = NSV("svg", { viewBox: "0 0 180 180", role: "img" });
    this._exploreWedge = NSV("path", {});
    this._exploitWedge = NSV("path", {});
    svg.append(this._exploreWedge, this._exploitWedge);
    this._exploreWedge.style.fill = "var(--x-explore)";
    this._exploitWedge.style.fill = "var(--x-exploit)";
    this._exploreLabel = html("div", { className: "label explore" });
    this._exploitLabel = html("div", { className: "label exploit" });
    this._pieSvg = svg;
    this._pieHost.replaceChildren(this._exploreLabel, svg, this._exploitLabel);
  }

  // ---- clock -----------------------------------------------------------------------------

  _frame(now) {
    const dt = Math.min((now - this._lastNow) / 1000, MAX_FRAME_S);
    this._lastNow = now;
    const total = this._data.schedule.total_s;
    if (this._playing && this._t < total) {
      const before = this._t;
      this._t = Math.min(this._t + dt * this._speed, total);
      this._playCues(before, this._t);
      if (this._t >= total) {
        this._playing = false;
        this._syncControls();
      }
    }
    this._render();
    const every = Math.max(MIN_TICK_MS, TICK_EVERY_MS / Math.max(1, this._speed / 4));
    if (now - this._lastTick >= every && (this._playing || this._tickPending)) this._emitTick(now);
    this._raf = requestAnimationFrame((n) => this._frame(n));
  }

  _render() {
    if (this._t === this._drawn.t) return;
    this._drawn.t = this._t;
    const { replay, schedule } = this._data;
    const frame = this._core.boardAt(replay, schedule, this._t, GEOM);
    const count = replay.config.num_discs;
    for (const disc of frame.discs) {
      const node = this._discEl(disc.id, count);
      node.setAttribute("transform", `translate(${disc.x.toFixed(2)} ${disc.y.toFixed(2)})`);
      node.firstChild.style.stroke = disc.moving ? "var(--text)" : "none";
      node.firstChild.setAttribute("stroke-width", disc.moving ? 3 : 0);
    }
    const moving = frame.discs.find((d) => d.moving);
    if (moving && moving.id !== this._topId) {
      this._svg.append(this._discEl(moving.id, count)); // the moving disc is drawn above the rest
      this._topId = moving.id;
    }
    this._drawPie(this._core.pieAt(replay, frame.position.step));
    if (!this._scrubbing) this._slider.value = String(this._t);
    this._time.textContent = `${clock(this._t)} / ${clock(schedule.total_s)}`;
  }

  _drawPie({ epsilon, explore }) {
    const key = `${epsilon}|${explore}`;
    if (key === this._drawn.pie) return;
    this._drawn.pie = key;
    const C = 90;
    const R = 80;
    const point = (f) => {
      const a = f * 2 * Math.PI - Math.PI / 2;
      return [C + R * Math.cos(a), C + R * Math.sin(a)];
    };
    const wedge = (from, to) => {
      if (to - from >= 0.9999) return `M ${C - R} ${C} A ${R} ${R} 0 1 1 ${C + R} ${C} A ${R} ${R} 0 1 1 ${C - R} ${C} Z`;
      const [x1, y1] = point(from);
      const [x2, y2] = point(to);
      return `M ${C} ${C} L ${x1.toFixed(2)} ${y1.toFixed(2)} A ${R} ${R} 0 ${to - from > 0.5 ? 1 : 0} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} Z`;
    };
    const shift = (from, to) => {
      const mid = ((from + to) / 2) * 2 * Math.PI - Math.PI / 2;
      return `translate(${(6 * Math.cos(mid)).toFixed(1)}px, ${(6 * Math.sin(mid)).toFixed(1)}px)`;
    };
    this._exploreWedge.setAttribute("d", wedge(0, epsilon));
    this._exploitWedge.setAttribute("d", wedge(epsilon, 1));
    for (const [node, lit, from, to] of [[this._exploreWedge, explore, 0, epsilon], [this._exploitWedge, !explore, epsilon, 1]]) {
      node.style.opacity = lit ? "1" : "0.3";
      node.style.transform = lit ? shift(from, to) : "none";
    }
    const pct = (v) => `${(v * 100).toFixed(1)}%`;
    this._exploreLabel.textContent = `explore ${pct(epsilon)}`;
    this._exploitLabel.textContent = `exploit ${pct(1 - epsilon)}`;
    this._exploreLabel.classList.toggle("dim", !explore);
    this._exploitLabel.classList.toggle("dim", explore);
    this._pieSvg.setAttribute("aria-label", `Epsilon pie: ${pct(epsilon)} explore. The agent is ${explore ? "exploring" : "exploiting"}.`);
  }

  // ---- sound -----------------------------------------------------------------------------

  /** Browsers only allow audio after a gesture, so the sounds load on the first click or key. */
  async _wakeAudio() {
    if (!this._sound || !this._data || this.hasAttribute("record") || this._audioLoading) return;
    if (this._audio) {
      if (this._audio.ctx.state === "suspended") this._audio.ctx.resume();
      return;
    }
    this._audioLoading = true;
    try {
      const ctx = new AudioContext();
      const cues = await (await fetch(new URL("cues.json", BASE_URL))).json();
      const buffers = {};
      await Promise.all(
        cues.names.map(async (name) => {
          const bytes = await (await fetch(new URL(`audio/${name}.wav`, BASE_URL))).arrayBuffer();
          buffers[name] = await ctx.decodeAudioData(bytes);
        }),
      );
      this._audio = { ctx, cues, buffers };
      this._skipCues = true;
    } catch (error) {
      console.warn("Sound is unavailable", error);
      this._sound = false;
      this._syncControls();
    } finally {
      this._audioLoading = false;
    }
  }

  _playCues(from, to) {
    const skip = this._skipCues;
    this._skipCues = false;
    if (skip || !this._sound || !this._audio || this._speed > MAX_SOUND_SPEED) return;
    const { ctx, cues, buffers } = this._audio;
    const [lo, hi] = this._core.cuesBetween(cues, from, to);
    if (hi - lo > MAX_CUES_PER_FRAME) return;
    for (let i = lo; i < hi; i++) {
      const source = ctx.createBufferSource();
      source.buffer = buffers[cues.names[cues.sound[i]]];
      source.connect(ctx.destination);
      source.start();
    }
  }

  _toggleSound() {
    this._sound = !this._sound;
    writePreference(this._sound);
    this._skipCues = true;
    this._syncControls();
    if (this._sound) this._wakeAudio();
  }

  _emitTick(now = performance.now()) {
    this._lastTick = now;
    this._tickPending = false;
    this.dispatchEvent(new CustomEvent("tick", { detail: { t: Math.round(this._t * 1000) / 1000, playing: this._playing } }));
  }

  // ---- controls --------------------------------------------------------------------------

  _toggle() {
    if (!this._data) return;
    if (!this._playing && this._t >= this._data.schedule.total_s) this._t = 0;
    this._playing = !this._playing;
    this._skipCues = true;
    this._lastNow = performance.now();
    this._syncControls();
    this._tickPending = true;
  }

  _setSpeed(speed) {
    this._speed = speed;
    this._syncControls();
  }

  _seek(t) {
    this._t = Math.min(Math.max(t, 0), this._data.schedule.total_s);
    this._skipCues = true;
    this._tickPending = true;
  }

  _jumpStep(direction) {
    const { schedule } = this._data;
    const { step } = this._core.locate(schedule, this._t);
    const target = Math.min(Math.max(step + direction, 0), schedule.step_t0.length - 1);
    this._playing = false;
    this._seek(schedule.step_t0[target]);
    this._syncControls();
  }

  _jumpEpisode(direction) {
    const { replay, schedule } = this._data;
    const { step } = this._core.locate(schedule, this._t);
    const episode = this._core.episodeOfStep(replay, step);
    const atStart = schedule.step_t0[replay.episodes.start[episode]] >= this._t - 1e-6;
    const target = Math.min(Math.max(direction < 0 && !atStart ? episode : episode + direction, 0), schedule.episode_t0.length - 1);
    this._seek(schedule.episode_t0[target]);
  }

  _syncControls() {
    const label = this._playing ? "Pause" : "Play";
    this._playButton.setAttribute("aria-label", label);
    this._playButton.replaceChildren(icon(this._playing ? ICONS.pause : ICONS.play));
    this._soundButton.setAttribute("aria-pressed", String(this._sound));
    this._soundButton.setAttribute("aria-label", this._sound ? "Mute sound" : "Turn sound on");
    this._soundButton.replaceChildren(icon(this._sound ? ICONS.soundOn : ICONS.soundOff));
    SPEEDS.forEach((s, i) => this._speedButtons[i].setAttribute("aria-pressed", String(s === this._speed)));
  }

  _key(event) {
    if (!this._data || event.target !== document.body || event.metaKey || event.ctrlKey || event.altKey) return;
    if (event.code === "Space") this._toggle();
    else if (event.code === "ArrowRight") event.shiftKey ? this._jumpEpisode(1) : this._jumpStep(1);
    else if (event.code === "KeyM") this._toggleSound();
    else if (event.code === "ArrowLeft") event.shiftKey ? this._jumpEpisode(-1) : this._jumpStep(-1);
    else return;
    event.preventDefault();
  }
}
