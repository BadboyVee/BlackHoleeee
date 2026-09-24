// Keyboard + mouse state with pointer lock.
//
// Keys are tracked by KeyboardEvent.code (layout independent). `pressed()`
// reports a key once per physical press; `down()` while it is held.

export class Input {
  constructor(dom, { ignore = () => false } = {}) {
    this.dom = dom;
    this.held = new Set();
    this.edges = new Set();
    this.mouseDX = 0;
    this.mouseDY = 0;
    this.wheel = 0;
    this.locked = false;
    this.enabled = true;
    this.onLockChange = null;

    addEventListener('keydown', (e) => {
      if (!this.enabled || isTyping(e)) return;
      if (!this.held.has(e.code)) this.edges.add(e.code);
      this.held.add(e.code);
      if (['Space', 'Tab', 'ArrowUp', 'ArrowDown'].includes(e.code) || (this.locked && e.ctrlKey)) e.preventDefault();
    });
    addEventListener('keyup', (e) => { this.held.delete(e.code); });
    addEventListener('blur', () => { this.held.clear(); });
    dom.addEventListener('mousedown', (e) => {
      if (ignore(e)) return;
      if (!this.locked && e.button === 0) dom.requestPointerLock?.();
    });
    addEventListener('mousemove', (e) => {
      if (!this.locked) return;
      this.mouseDX += e.movementX || 0;
      this.mouseDY += e.movementY || 0;
    });
    addEventListener('wheel', (e) => { if (this.locked) this.wheel += Math.sign(e.deltaY); }, { passive: true });
    document.addEventListener('pointerlockchange', () => {
      this.locked = document.pointerLockElement === dom;
      this.held.clear();
      this.onLockChange?.(this.locked);
    });
  }

  down(code) { return this.held.has(code); }
  pressed(code) { return this.edges.has(code); }
  axis(neg, pos) { return (this.down(pos) ? 1 : 0) - (this.down(neg) ? 1 : 0); }

  /** call once per frame after the game has read the input */
  endFrame() {
    this.edges.clear();
    this.mouseDX = 0;
    this.mouseDY = 0;
    this.wheel = 0;
  }

  unlock() { if (this.locked) document.exitPointerLock?.(); }
}

function isTyping(e) {
  const t = e.target;
  return t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable) && t.type !== 'range';
}
