// <indah-x-hanoi-board>: the Tower of Hanoi board as one SVG (ADR-0006, ADR-0007).
//
// Props (set as properties by indah's web-component bridge, ADR-0039):
//   rods  - three stacks of disc ids, bottom to top, e.g. [[4, 3], [2], [1, 0]]
//   discs - how many discs the game has
//   move  - {disc, source, target} for the move in flight, or null
// The moving disc is drawn lifted clear above its source rod, with a dashed ghost where it will
// land. Animating the lift, the travel and the descent is the next slice; the board already
// takes every position from the props, so it will not need to change shape.
const NS = "http://www.w3.org/2000/svg";
const VIEW = { w: 560, h: 310, base: 256, rodTop: 66, lift: 30, discH: 28 };
const ROD_X = [100, 280, 460];

function svg(tag, attrs = {}, style = {}) {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  for (const [k, v] of Object.entries(style)) el.style.setProperty(k, v);
  return el;
}

function discWidth(disc, count) {
  const min = 52;
  const max = 172;
  return count < 2 ? max : min + (disc * (max - min)) / (count - 1);
}

export default class HanoiBoard extends HTMLElement {
  constructor() {
    super();
    this._rods = [[], [], []];
    this._discs = 5;
    this._move = null;
    this._queued = false;
    this._root = this.attachShadow({ mode: "open" });
  }

  set rods(value) {
    this._rods = Array.isArray(value) ? value : [[], [], []];
    this._queue();
  }
  set discs(value) {
    this._discs = Number(value) || 5;
    this._queue();
  }
  set move(value) {
    this._move = value && typeof value === "object" ? value : null;
    this._queue();
  }

  connectedCallback() {
    this.style.display = "block";
    this._queue();
  }

  _queue() {
    if (this._queued || !this.isConnected) return;
    this._queued = true;
    requestAnimationFrame(() => {
      this._queued = false;
      this._draw();
    });
  }

  _draw() {
    const { w, h, base, rodTop, lift, discH } = VIEW;
    const root = svg("svg", { viewBox: `0 0 ${w} ${h}`, role: "img" }, { width: "100%", height: "100%" });
    root.setAttribute("aria-label", this._describe());

    root.append(svg("rect", { x: 16, y: base, width: 528, height: 10, rx: 5 }, { fill: "var(--x-base)" }));
    ROD_X.forEach((x, rod) => {
      root.append(svg("rect", { x: x - 4, y: rodTop, width: 8, height: base - rodTop + 2, rx: 4 }, { fill: "var(--x-rod)" }));
      const label = svg("text", { x, y: 293, "text-anchor": "middle", "font-size": 13 }, { fill: "var(--muted)", "font-family": "var(--font-mono)" });
      label.textContent = `rod ${rod}`;
      root.append(label);
    });

    const moving = this._move;
    this._rods.forEach((stack, rod) => {
      stack.forEach((disc, level) => {
        const isMoving = moving && moving.disc === disc;
        const y = isMoving ? lift : base - (level + 1) * discH;
        root.append(this._disc(disc, ROD_X[rod], y, isMoving));
      });
    });

    if (moving) {
      const landed = this._rods[moving.target].length;
      const width = discWidth(moving.disc, this._discs);
      root.append(
        svg(
          "rect",
          { x: ROD_X[moving.target] - width / 2, y: base - (landed + 1) * discH + 2, width, height: discH - 4, rx: 9, "stroke-dasharray": "5 4", "stroke-width": 2 },
          { fill: "none", stroke: "var(--x-gold)" },
        ),
      );
    }
    this._root.replaceChildren(root);
  }

  _disc(disc, cx, y, highlighted) {
    const width = discWidth(disc, this._discs);
    const group = svg("g");
    group.append(
      svg(
        "rect",
        { x: cx - width / 2, y: y + 2, width, height: VIEW.discH - 4, rx: 9, "stroke-width": highlighted ? 3 : 0 },
        { fill: `var(--x-disc-${disc % 5})`, stroke: highlighted ? "var(--text)" : "none" },
      ),
    );
    const label = svg("text", { x: cx, y: y + VIEW.discH / 2 + 5, "text-anchor": "middle", "font-size": 13, "font-weight": 500 }, { fill: "#0b1020", "font-family": "var(--font-mono)" });
    label.textContent = String(disc);
    group.append(label);
    return group;
  }

  _describe() {
    const parts = this._rods.map((stack, rod) => `rod ${rod} holds ${stack.length ? "discs " + stack.join(", ") : "no discs"}`);
    const m = this._move;
    return parts.join("; ") + (m ? `. Disc ${m.disc} is moving from rod ${m.source} to rod ${m.target}.` : ".");
  }
}
