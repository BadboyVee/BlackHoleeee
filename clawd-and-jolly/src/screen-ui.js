// The laptop screen: a Claude Code session drawn without a single glyph.
// Words are rounded bars, the mascot is drawn from the same 18x5 sprite as the 3D Clawd.
import { SPRITE, SPRITE_W, SPRITE_H } from './clawd.js';

export const UI_W = 2560, UI_H = 1600;
export const CELL_W = 16, CELL_H = 34;
const BG = '#151513', ORANGE = '#d77757', CREAM = '#e9e6dc', GREY = '#8f8d86', DIM = '#55534e';

// Jolly as a tiny sprite for the last shot (blue, pink cheeks, two eyes)
export const JOLLY_SPRITE = [
  '....######....',
  '..##########..',
  '.###e####e###.',
  '.#p########p#.',
  '..##########..',
  '...##....##...',
];

// where the Clawd sprite sits on the screen (UI pixels), one sprite pixel = SP x SP
export const SPRITE_POS = { x: 112, y: 150, px: 16 };

function rng(seed) { let s = seed; return () => ((s = (s * 16807) % 2147483647) / 2147483647); }

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

// a "line of text": words as bars on the cell grid
function textLine(ctx, col, row, words, color, rnd, opts = {}) {
  let x = col * CELL_W;
  const y = row * CELL_H + CELL_H * 0.28;
  const h = CELL_H * (opts.h ?? 0.46);
  ctx.fillStyle = color;
  for (const w of words) {
    const len = typeof w === 'number' ? w : 2 + Math.floor(rnd() * 7);
    roundRect(ctx, x + 1, y, len * CELL_W - 2, h, 3);
    ctx.fill();
    x += (len + 1) * CELL_W;
  }
  return x / CELL_W;
}
function para(ctx, col, row, cols, color, rnd) {
  const words = [];
  let used = 0;
  while (used < cols) { const l = 2 + Math.floor(rnd() * 8); if (used + l > cols) break; words.push(l); used += l + 1; }
  return textLine(ctx, col, row, words, color, rnd);
}
function chevron(ctx, col, row, color) {
  const x = col * CELL_W + 3, y = row * CELL_H + CELL_H * 0.26, h = CELL_H * 0.5;
  ctx.strokeStyle = color; ctx.lineWidth = 3.2; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 8, y + h / 2); ctx.lineTo(x, y + h); ctx.stroke();
}
function dot(ctx, col, row, color) {
  ctx.fillStyle = color;
  ctx.beginPath(); ctx.arc(col * CELL_W + 8, row * CELL_H + CELL_H * 0.5, 5.5, 0, Math.PI * 2); ctx.fill();
}
function hook(ctx, col, row, color) {
  const x = col * CELL_W + 6, y = row * CELL_H + 4;
  ctx.strokeStyle = color; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + CELL_H * 0.5); ctx.lineTo(x + 10, y + CELL_H * 0.5); ctx.stroke();
}

export function drawSprite(ctx, sprite, x, y, px, colors, mask) {
  let i = 0;
  for (let r = 0; r < sprite.length; r++) {
    for (let c = 0; c < sprite[r].length; c++) {
      const ch = sprite[r][c];
      if (ch === '.') continue;
      const col = colors[ch];
      const idx = i++;
      if (!col) continue;
      if (mask && !mask(r, c, idx)) continue;
      ctx.fillStyle = col;
      ctx.fillRect(x + c * px, y + r * px, px, px);
    }
  }
}

