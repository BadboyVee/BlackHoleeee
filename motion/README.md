# Motion — every frame is code

Three motion-design films at 60 fps, written entirely in Python. No editor, no stock footage, no samples:
pictures are drawn with [skia-python](https://github.com/kyamagu/skia-python), the two 3D plates are rendered
with Blender's Cycles through the `bpy` module, and every sound is synthesised with numpy.

| Film | Format | Tempo | File |
| --- | --- | --- | --- |
| **THE FRONTIER** — Astra 6 · Gemini 3.8 · Fable 5.1 | 26.4 s, 1920×1080 | 150 BPM, F minor | [out/the-frontier.mp4](out/the-frontier.mp4) |
| **DARIO AMODEI**, a tribute | 32.8 s, 1920×1080 | 120 BPM, B minor → D major | [out/dario-amodei-tribute.mp4](out/dario-amodei-tribute.mp4) |
| **INTERFACE** — Fable 5.1 answers, on one board | 25 s, 1440×1440 | 120 BPM, F♯ minor | [out/interface.mp4](out/interface.mp4) |

**▶ [Watch them](https://badboyvee.github.io/BlackHoleeee/motion/)** · [the prompts](PROMPTS.md)

## THE FRONTIER

Three frontier models introduced like a fight card, each with its own colour, visual system and musical motif.
The finale plays all three motifs at once.

| Bars | Section | What happens |
| --- | --- | --- |
| 1–2 | Cold open | THREE / LABS. / THREE / MINDS. / ONE / FRONTIER., one word per beat, then the three labs as a constellation of their marks |
| 3–5 | 01 ASTRA 6 · OpenAI | letters drop on sixteenths, the italic 6 writes itself on, a zoom through the counter of the A into a star sphere around the OpenAI blossom, hyperspace |
| 6–8 | 02 GEMINI 3.8 · Google DeepMind | twin copies of the name converge while two bodies orbit through it, a double helix, a split marquee around the Gemini sparkle |
| 9–11 | 03 FABLE 5.1 · Anthropic | split-flap letters, a typewriter line with the Claude spark as its cursor, a 3D book turning pages on the beat, a ring of text around ✳ FABLE |
| 12–13 | 04 The clash | a triptych whose names squeeze from wide to condensed as the panels change width; the build stamps one letter of THE FRONTIER per kick |
| 14–16 | 05 The frontier | three monoliths rise out of a mirror floor (Blender Cycles), the title prints itself, each lab gets its mark |

Each contender card carries only public facts: the lab, the year it was founded (OpenAI 2015, DeepMind 2010,
Anthropic 2021) and where it is based. The model names are the ones the brief asked for.

## DARIO AMODEI, a tribute

A chaptered portrait of the co-founder and CEO of Anthropic, built from his public record: typography, data and
light, closing on his portrait.

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

A square reel about making the other two films, shot as one camera move over a board of fourteen live UI
components. You pick Fable 5.1, type the prompt and press Send, and the model streams its answer: it thinks (the
thoughts fold away into *Thought for 12s*), writes the plan token by token, lists the three drops with their
marks, writes the Python for the Astra scene with syntax colours, and calls a render tool whose film strip fills
with real frames of THE FRONTIER as the counter reaches 1,584. Open whips the camera to a player that plays the
real film, with its real soundtrack coming out of the player's little speaker, and scrubs it at varispeed. One
toggle wipes the whole board into dark mode from the switch outward, and on the drop the board tilts back into a
3D overview with the cursor's twelve clicks traced across it.

| Bars | Scene | What happens |
| --- | --- | --- |
| 1 | Model picker | Astra 6 → Gemini 3.8 → Fable 5.1 on a springy pill, then Fable's model card drops in |
| 2 | Composer | the prompt is typed, four chips pop, Send turns into a stop button |
| 3–6 | Fable 5.1 answers | thinking with a shimmer, the streamed plan, a list with inline marks, a code block, a render tool call with a live film strip, a toast |
| 6–7 | Player | THE FRONTIER plays through the player, the music steps back, a scrub jumps to the FABLE drop |
| 7–9 | Settings, stats | film grain on, dark mode wipes the board, effort to max; frames, tempo and loudness roll between the three films |
| 10–11 | Overview | the board tilts back in perspective, a light sweep, the click path draws with numbered markers, counters roll |
| 11–12 | Ship | ⌘K, *ship*, Enter; the palette collapses into *Every frame is code* and the three marks |

The camera is a homography over the board (pan, zoom, roll, tilt), so whip pans get real motion blur from the
sub-frame renderer. Every click, keystroke, token burst, toggle and chime has a sound on the 120 BPM grid.

## ARNAUD'S, a concept spot

A 27.5 s, 1920×1080 AI-concierge spot for a real restaurant: Arnaud's, 813 Bienville St in the French Quarter of
New Orleans, serving classic Creole since 1918. It started from a UI food ad and grew its own identity in four
colours used the same way in every scene: one light-green ground from the first frame to the last, white for cards,
panels and the phone, gold for everything that glows, and black only for type. A glowing frame of light is its
signature and MADE BY VEEE the maker's mark.

| Bars | Scene | What happens |
| --- | --- | --- |
| 1–2 | The table | a light-green kitchen table seen from above: bread, gold cutlery, a board and a knife drop onto it on the sixteenths while *Choosing dinner / for your anniversary / is a lot.* pops in, fruit keeps landing until the table is crowded, and a white card with a glowing edge drops in the middle |
| 3 | The ask | the props fly off the table, the card becomes the phone's input box, the phone rises behind it, and the prompt types in: pizza, sushi or ramen, or something special |
| 4 | Giant words | *Pizza, sushi, ramen?* typed huge in the serif of the name, white letters lined in black with a soft shadow, then *something special.* in italic |
| 5 | Thinking | under *Finding something special* in white serif lined in black, a ring of vivid gold, emerald and white beads spins like a loader; the three cravings orbiting inside are tossed away one by one and a gold doubloon stamped with the A flips into the middle |
| 6 | Carousel | white menu cards race over the ground and brake on Arnaud's, edged in gold, which opens into the dining room with its chandeliers glinting |
| 7–8 | The cashier | a white printer feeds out the pre-order (Soufflé Potatoes, Shrimp Arnaud, Bananas Foster), a white terminal rolls the amount due, a gold card taps, the screen goes gold and the receipt is stamped CONFIRMED |
| 9–10 | Map | the French Quarter by day in light green and white, a gold walk from Canal Street down Bourbon to 813 Bienville, a booking card |
| 11–12 | The name | *You were craving… something special. Now your table is waiting.*, then a white frame edged in light bursts open around the name and the address |
| 13 | Credit | the frame folds back into a gold orb, and the orb signs it: MADE BY VEEE |

The soundtrack is a 120 BPM jazz-pop groove in F with a sound for every event, from each prop knocking onto the
table and the fruit popping up the scale to the printer, the till and the stamp. The receipt shows no dish prices
(the published menu could not be checked for this render). The photographs (`photos/arnauds/pizza.jpg`,
`sushi.jpg`, `ramen.jpg`, `dining.jpg`) were supplied for the render and are not in the repository. Fan-made; not
affiliated with Arnaud's.

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
interface/     film 3: score.py, film.py (board, camera, cursor), stream.py (the streamed answer), ui.py, music.py
arnauds/       the concept spot: table.py (the opening), intro.py (the end: the name, the credit), phone.py, words.py, cards.py, checkout.py, map.py, film.py, music.py
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
ffmpeg -i out/the-frontier.mp4 -vf fps=30,scale=1280:720 -q:v 3 out/player_frames/f%04d.jpg   # for the player
python3 -m interface.main
python3 -m arnauds.main            # needs the four photographs in photos/arnauds/
```

`--scale 0.5 --mb 3 --step 2` renders a quick half-resolution, 30 fps preview. Without a plate directory the
finales fall back to a drawn stand-in.

## Notes

Fan-made. Not affiliated with or endorsed by OpenAI, Google or Anthropic. The OpenAI, Google, Gemini, Anthropic
and Claude marks are trademarks of their owners and are drawn here only to identify them.
