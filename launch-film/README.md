# Claude Opus 5 — a launch film made of code

A 66-second product film that runs in a browser tab. Every frame is computed at runtime in
canvas 2D and the score is synthesised in Web Audio, so the whole thing is one `index.html`
with **no images, no video, no fonts to download and no libraries**.

## Watch

**https://badboyvee.github.io/BlackHoleeee/launch-film/**

Or download [`index.html`](index.html) and open it. It works offline — there is nothing to fetch.

| Input | Action |
| --- | --- |
| `space` or click the frame | Play / pause |
| `←` `→` | Seek ±5s |
| Scrubber | Drag to any point; chapters are marked |
| `m` | Sound on/off (the score is generated, not a file) |
| `f` | Fullscreen |

## The cut

| # | Chapter | What happens |
| --- | --- | --- |
| 1 | Ignition | A hairline cross, then a spark that swells into the first rays |
| 2 | The mark | Twelve tapered rays open into the burst, with a slow counter-rotating outer set |
| 3 | The name | The mark dissolves into 3,000 drifting particles; the name resolves in front of them |
| 4 | It writes code | A solver is typed live into an editor card, syntax-highlighted, then the tests run green |
| 5 | The whole loop | Five lanes — read, patch, test, fix, ship — filling and checking off from one instruction |
| 6 | It stays | An eight-hour task drawn as a timeline, with the elapsed clock counting up |
| 7 | Convergence | The particles fly back together and spell OPUS 5 |
| 8 | End card | Flip to paper: the mark, the name, the line |

## How it's built

- **Time is the only state.** Every frame is a pure function of one clock value, so scrubbing
  is frame-accurate and the film never drifts. Scenes declare a duration; the renderer
  cross-dissolves whichever ones overlap and blends their background colours by weight.
- **The mark is geometry.** Each ray is two quadratic curves meeting at the origin, with a
  gradient along its length. Ray count, taper, stagger and rotation are parameters, so the same
  function draws the hero burst, the seed rays in scene 1 and the small end-card lockup.
- **The particles are seeded.** A `mulberry32` PRNG gives 3,000 particles fixed identities, so
  the swirl and the convergence look identical every time you scrub back over them.
- **The wordmark is sampled, not drawn.** `OPUS 5` is rendered once to an offscreen canvas, the
  opaque pixels are collected as points, shuffled and used as particle targets — then the pixels
  are thrown away. Type becomes coordinates.
- **Film grain from numbers.** A 168×168 tile of random alpha is generated once into an
  `ImageData` and tiled as a pattern, offset per 24fps frame index so it flickers without ever
  becoming non-deterministic.
- **The score is four oscillators.** A drifting pad — root, octave, fifth, third — through a
  lowpass filter whose cutoff tracks each scene's intensity, plus band-passed noise that rises
  into every transition and a tiny square-wave click for each burst of typing.

## Note

This is an unofficial, self-made recreation, not Anthropic's launch video and not a copy of one.
The copy, the cut and the mark are all written for this piece. Claude Opus 5 wrote it.
