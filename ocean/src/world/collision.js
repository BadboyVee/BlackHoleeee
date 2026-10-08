// Static collision world for the walkable scene: terrain heightfield plus
// boxes (decks, walls, crates, hulls) and vertical cylinders (posts, trunks).
//
// Boxes are oriented about y. A walkable box is something you can stand on
// (its top face); a solid box also blocks horizontal movement when it overlaps
// the body's vertical span above the step height.

export class CollisionWorld {
  constructor(island) {
    this.island = island;
    this.boxes = [];
    this.cylinders = [];
    this.cell = 8;
    this.grid = new Map();
  }

  _key(i, j) { return i * 73856093 ^ j * 19349663; }

  _insert(item, x0, z0, x1, z1) {
    const c = this.cell;
    for (let i = Math.floor(x0 / c); i <= Math.floor(x1 / c); i++) {
      for (let j = Math.floor(z0 / c); j <= Math.floor(z1 / c); j++) {
        const k = this._key(i, j);
        let list = this.grid.get(k);
        if (!list) this.grid.set(k, list = []);
        list.push(item);
      }
    }
  }

  /**
   * @param {object} b  center x/z, bottom y0, top y1, half sizes hx/hz, yaw (rad)
   */
  addBox({ x, z, y0, y1, hx, hz, yaw = 0, walkable = true, solid = true, tag = null }) {
    const box = { type: 'box', x, z, y0, y1, hx, hz, c: Math.cos(yaw), s: Math.sin(yaw), walkable, solid, tag };
    const r = Math.hypot(hx, hz);
    this.boxes.push(box);
    this._insert(box, x - r, z - r, x + r, z + r);
    return box;
  }

  addCylinder({ x, z, y0, y1, r, walkable = false, tag = null }) {
    const cyl = { type: 'cyl', x, z, y0, y1, r, walkable, solid: true, tag };
    this.cylinders.push(cyl);
    this._insert(cyl, x - r, z - r, x + r, z + r);
    return cyl;
  }

  /** helper: box from a THREE.Object3D-like transform (center + size + yaw) */
  addBoxFromCenter(cx, cy, cz, sx, sy, sz, yaw = 0, opts = {}) {
    return this.addBox({ x: cx, z: cz, y0: cy - sy / 2, y1: cy + sy / 2, hx: sx / 2, hz: sz / 2, yaw, ...opts });
  }

  _near(x, z, r = 0) {
    const c = this.cell, out = new Set();
    for (let i = Math.floor((x - r) / c); i <= Math.floor((x + r) / c); i++) {
      for (let j = Math.floor((z - r) / c); j <= Math.floor((z + r) / c); j++) {
        const list = this.grid.get(this._key(i, j));
        if (list) for (const it of list) out.add(it);
      }
    }
    return out;
  }

  _local(box, x, z) {
    const dx = x - box.x, dz = z - box.z;
    return [dx * box.c + dz * box.s, -dx * box.s + dz * box.c];
  }

  terrainHeight(x, z) { return this.island.heightAt(x, z); }

  /**
   * Height of the surface the feet rest on: the terrain or the highest
   * walkable top at or below footY + step.
   */
  groundAt(x, z, footY = Infinity, step = 0.5, radius = 0.2) {
    let g = this.terrainHeight(x, z);
    let surface = null;
    for (const it of this._near(x, z, radius)) {
      if (!it.walkable) continue;
      let inside;
      if (it.type === 'box') {
        const [lx, lz] = this._local(it, x, z);
        inside = Math.abs(lx) <= it.hx + radius * 0.5 && Math.abs(lz) <= it.hz + radius * 0.5;
      } else {
        inside = Math.hypot(x - it.x, z - it.z) <= it.r + radius * 0.5;
      }
      if (inside && it.y1 <= footY + step && it.y1 > g) { g = it.y1; surface = it; }
    }
    return { y: g, surface };
  }

  /**
   * Push a vertical capsule (approximated as a cylinder of `radius` from
   * footY + step to headY) out of solid geometry. Mutates pos (x, z).
   */
  resolve(pos, radius, footY, headY, step = 0.45) {
    for (let iter = 0; iter < 3; iter++) {
      let moved = false;
      for (const it of this._near(pos.x, pos.z, radius + 1)) {
        if (!it.solid) continue;
        if (it.y1 <= footY + step || it.y0 >= headY) continue;
        if (it.type === 'box') {
          const [lx, lz] = this._local(it, pos.x, pos.z);
          const px = it.hx + radius - Math.abs(lx), pz = it.hz + radius - Math.abs(lz);
          if (px > 0 && pz > 0) {
            // push out along the axis of least penetration (box local frame)
            let ox = 0, oz = 0;
            if (px < pz) ox = Math.sign(lx || 1) * px; else oz = Math.sign(lz || 1) * pz;
            pos.x += ox * it.c - oz * it.s;
            pos.z += ox * it.s + oz * it.c;
            moved = true;
          }
        } else {
          const dx = pos.x - it.x, dz = pos.z - it.z;
          const d = Math.hypot(dx, dz), m = it.r + radius;
          if (d < m) {
            const k = d > 1e-5 ? (m - d) / d : 0;
            pos.x += dx * k; pos.z += dz * k;
            if (d <= 1e-5) pos.x += m;
            moved = true;
          }
        }
      }
      if (!moved) break;
    }
    return pos;
  }

  /** lowest solid ceiling above y at (x, z) (for jumping under decks) */
  ceilingAt(x, z, y) {
    let c = Infinity;
    for (const it of this._near(x, z, 0.3)) {
      if (!it.solid || it.y0 < y) continue;
      if (it.type === 'box') {
        const [lx, lz] = this._local(it, x, z);
        if (Math.abs(lx) <= it.hx && Math.abs(lz) <= it.hz) c = Math.min(c, it.y0);
      } else if (Math.hypot(x - it.x, z - it.z) <= it.r) c = Math.min(c, it.y0);
    }
    return c;
  }
}
