# Opus 5 — the launch film, in code

A code-only recreation of the eight-second Claude Opus 5 launch clip: speckled birds' eggs
arriving one at a time on tan paper until they form a **5**, then a cut to the wordmark.

Everything is drawn at runtime in canvas 2D. **No images, no video, no fonts to download and no
libraries** — the eggs are generated, not photographed, and the whole film is one `index.html`
that works offline.

## Watch

**https://badboyvee.github.io/BlackHoleeee/launch-film/**

| Input | Action |
| --- | --- |
| `space` or click the frame | Play / pause |
| `←` `→` | Seek |
| Scrubber | Drag anywhere in the 8 seconds |
| `l` | Loop on/off |
| `f` | Fullscreen |

## Matching the original

The source clip was measured rather than guessed: 8.09s, 24fps, 4:5 (1728×2160), silent, paper
sampled at `rgb(204,186,156)`. Counting changed pixels frame by frame gives the choreography —
eggs pop in from t≈0 to t≈2.9 with no tweening between them, the finished numeral holds until
t=5.0, then a hard cut to `Opus 5` centred, held to the end. This build reproduces that timing,
and quantises playback to 24fps so the stop-motion cadence survives on a 60Hz screen.

## Drawing an egg with arithmetic

- **The ovoid.** An egg is a circle whose width is skewed toward the blunt end:
  `x = b·sin t·(1 − k·cos t)`, `y = −a·cos t`, with a little low-frequency wobble on the radius so
  the outline looks drawn rather than printed.
- **The shell.** A base colour from a plate of fourteen olives, buffs and terracottas, then ~50
  soft radial blooms of neighbouring hues so the ground is never flat.
- **The markings, in three layers.** A grey-lilac underlayer first (real eggs show it beneath the
  surface pigment), then dark blotches — irregular loops smoothed through their own midpoints —
  then fine peppering. Every mark is placed by a sampler biased toward the blunt end, where a real
  egg carries most of its pigment. Four styles: plain, peppered, blotched and scrawled.
- **Volume and ink.** A highlight up-left and a shadow at the rim, then the plate's outline
  stroked over the top.
- Each egg is painted once into its own offscreen canvas and then reused every frame, so 36 eggs
  cost 36 `drawImage` calls.

## Arranging them into a numeral

The `5` is rendered once to an offscreen mask and its ink bounding box mapped onto the frame.
Eggs are then packed into it largest first — the radius target shrinks as attempts go on, so big
eggs claim their space and small ones fill the gaps, with a little overlap allowed and a little
spill past the edge. They arrive roughly top to bottom, jittered so it never looks like a queue.

The paper is a seeded sheet of its own: uneven ageing, pale flecks in the pulp, and a grain tile
offset per frame index.

## Also here

[`extended-cut.html`](extended-cut.html) — a longer, unrelated 66-second film in the same
no-images spirit: a parametric burst mark, 3,000 seeded particles, a live typing scene and a
Web Audio score.

## Note

Unofficial. The original clip is Anthropic's; this is a from-scratch reconstruction of its
choreography and look in code, and none of its artwork is reused — every egg here was generated
by the program you can read in `index.html`.
