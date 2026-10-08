// On-screen controls for phones and tablets.
//
// A move stick appears under the left thumb (drag past its ring to run), a
// drag anywhere else turns the view, and buttons on the right jump / go up,
// go down, use (E: take the helm, leave the boat) and toggle free fly. They
// drive the same Input as the keyboard and mouse: the stick as analog
// W/A/S/D, the buttons as held keys.

const RING = 56;          // px the knob travels from the stick's centre
const DEAD = 0.12;        // stick dead zone, as a fraction of the ring
const RUN = 1.35;         // drag this many rings from the centre to run
const TURN = 2.6;         // radians a drag across the screen's short side turns
const SENS = 0.0021;      // the player's default look sensitivity (per mouse count)
const BUTTONS = [
  { code: 'KeyG', label: 'Fly', cls: 'fly' },
  { code: 'KeyE', label: 'E', cls: 'use' },
  { code: 'KeyC', label: '▼', cls: 'down' },
  { code: 'Space', label: '▲', cls: 'up' },
];

const add = (parent, tag, cls) => {
  const e = document.createElement(tag);
  e.className = cls;
  parent.appendChild(e);
  return e;
};

export class TouchControls {
  constructor(input, canvas) {
    this.input = input;
    this.onStart = null;      // called once, when touch controls switch on
    this.stick = null;        // { id, x0, y0 } of the finger on the stick
    this.look = null;         // { id, x, y } of the finger turning the view

    const el = this.el = document.createElement('div');
    el.id = 'touch';
    el.hidden = true;
    this.base = add(el, 'div', 't-stick');
    this.knob = add(this.base, 'div', 't-knob');
    this.base.hidden = true;
    for (const b of BUTTONS) {
      const btn = add(el, 'button', `t-btn t-${b.cls}`);
      btn.textContent = b.label;
      btn.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        btn.setPointerCapture?.(e.pointerId);
        this.activate();
        input.edges.add(b.code);
        input.touchHeld.add(b.code);
        btn.classList.add('on');
      });
      const up = () => { input.touchHeld.delete(b.code); btn.classList.remove('on'); };
      btn.addEventListener('pointerup', up);
      btn.addEventListener('pointercancel', up);
      btn.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    const full = add(el, 'button', 't-full');
    full.textContent = '⛶';
    full.title = 'Full screen';
    full.addEventListener('click', () => {
      if (document.fullscreenElement) { document.exitFullscreen?.(); return; }
      document.documentElement.requestFullscreen?.()
        .then(() => screen.orientation?.lock?.('landscape'))
        .catch(() => {});
    });
    document.body.appendChild(el);

    canvas.style.touchAction = 'none';
    canvas.addEventListener('pointerdown', (e) => this._down(e));
    canvas.addEventListener('pointermove', (e) => this._move(e));
    canvas.addEventListener('pointerup', (e) => this._up(e));
    canvas.addEventListener('pointercancel', (e) => this._up(e));
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    if (matchMedia('(pointer: coarse)').matches) this.activate();
  }

  activate() {
    if (this.input.touch) return;
    this.input.touch = true;
    this.el.hidden = false;
    this.onStart?.();
  }

  _down(e) {
    if (e.pointerType !== 'touch') return;
    e.preventDefault();
    this.activate();
    e.target.setPointerCapture?.(e.pointerId);
    if (!this.stick && e.clientX < innerWidth * 0.45) {
      this.stick = { id: e.pointerId, x0: e.clientX, y0: e.clientY };
      this.base.style.left = `${e.clientX}px`;
      this.base.style.top = `${e.clientY}px`;
      this.base.hidden = false;
      this._stickTo(e.clientX, e.clientY);
    } else if (!this.look) {
      this.look = { id: e.pointerId, x: e.clientX, y: e.clientY };
    }
  }

  _move(e) {
    if (this.stick && e.pointerId === this.stick.id) {
      this._stickTo(e.clientX, e.clientY);
    } else if (this.look && e.pointerId === this.look.id) {
      const k = TURN / (Math.min(innerWidth, innerHeight) * SENS);
      this.input.mouseDX += (e.clientX - this.look.x) * k;
      this.input.mouseDY += (e.clientY - this.look.y) * k;
      this.look.x = e.clientX;
      this.look.y = e.clientY;
    }
  }

  _up(e) {
    if (this.stick && e.pointerId === this.stick.id) {
      this.stick = null;
      this.base.hidden = true;
      this.input.analog = {};
      this.input.touchHeld.delete('ShiftLeft');
    } else if (this.look && e.pointerId === this.look.id) {
      this.look = null;
    }
  }

  _stickTo(x, y) {
    const s = this.stick;
    let dx = (x - s.x0) / RING, dy = (y - s.y0) / RING;
    const m = Math.hypot(dx, dy);
    const run = m > RUN;
    if (m > 1) { dx /= m; dy /= m; }
    this.knob.style.transform = `translate(${dx * RING}px, ${dy * RING}px)`;
    this.base.classList.toggle('run', run);
    // past the dead zone, rescaled so the ring's edge is still full speed
    const r = Math.min(m, 1);
    const g = r < DEAD ? 0 : (r - DEAD) / (1 - DEAD) / r;
    const fx = dx * g, fy = -dy * g;
    this.input.analog = { KeyD: Math.max(fx, 0), KeyA: Math.max(-fx, 0), KeyW: Math.max(fy, 0), KeyS: Math.max(-fy, 0) };
    if (run) this.input.touchHeld.add('ShiftLeft');
    else this.input.touchHeld.delete('ShiftLeft');
  }
}
