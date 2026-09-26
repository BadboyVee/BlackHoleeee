# Motion — every frame is code

Three motion-design films at 60 fps, written entirely in Python. No editor, no stock footage, no samples:
pictures are drawn with [skia-python](https://github.com/kyamagu/skia-python), the two 3D plates are rendered
with Blender's Cycles through the `bpy` module, and every sound is synthesised with numpy.

| Film | Format | Tempo | File |
| --- | --- | --- | --- |
| **THE FRONTIER** — Astra 6 · Gemini 3m · Fable 5.1 | 26.4 s, 1920×1080 | 150 BPM, F minor | [out/the-frontier.mp4](out/the-frontier.mp4) |
| **DARIO AMODEI**, a tribute | 32.8 s, 1920×1080 | 120 BPM, B minor → D major | [out/dario-amodei-tribute.mp4](out/dario-amodei-tribute.mp4) |
| **INTERFACE** — a UI micro-interaction reel | 16.4 s, 1440×1440 | 120 BPM, E major | [out/interface.mp4](out/interface.mp4) |

**▶ [Watch them](https://badboyvee.github.io/BlackHoleeee/motion/)**

## THE FRONTIER

Three frontier models introduced like a fight card, each with its own colour, visual system and musical motif.
The finale plays all three motifs at once.

| Bars | Section | What happens |
| --- | --- | --- |
| 1–2 | Cold open | THREE / LABS. / THREE / MINDS. / ONE / FRONTIER., one word per beat, then the three labs as a constellation of their marks |
| 3–5 | 01 ASTRA 6 · OpenAI | letters drop on sixteenths, the italic 6 writes itself on, a zoom through the counter of the A into a star sphere around the OpenAI blossom, hyperspace |
| 6–8 | 02 GEMINI 3m · Google DeepMind | twin copies of the name converge while two bodies orbit through it, a double helix, a split marquee around the Gemini sparkle |
| 9–11 | 03 FABLE 5.1 · Anthropic | split-flap letters, a typewriter line with the Claude spark as its cursor, a 3D book turning pages on the beat, a ring of text around ✳ FABLE |
| 12–13 | 04 The clash | a triptych whose names squeeze from wide to condensed as the panels change width; the build stamps one letter of THE FRONTIER per kick |
| 14–16 | 05 The frontier | three monoliths rise out of a mirror floor (Blender Cycles), the title prints itself, each lab gets its mark |

Each contender card carries only public facts: the lab, the year it was founded (OpenAI 2015, DeepMind 2010,
Anthropic 2021) and where it is based. The model names are the ones the brief asked for.

## DARIO AMODEI, a tribute

A chaptered portrait of the co-founder and CEO of Anthropic, built from his public record. No likeness is used;
the film is typography, data and light.

| Bars | Chapter | Content |
| --- | --- | --- |
| 1–2 | Prologue | *It started with neurons.* A live extracellular trace whose spikes fall into the tempo |
| 3–4 | 01 Physics | Stanford, B.S. physics · Princeton, Ph.D., studying neural circuits; a spike raster with synchrony on the beat |
| 5–6 | 02 Safety | *Concrete Problems in AI Safety* (2016) with its five problems; *Deep Reinforcement Learning from Human Preferences* (2017) |
| 7–8 | 03 Scale | VP of Research at OpenAI; a network that doubles its width on every beat; a log-log power law; GPT-2, GPT-3 and the scaling-laws paper |
| 9–10 | 04 Anthropic | the year rolls from 2016 to 2021: co-founds Anthropic with Daniela Amodei and colleagues; Claude, 2023 |
| 11–13 | 05 Machines of Loving Grace | the October 2024 essay: *a country of geniuses in a datacenter* over a Blender flyover of a city of racks, *the compressed 21st century*, and the essay's five domains |
| 14–16 | 06 Dario Amodei | the name, the role, the chapters, and the trace from the prologue firing once on the last chord |

The finale uses a portrait when `photos/dario.jpg` is present (the published render uses one supplied for it);
chapter 04 can show the Anthropic office from `photos/anthropic-hq.jpg`. Photos are rendered in the film's
duotone and are git-ignored: see [photos/README.md](photos/README.md).

## INTERFACE

A square reel of product-UI micro-interactions, about making the other two films: a model picker with the three
marks, a prompt typed into a composer, a Generate button that morphs into a spinning Claude spark and then a
render-progress pill counting 1,584 frames, a player scrubbing real frames of THE FRONTIER over its real
waveform, springy toggles and an effort slider, a stats card whose digits roll from one film's numbers to the
other's over each film's measured loudness curve, and a command palette that ships them. Every click, keystroke,
toggle and chime lands on the 120 BPM grid.

## How it is built

```
engine/        the shared engine
  core.py      easing (Penner set, cubic-bezier, springs), musical time, Perlin noise
  gfx.py       paints, layers, variable-font typography shaped with HarfBuzz, an SVG path parser
  logos.py     the lab and model marks, redrawn from memory as vector paths
  three.py     a look-at camera and point/mesh generators for the 2D-drawn 3D
  post.py      bloom and halation, anamorphic streaks, radial zoom blur, chromatic aberration, glitch, grain
  render.py    motion blur by accumulating sub-frames, parallel workers, near-lossless master, delivery encode
  hud.py       the broadcast frame: brackets, timecode, bar counter, a live level meter
  audio.py     oscillators with PolyBLEP, drum and synth voices, foley clicks, convolution reverb,
               sidechain, glue compression, a look-ahead limiter and LUFS normalisation
blender/       the two Cycles plates (monoliths, datacenter)
frontier/      film 1: score.py (timing shared by picture and sound), music.py, scenes, film.py
dario/         film 2: the same layout, plus photos.py for the optional photographs
interface/     film 3: score.py (cursor choreography), film.py (components), music.py
fonts/         Archivo, Fraunces, Inter, JetBrains Mono, Instrument Serif (all SIL OFL); DejaVu for ∝ ⌘ ⏎
```

Picture and sound read the same timing sheet (`score.py`), so every cut, letter and flash lands on the beat it was
written for, and every on-screen event has its own sound: split-flap clacks, typewriter keys, decode chatter,
whooshes, and a euclidean click pattern under the drops. The HUD's level meter is measured from the finished mix.

### Rebuild

```sh
apt-get install ffmpeg libegl1
pip install skia-python numpy scipy opencv-python-headless uharfbuzz pyloudnorm fonttools brotli
pip install bpy==4.2.0            # only for the two Blender plates

cd motion
python3 blender/monoliths.py  /tmp/plates/monoliths  1 150
python3 blender/datacenter.py /tmp/plates/datacenter 1 150
python3 -m frontier.main --plate /tmp/plates/monoliths
python3 -m dario.main    --plate /tmp/plates/datacenter
ffmpeg -i out/the-frontier.mp4 -vf fps=10,scale=452:254 out/player_frames/f%04d.jpg   # frames for the player
python3 -m interface.main
```

`--scale 0.5 --mb 3 --step 2` renders a quick half-resolution, 30 fps preview. Without a plate directory the
finales fall back to a drawn stand-in.

## Notes

Fan-made. Not affiliated with or endorsed by OpenAI, Google or Anthropic. The OpenAI, Google, Gemini, Anthropic
and Claude marks are trademarks of their owners and are drawn here only to identify them.
