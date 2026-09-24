// Settings panel: collapsible sections of sliders, toggles and choices.
// Plain DOM, styled in ui.css. Tab or the ☰ button opens it.

const el = (tag, cls, parent, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  if (parent) parent.appendChild(e);
  return e;
};

export class Panel {
  constructor(root, toggleButton, body) {
    this.root = root;
    this.body = body;
    this.controls = new Map();
    this.onToggle = null;
    toggleButton.addEventListener('click', () => this.toggle());
    // keep panel interaction from reaching the game
    for (const ev of ['mousedown', 'wheel']) root.addEventListener(ev, (e) => e.stopPropagation());
    root.addEventListener('keydown', (e) => { if (e.code !== 'Tab' && e.code !== 'Escape') e.stopPropagation(); });
  }

  get open() { return !this.root.classList.contains('collapsed'); }

  toggle(force) {
    const open = force === undefined ? !this.open : force;
    this.root.classList.toggle('collapsed', !open);
    this.onToggle?.(open);
  }

  header(title, subtitle) {
    const h = el('div', 'pn-header', this.body);
    el('div', 'pn-title', h, title);
    if (subtitle) el('div', 'pn-sub', h, subtitle);
    return h;
  }

  section(title, { open = false, icon = '' } = {}) {
    const sec = el('section', 'pn-section' + (open ? ' open' : ''), this.body);
    const head = el('button', 'pn-section-head', sec);
    el('span', 'pn-icon', head, icon);
    el('span', 'pn-section-title', head, title);
    el('span', 'pn-chevron', head, '›');
    const content = el('div', 'pn-section-body', sec);
    head.addEventListener('click', () => sec.classList.toggle('open'));
    return content;
  }

  slider(parent, { id, label, min, max, step = 0.01, value, format = (v) => v.toFixed(2), onInput, hint }) {
    const row = el('label', 'pn-row pn-slider', parent);
    const top = el('div', 'pn-row-top', row);
    el('span', 'pn-label', top, label);
    const out = el('span', 'pn-value', top, format(value));
    const input = el('input', '', row);
    input.type = 'range';
    input.min = min; input.max = max; input.step = step; input.value = value;
    if (hint) row.title = hint;
    const paint = () => {
      const t = (input.value - min) / (max - min);
      input.style.setProperty('--fill', `${(t * 100).toFixed(1)}%`);
      out.textContent = format(+input.value);
    };
    input.addEventListener('input', () => { paint(); onInput?.(+input.value); });
    paint();
    const ctl = { row, input, get value() { return +input.value; }, set(v, fire = false) { input.value = v; paint(); if (fire) onInput?.(+input.value); } };
    if (id) this.controls.set(id, ctl);
    return ctl;
  }

  toggleRow(parent, { id, label, value, onChange, hint }) {
    const row = el('label', 'pn-row pn-toggle', parent);
    el('span', 'pn-label', row, label);
    const input = el('input', '', row);
    input.type = 'checkbox';
    input.checked = !!value;
    el('span', 'pn-switch', row);
    if (hint) row.title = hint;
    input.addEventListener('change', () => onChange?.(input.checked));
    const ctl = { row, input, get value() { return input.checked; }, set(v, fire = false) { input.checked = !!v; if (fire) onChange?.(input.checked); } };
    if (id) this.controls.set(id, ctl);
    return ctl;
  }

  choice(parent, { id, label, options, value, onChange }) {
    const row = el('div', 'pn-row pn-choice', parent);
    el('span', 'pn-label', row, label);
    const group = el('div', 'pn-seg', row);
    const buttons = options.map(([val, text]) => {
      const b = el('button', 'pn-seg-btn' + (val === value ? ' on' : ''), group, text);
      b.addEventListener('click', () => { set(val, true); });
      return [val, b];
    });
    const set = (v, fire = false) => {
      for (const [val, b] of buttons) b.classList.toggle('on', val === v);
      if (fire) onChange?.(v);
    };
    const ctl = { row, set };
    if (id) this.controls.set(id, ctl);
    return ctl;
  }

  buttons(parent, list) {
    const row = el('div', 'pn-row pn-buttons', parent);
    for (const [text, fn] of list) {
      const b = el('button', 'pn-btn', row, text);
      b.addEventListener('click', fn);
    }
    return row;
  }

  keys(parent, list) {
    const grid = el('div', 'pn-keys', parent);
    for (const [k, what] of list) {
      const kk = el('div', 'pn-key', grid);
      for (const part of k.split(' ')) el('kbd', '', kk, part);
      el('div', 'pn-key-what', grid, what);
    }
    return grid;
  }

  note(parent, text) { return el('div', 'pn-note', parent, text); }

  get(id) { return this.controls.get(id); }
}
