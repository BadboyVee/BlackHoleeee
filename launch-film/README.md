# Opus 5 — the launch film, in code

Eighteen seconds on tan paper: speckled birds' eggs arrive one at a time until they form a **5**,
the eggs hatch into birds on the same spots, the flock lifts off, and the wordmark is left behind.

The first eight seconds are a recreation of the Claude Opus 5 launch clip, measured frame by
frame. **Everything from the hatch onward is an extension of my own** — the source clip I was
given ends on the wordmark at 8.09s, so the birds are not a reconstruction of anything.

Everything is drawn at runtime in canvas 2D. **No images, no video, no fonts to download and no
libraries** — the eggs are generated, not photographed, and the whole film is one `index.html`
that works offline.

## Watch

**https://badboyvee.github.io/BlackHoleeee/launch-film/**

| Input | Action |
| --- | --- |
| `space` or click the frame | Play / pause |
| `←` `→` | Seek |
| Scrubber | Drag anywhere in the 18 seconds |
| `m` | Sound on/off (synthesised — see below) |
| `l` | Loop on/off |
| `f` | Fullscreen |

## Matching the original

The source clip was measured rather than guessed: 8.09s, 24fps, 4:5 (1728×2160), silent, paper
sampled at `rgb(204,186,156)`. Counting changed pixels frame by frame gives the choreography —
eggs pop in from t≈0 to t≈2.9 with no tweening between them, the finished numeral holds until
t=5.0, then a hard cut to `Opus 5` centred, held to the end. This build reproduces that timing,
and quantises playback to 24fps so the stop-motion cadence survives on a 60Hz screen.

## The cut

| Time | Beat |
| --- | --- |
| 0 → 2.9s | Eggs arrive one at a time, no tweening between them |
| 2.9 → 5.0s | The finished numeral holds |
| 5.0 → 7.7s | Each egg hatches: a bird takes its place, on the same 24fps beat |
| 7.7 → 9.6s | A 5 made of birds |
| 9.6 → 13.1s | The flock lifts off, top of the frame first, wingbeats and all |
| 13.5 → 18s | `Opus 5` on bare paper |

## The sound

**The source clip carries no audio.** Its AAC track decodes to 388,096 samples of digital
silence — peak amplitude zero, not one non-zero sample — so there is nothing to lift from it.
What plays here is foley written for the film, synthesised in Web Audio with no samples:

- a wooden **tok** as each egg lands, pitched by the egg's size — big eggs land lower
- a shell **crack** and a two-note **chirp** at each hatch, the chirp seeded per bird
- a **wingbeat bed**: noise through a bandpass, gated by a 7 Hz oscillator, whose level follows
  how many birds are actually in the air on that frame
- a short **whoosh** as each bird leaves
- a low **room tone** under everything, a pad that changes chord with the phase of the film, and
  a warm triad on the card

Every one-shot is panned by where it happens on the paper, so eggs landing on the left of the
numeral land in your left ear. Events fire as the playhead crosses them, so the score follows
scrubbing and looping rather than running on its own clock.

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

## And a bird

The bird uses the same engine one level up. A teardrop body with a pale belly gradient and fine
speckling; a wing of three layered coverts clipped to the body, with primaries reaching past the
rear; a short tail fan; a neck wedge drawn before the head so the join disappears under it; beak,
eye and legs; then the plate's ink line — stroked *before* the head, or it draws a line straight
across the bird's face.

Each bird's plumage is derived from the shell it came out of: the back is its egg's ground colour
darkened, the belly the same colour lifted toward cream, the wing darker still. Beak length, leg
length, head size, tail spread, speckle count and which way it faces all vary per bird from a
seed.

In flight the folded wing is replaced by a swept blade that leaves the shoulder, curves forward
and tapers to a point, drawn twice — a dim far wing behind the body, a lit near wing in front of
it but **behind the head**, so the bird does not disappear behind its own wing on the upstroke.
Two poses, one wingbeat apart, alternating about seven times a second.

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

Unofficial. The original clip is Anthropic's; the first eight seconds here are a from-scratch
reconstruction of its choreography and look, and none of its artwork is reused. The hatch and the
flight are mine — if the real film goes somewhere else after the wordmark, this is not it.
