# Launch-film playbook

How to make a premium launch film or "AI edit" for veee (GitHub `badboyvee`). It's distilled from
studying reference films frame by frame ([references/](references/)) and from the films already
made in this repo. Read this before planning any video. The reference studies hold the evidence
behind each rule.

---

## 0. Who it's for

- **The bar the user sets:** "Make it beautiful, GO ALL OUT", "No mistakes", "as good as the video I sent".
  They notice low quality (they rejected a 30 fps, grainy, low-bitrate cut) and they notice music
  that doesn't flow.
- **They want it fast.** They'll ask "why the delay". Send a status line while working, and deliver
  as soon as the checks pass.
- **They watch on a phone,** with files passed through WhatsApp. Deliver an **MP4 via SendUserFile
  (limit 30 MiB)**, 1080p **60 fps**, H.264, AAC 48 kHz.
- **Signature:** their AI edit closed on **"made by veee"** (Instrument Serif italic, typed on the last hit). Offer it as the sign-off on their videos.
- **Recurring subjects:** AI model launches (Claude, Gemini, GPT, Grok and their leaders), punchy
  statement lines ("A world without stress.", "AI takes over."). Spell names exactly as they're
  publicly known, and fix their typos quietly (e.g. "Dennis Hannabis" → Demis Hassabis).

---

## 1. Start from the music

1. **Pick or receive the track first.** Measure BPM and bar length: `bar = 240 / BPM` s
   (124.6 BPM → 1.926 s; 120 → 2.000 s; 128 → 1.875 s). Lock the grid to the claps/snare
   (beats 2 & 4); kick onsets in a band-pass are biased late. Tool: [`tools/`](tools/).
2. **Map the arrangement:** intro (no bass), drop, breaks, risers, final hit, end. Each of these
   gets a picture event.
3. **One idea per bar.** About 30 s ≈ 16 bars at ~125 BPM. Two halves of 8 bars, with a break at the
   midpoint that opens chapter 2.
4. **To lengthen a track, insert whole loop phrases.** For a 4-bar loop, insert exactly 4 bars and
   join on downbeats. Two bars works **only** if the repeated bars keep the chord flow natural, so
   check the bass note per bar first (e.g. D♭ → B♭ minor was smooth). A beat-locked extension
   keeps every later cut on its beat.
5. **Joins:** align the incoming hit by cross-correlation (±20 ms), equal-power crossfade 12 ms
   (40 ms into a restart). Verify each join by its onset pattern against the source's own
   downbeat, with no sample-step spike (no click).
6. **Master:** −12 to −14 LUFS for social, **true peak ≤ −1 dBTP** (the Tender reference clips at +0.3).
   Keep the source's loudness if you're editing its song.

## 2. Beat sheet template (16 bars)

Times at 124.6 BPM; for any other tempo use `t = d0 + (bar − 1) · 240/BPM`.

| Bar | Role | Picture | Text rhythm |
|---:|---|---|---|
| 1 | Hook (quiet intro) | logo → words on white | one word/phrase per chord stab, hard swaps |
| 2 | Promise | the line holds 1 beat, then the camera dives into it | — |
| 3 | **Drop = reveal** | match-cut from type/shape to the product/subject | 1–4 words as the subject settles |
| 4 | Use case / metaphor | show the claim (Tender: a day→night sky for "24/7") | a short line on the object's plane |
| 5 | Scale | many objects in a void | number on beat 2, noun on 3, verb on 4 |
| 6 | Craft | objects regroup, a dive to the next detail | — |
| 7 | Brand echo | objects form the logo shape | silence (let it breathe) |
| 8 | **Break** | macro + strobe on the stutter hits | — |
| 9 | Chapter 2 | kinetic headline → logo lockup | scattered words, each with an ease-out |
| 10–14 | Feature montage | one feature per bar, UI in 3D or zoom-through | UI micro-events on 8ths |
| 15 | Payoff | three-word triad | words on beats 1, 2, 3 |
| 16 | Sign-off | tagline → logo → inverse flash on the final hit → tags | "made by veee" at the very end |

## 3. Timing rules

- **Cut on downbeats, 0–1 frame early** (−8 to −43 ms measured for hard cuts). At 60 fps, cut 1–2 frames early. Multi-frame transitions start early enough to *resolve* on the beat.
- **Words land on beats or on the stab's "and",** never at random times. Closing words should be
  frame-tight.
- **The flash/strobe is the sound made visible:** one solid frame per stutter hit; put the accent
  colour on one of them.
- **UI micro-changes** (QR swaps, checkbox ticks, typing) run on 8ths or 16ths.
- **Every shot has three phases:**
  1. **impact**, decelerating after the cut (expo-out, e.g. zoom −40% → −1% per frame);
  2. **drift** while the content plays (≈ 1–2% per frame, or a slow roll);
  3. **throw**, accelerating into the next downbeat (expo-in, e.g. +1% → +37% per frame).

```js
// one bar of camera: impact (expo-out) -> drift -> throw (expo-in); u = 0..1 through the bar
const expoOut = t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t);
const expoIn  = t => t <= 0 ? 0 : Math.pow(2, 10 * (t - 1));
function barMove(u, impact = .3, throwAt = .75) {
  if (u < impact)  return .35 * expoOut(u / impact);                                 // fast -> slow
  if (u < throwAt) return .35 + .15 * (u - impact) / (throwAt - impact);              // steady drift
  return .5 + .5 * expoIn((u - throwAt) / (1 - throwAt));                             // slow -> fast
}
```

## 4. Look