// state: { cursor: 0..1, spriteMask(r,c) -> bool, showJolly: 0..1, typed: n chars in prompt, scroll }
export function drawTerminal(ctx, state = {}) {
  const rnd = rng(42);
  ctx.save();
  // desktop + window chrome
  const g = ctx.createLinearGradient(0, 0, UI_W, UI_H);
  g.addColorStop(0, '#2b2622'); g.addColorStop(1, '#16191d');
  ctx.fillStyle = g; ctx.fillRect(0, 0, UI_W, UI_H);
  ctx.fillStyle = BG;
  roundRect(ctx, 0, 0, UI_W, UI_H, 0); ctx.fill();
  ctx.fillStyle = '#1f1e1c'; ctx.fillRect(0, 0, UI_W, 52);
  [['#ff5f57', 30], ['#febc2e', 62], ['#28c840', 94]].forEach(([c, x]) => { ctx.fillStyle = c; ctx.beginPath(); ctx.arc(x, 26, 9, 0, Math.PI * 2); ctx.fill(); });
  ctx.fillStyle = '#3a3936'; roundRect(ctx, UI_W / 2 - 160, 18, 320, 16, 8); ctx.fill();

  // welcome box
  ctx.strokeStyle = ORANGE; ctx.lineWidth = 3;
  roundRect(ctx, 64, 92, 1300, 236, 16); ctx.stroke();
  const S = SPRITE_POS;
  drawSprite(ctx, SPRITE, S.x, S.y, S.px, { '#': ORANGE, a: ORANGE, l: ORANGE, e: null }, state.spriteMask);
  if (state.showJolly) {
    ctx.globalAlpha = state.showJolly;
    drawSprite(ctx, JOLLY_SPRITE, S.x + 316, S.y - 16, 16, { '#': '#3c8cff', p: '#f2a0a4', e: null });
    ctx.globalAlpha = 1;
  }
  textLine(ctx, 46, 4, [3, 7, 2, 6, 4], CREAM, rnd);
  textLine(ctx, 46, 5.3, [5, 3, 4, 2, 9, 3], GREY, rnd);
  textLine(ctx, 46, 6.6, [2, 14, 3, 8], DIM, rnd);

  // conversation
  let row = 11 - (state.scroll || 0);
  chevron(ctx, 5, row, GREY); para(ctx, 7, row, 70, CREAM, rnd); row += 1; para(ctx, 7, row, 38, CREAM, rnd); row += 2;
  dot(ctx, 5, row, CREAM); para(ctx, 7, row, 92, CREAM, rnd); row += 1; para(ctx, 7, row, 64, CREAM, rnd); row += 2;
  dot(ctx, 5, row, '#4fb35a'); textLine(ctx, 7, row, [6], CREAM, rnd); textLine(ctx, 14, row, [18], GREY, rnd); row += 1;
  hook(ctx, 6, row, DIM); textLine(ctx, 9, row, [7, 3, 4, 2], GREY, rnd); row += 1;
  // diff block
  const diff = [['ctx', 40], ['ctx', 28], ['del', 34], ['del', 22], ['add', 46], ['add', 38], ['add', 30], ['ctx', 18], ['ctx', 26]];
  for (const [kind, len] of diff) {
    if (kind !== 'ctx') {
      ctx.fillStyle = kind === 'add' ? '#173a22' : '#43191c';
      ctx.fillRect(9 * CELL_W, row * CELL_H + 1, 104 * CELL_W, CELL_H - 2);
    }
    textLine(ctx, 9, row, [3], DIM, rnd);
    const tok = [];
    let used = 0; while (used < len) { const l = 2 + Math.floor(rnd() * 7); tok.push(l); used += l + 1; }
    let x = 14 + (kind === 'ctx' ? 2 : 2);
    tok.forEach((l, i) => {
      const c = kind === 'add' ? (i % 3 === 0 ? '#9fdca8' : '#6fbf7c') : kind === 'del' ? (i % 3 === 0 ? '#f0a0a0' : '#d27272') : (i % 4 === 0 ? '#c792ea' : i % 4 === 1 ? '#82aaff' : GREY);
      x = textLine(ctx, x, row, [l], c, rnd);
    });
    row += 1;
  }
  row += 1;
  dot(ctx, 5, row, CREAM); para(ctx, 7, row, 84, CREAM, rnd); row += 1; para(ctx, 7, row, 52, CREAM, rnd); row += 2;
  dot(ctx, 5, row, '#4fb35a'); textLine(ctx, 7, row, [4], CREAM, rnd); textLine(ctx, 12, row, [11], GREY, rnd); row += 1;
  hook(ctx, 6, row, DIM); textLine(ctx, 9, row, [5, 2, 6], GREY, rnd); row += 2;
  dot(ctx, 5, row, CREAM); para(ctx, 7, row, 76, CREAM, rnd); row += 1;

  // input box
  const iy = 39.5 * CELL_H;
  ctx.strokeStyle = '#5c5a55'; ctx.lineWidth = 2.5;
  roundRect(ctx, 64, iy, UI_W - 128, CELL_H * 1.9, 12); ctx.stroke();
  const prow = 39.5 + 0.45;
  chevron(ctx, 6, prow, CREAM);
  const typed = state.typed || 0;
  let cx = 8;
  if (typed > 0) cx = textLine(ctx, 8, prow, [Math.min(typed, 5), ...(typed > 6 ? [Math.min(typed - 6, 8)] : [])], CREAM, rnd);
  if ((state.cursor ?? 1) > 0) {
    ctx.globalAlpha = state.cursor ?? 1;
    ctx.fillStyle = CREAM;
    ctx.fillRect(cx * CELL_W, prow * CELL_H + 2, CELL_W, CELL_H - 4);
    ctx.globalAlpha = 1;
  }
  textLine(ctx, 5, 42, [1, 3, 2, 9], DIM, rnd, { h: 0.38 });
  textLine(ctx, 140, 42, [6, 4], DIM, rnd, { h: 0.38 });
  ctx.restore();
}

// UI-pixel position (x, y) of the centre of sprite pixel (row, col)
export function spritePixelUI(r, c) {
  return { x: SPRITE_POS.x + (c + 0.5) * SPRITE_POS.px, y: SPRITE_POS.y + (r + 0.5) * SPRITE_POS.px };
}
export const CURSOR_UI = { x: 8.5 * CELL_W, y: (39.95 + 0.5) * CELL_H };
export { SPRITE_W, SPRITE_H };
