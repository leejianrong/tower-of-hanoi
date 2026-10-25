// <indah-x-explore-pie>: epsilon as a pie, with the slice the agent just used lit (ADR-0006).
//
// Props: epsilon (0..1, the chance of exploring) and explore (true when this step explored).
// The slice for the decision taken is full colour and lifted out; the other one is dimmed.
const NS = "http://www.w3.org/2000/svg";
const C = 90;
const R = 80;

function svg(tag, attrs = {}, style = {}) {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  for (const [k, v] of Object.entries(style)) el.style.setProperty(k, v);
  return el;
}

function point(fraction) {
  const angle = fraction * 2 * Math.PI - Math.PI / 2;
  return [C + R * Math.cos(angle), C + R * Math.sin(angle)];
}

function wedge(from, to) {
  if (to - from >= 0.9999) return `M ${C - R} ${C} A ${R} ${R} 0 1 1 ${C + R} ${C} A ${R} ${R} 0 1 1 ${C - R} ${C} Z`;
  const [x1, y1] = point(from);
  const [x2, y2] = point(to);
  return `M ${C} ${C} L ${x1.toFixed(2)} ${y1.toFixed(2)} A ${R} ${R} 0 ${to - from > 0.5 ? 1 : 0} 1 ${x2.toFixed(2)} ${y2.toFixed(2)} Z`;
}

export default class ExplorePie extends HTMLElement {
  constructor() {
    super();
    this._epsilon = 1;
    this._explore = false;
    this._queued = false;
    this._root = this.attachShadow({ mode: "open" });
  }

  set epsilon(value) {
    this._epsilon = Math.min(Math.max(Number(value) || 0, 0), 1);
    this._queue();
  }
  set explore(value) {
    this._explore = Boolean(value);
    this._queue();
  }

  connectedCallback() {
    // The pie sizes itself: the SVG fills its host, so the host must not fill the card.
    this.style.display = "block";
    this.style.width = "150px";
    this.style.height = "150px";
    this.style.margin = "0 auto";
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
    const e = this._epsilon;
    const exploring = this._explore;
    const percent = (v) => `${(v * 100).toFixed(1)}%`;
    const root = svg("svg", { viewBox: "0 0 180 180", role: "img" }, { width: "100%", height: "100%", overflow: "visible" });
    root.setAttribute(
      "aria-label",
      `Epsilon pie: ${percent(e)} explore, ${percent(1 - e)} exploit. The agent is ${exploring ? "exploring" : "exploiting"}.`,
    );

    const defs = svg("defs");
    const filter = svg("filter", { id: "glow", x: "-30%", y: "-30%", width: "160%", height: "160%" });
    filter.append(svg("feGaussianBlur", { stdDeviation: 5, result: "blur" }));
    const merge = svg("feMerge");
    merge.append(svg("feMergeNode", { in: "blur" }), svg("feMergeNode", { in: "SourceGraphic" }));
    filter.append(merge);
    defs.append(filter);
    root.append(defs);

    const slices = [
      { from: 0, to: e, colour: "var(--x-explore)", lit: exploring },
      { from: e, to: 1, colour: "var(--x-exploit)", lit: !exploring },
    ];
    for (const s of slices) {
      if (s.to - s.from <= 0) continue;
      const mid = ((s.from + s.to) / 2) * 2 * Math.PI - Math.PI / 2;
      const shift = s.lit ? `translate(${(5 * Math.cos(mid)).toFixed(1)} ${(5 * Math.sin(mid)).toFixed(1)})` : "";
      const path = svg("path", { d: wedge(s.from, s.to), transform: shift }, { fill: s.colour, opacity: s.lit ? "1" : "0.32" });
      if (s.lit) path.setAttribute("filter", "url(#glow)");
      root.append(path);
    }
    this._root.replaceChildren(root);
  }
}