- **Palette: white #FFFFFF + ink #111111 + ONE accent family.** Tender's is gold, #9C6A2C → #C88B45
  (with #C68535 for flashes and #E8B16B for warm fields). The accent means "brand" or "done", so
  never use it as decoration. Alternate light and dark fields bar to bar for rhythm.
- **Three type voices:**
  - a serif for promises (Newsreader Display / Instrument Serif / Source Serif 4 Display);
  - mono caps tracked +12–20% for data, states and end tags (Geist Mono / JetBrains Mono);
  - a native-looking sans for UI (Inter / Geist).
- **Sizes at 1080p:**
  - hero serif cap height ≈ **63 px (5.8% of H)**, about a 93 px font;
  - end tags ≥ **38 px caps (3.5% of H)**. The reference's 2.8% is too small on phones.
- **Placement:** single statements dead centre; stacks in a left column positioned so the block sits
  optically centred (~36% of W); text beside a device at a 6% margin; text attached to 3D planes when
  it belongs to the object.
- **Copy:** sentence case, full stops, 1–4 words per beat, parallel triads ("Scan. Send. Settled."),
  concrete numbers.
- **Type moves** (pick 2–3 per film, not all):
  - hard swap on stabs;
  - per-word fade from light grey along a path;
  - mask-rise (5 frames at 25 fps ≈ 0.2 s, ease-out);
  - typeface-flip scramble (sans → mono caps in the accent → serif) for "transformation";
  - typing with a caret;
  - letters exploding into 3D glyphs;
  - colour-by-occlusion (letters take the colour of what passes behind them).
- **Real-world anchors:** native camera QR detection, lock-screen notifications, the home screen.
  They make the product feel shipped.

## 5. Transitions cookbook

| Transition | Recipe |
|---|---|
| **Morph cut** | dive (expo-in) into a shape until it fills the frame (O, dot, ring); on the drop, cut to an object with the same silhouette and pull back (expo-out) |
| Whip | 1–3 frames of strong directional blur (canvas: draw 8–12 offset copies at low alpha, or `filter: blur()` on a layer) |
| Dive-through | zoom into a UI detail (pill, icon, screen) until it fills the frame, then cut inside |
| White-out | bleach to white over 3–4 frames while objects fly at the camera |
| Strobe | solid frames on stutter hits: white, black, white, black, accent, white |
| Glitch swap | one dimmed frame between data states |
| Shatter | Voronoi shards with accent rims flying toward the camera, 0.6 s |
| Inverse flash | 2–3 frames of the logo inverted on the final hit |
| Echo trails | 6–8 stepped copies of a fast object (not smooth blur) for a designed look |

## 6. Production pipeline (works in the cloud container)

- **Rendering:** a canvas-2D or three.js page driven by headless Chromium (Playwright at
  `/opt/node22/lib/node_modules/playwright`); `render(scene, t)` per frame → JPEG q .95. Run 4 parallel
  workers on frame ranges (≈ 0.08 s per frame at 1080p for 2D).
- **Fonts:** npm `@fontsource/*` packages (the registry is reachable). Wikimedia and similar hosts
  return 403, so ask the user for photos.
- **Photos:** Real-ESRGAN via the `realesrgan-ncnn-py` wheel on CPU (`gpuid=-1`, model 4;
  needs `apt-get install libomp5-18`). Blend 45–70% with a Lanczos upscale and unsharp 1.0/40/2.
  Pad headroom with a blurred extension when the crop is tight.
- **Logos:** trace with `potracer` (pure Python) → SVG path → `Path2D` with `evenodd`.
- **Assembly:** symlink frames into a sequence; source footage at its native time with
  **`floor((src + T − t0) · fps + 1e-6)`, never `round`.** Rounding shows the first frame after a
  cut for 1/60 s, a visible flash.
- **Encode (delivery ≤ 30 MiB):**
  - two-pass libx264 `veryslow`, `aq-mode=3`, `psy-rd=1.0,0.15`, `deblock=-1,-1`;
  - bitrate ≈ `(29.6 MB · 8 / duration) − 192k` (≈ 4.3 Mbps for 53 s, 4.0 for 56 s at 1080p60);
  - AAC 192k at 48 kHz, `+faststart`, bt709 tags.
- **Analysis tools for reference videos:** see [`tools/README.md`](tools/README.md).

## 7. QA before sending (every time)

- [ ] **Text up close:** crop every typed line at 100%. Per-letter animation must place letter *i* at
      `width(text[0..i]) − width(text[i])`. Plain prefix widths break kerning ("6.1Sol", "GPT -").
- [ ] **Group fades work:** drawing helpers multiply `globalAlpha` (`*=`), never overwrite it.
- [ ] **No one-frame flashes:** scan the decoded file for frames that differ from both neighbours while
      the neighbours match each other.
- [ ] **Sync:** assert every source-footage piece plays its own audio (drift < 1 ms); cuts on downbeats.
- [ ] **Music joins:** onset pattern after each join matches a real downbeat, no click, the chord move
      is natural.
- [ ] **Quality:** SSIM of the encode vs the rendered frames ≥ 0.998; 60 fps; size under the limit.
- [ ] **Spelling** of every name and product.
- [ ] Contact sheets of the whole cut and a frame-by-frame look at every transition.

## 8. Mistakes already made (don't repeat)

| Mistake | Fix |
|---|---|
| 30 fps + heavy grain + 4 Mbps looked "low quality" | 60 fps, clean graphics, two-pass, check SSIM |
| Cinematic grade that didn't match the source clip | match the source's own brand style first, then elevate |
| Per-letter type-in using prefix widths broke kerning | `w(prefix through i) − w(i)` |
| Fade-out ignored because the helper overwrote alpha | multiply alpha |
| `round()` source-frame mapping flashed a frame | `floor` |
| A shot planned on a guessed grid | lock the grid to the claps; the intro may have its own pulse |
