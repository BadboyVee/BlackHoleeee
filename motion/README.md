# Motion — every frame is code

Motion-design films at 60 fps, written entirely in Python. No editor, no stock footage: pictures are drawn with
[skia-python](https://github.com/kyamagu/skia-python), the 3D is rendered with Blender's Cycles through the `bpy`
module, and every sound is synthesised with numpy, except where a film is cut to a reference soundtrack that was
supplied for it.

| Film | Format | Tempo | File |
| --- | --- | --- | --- |
| **THE FRONTIER** — Astra 6 · Gemini 3.8 · Fable 5.1 | 26.4 s, 1920×1080 | 150 BPM, F minor | [out/the-frontier.mp4](out/the-frontier.mp4) |
| **DARIO AMODEI**, a tribute | 32.8 s, 1920×1080 | 120 BPM, B minor → D major | [out/dario-amodei-tribute.mp4](out/dario-amodei-tribute.mp4) |
| **INTERFACE** — Fable 5.1 answers, on one board | 25 s, 1440×1440 | 120 BPM, F♯ minor | [out/interface.mp4](out/interface.mp4) |
| **ARNAUD'S**, a concept spot (and its intro alone) | 27.5 s (4.5 s), 1920×1080 | 120 BPM, F, jazz-pop | [out/arnauds.mp4](out/arnauds.mp4) · [intro](out/arnauds_intro.mp4) |
| **AGI WEEK**, the last week of September (and an earlier cut) | 20.8 s (35.3 s), 1920×1080 | the reference clip's | [out/agiweek.mp4](out/agiweek.mp4) · [earlier cut](out/agiweek_preview.mp4) |
| **DEVDAY 2026**, twenty product launches | 51.6 s, 1920×1080 | 120 BPM, the teaser's | [out/devday.mp4](out/devday.mp4) |
| **HORIZON**, your AI-race intelligence | 53 s, 1920×1080 | 112.5 BPM, the reference film's | [out/horizon.mp4](out/horizon.mp4) |
| **SPARKS**, always-on Claude agents (a fan concept) | 49.6 s, 1920×1080 | the reference film's | [out/sparks.mp4](out/sparks.mp4) |
| **TOMO**, a home robot | 15 s, 1920×1080 | 123 BPM, the reference ad's | [out/tomo.mp4](out/tomo.mp4) |
| **VEEE**, the studio spot (replaced by TOMO) | 15 s, 1920×1080 | 123 BPM, the reference ad's | [out/veee.mp4](out/veee.mp4) |

**▶ [Watch them](https://badboyvee.github.io/BlackHoleeee/motion/)** · [the prompts](PROMPTS.md) · [the chat](CHAT.md), every
request in order · [references/](references/), every video and image sent with them

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
duotone and kept in `photos/`: see [photos/README.md](photos/README.md).

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
`sushi.jpg`, `ramen.jpg`, `dining.jpg`) were supplied for the render and are kept with it. Fan-made; not
affiliated with Arnaud's.

## AGI WEEK, the last week of September

A 20.8 s, 1920×1080, 60 fps film about one post (another week closer to AGI), built on a reference clip the user
supplied: it keeps that clip's sound and its design, then adds this week's models on top of the labs, the founders,
and the post's news. The claims are the post's, worded as it words them (expected, might, planned); MiniMax and
Qwen are left out.

| Time | Moment | What happens |
| --- | --- | --- |
| 0–3.3 s | Wordmarks | on black, a lab's wordmark on every click of the intro, each with its model on top: OpenAI *New model*, Claude *Sonnet 5.5*, Gemini, Grok *4.8*, Anthropic, Meta *Muse*, OpenAI *Agent “O”*, Google *Gemini* |
| 3.3–4.3 s | The drop | a white sparkle with an iridescent rim opens like a portal into a collage: the founders' photos and the models' cards flying past |
| 4.3–7.1 s | Gemini | the search pill turns into Gemini's dark pill; *Another week closer to AGI.* in Gemini's gradient; a phone where *the final week of September is looking stacked*, with Demis Hassabis, Mark Zuckerberg and Dario and Daniela Amodei on its cards |
| 7.1–10.9 s | ChatGPT | the blossom with *New model + Agent “O”* on top; the composer asks what OpenAI is launching this week, reads Sam Altman and OpenAI DevDay, and answers: DevDay is tomorrow, even more announcements and releases (AGI?) |
| 10.9–14.8 s | Claude | the spark, *Claude* typing in with *Sonnet 5.5* on top; a wall of canvases (the model, expected today, the Amodeis, a Fable moment?, the IPO in November, staying on top); a dive into the toolbar and a click on Comment: *IPO planned for November. Staying on top.* |
| 14.8–19.8 s | Grok | the wordmark with *4.8 · this week?* on top; *@X is Grok 4.8 dropping this week?*; the week in a terminal; Grok's answer (might drop, after 4.7's bad reviews) beside Elon Musk's card; *Big week ahead.* |
| 19.5–20.8 s | Credit | the maker's mark: MADE BY VEEE, each letter popping in under a band of light, held a second past the end of the sound |

Each lab is drawn in its own product's look and type: Google Sans for Google and Gemini, Source Serif for Claude,
Inter for ChatGPT. The cuts follow the reference's edit on its sound, the wordmarks flash on its clicks, and the
sparkle opens on its drop. The Claude, Gemini, Meta and X marks are Simple Icons paths; OpenAI's is the engine's;
the Grok mark and Google's G are drawn. The founders' photographs and the reference clip's sound
(`photos/agiweek/`) were supplied for the render and are kept with it. Fan-made; not affiliated with any
of the companies shown.

## DEVDAY 2026, twenty product launches

A 51.6 s, 1920×1080, 60 fps fan film for DevDay, built on OpenAI's DevDay 2026 teaser, which the user supplied: it
keeps the teaser's soundtrack and its design, opens on white with *Introducing…*, brings on the OpenAI team, the
developers from 78 countries and Dots, and fills in the twenty product launches the user predicted, each with a
drawing and its own motion. It says what it is on screen: fan-made predictions, not affiliated with OpenAI.

| Time | Moment | What happens |
| --- | --- | --- |
| 0–2 s | Introducing… | on white, *Introducing* lands point by point, three orange points follow it, and the last one swells into the teaser's big grey face |
| 2–9.3 s | The teaser | redrawn beat for beat, on white: the grey face pulls back and turns right round; its eyes go * * to - - to o o to > <; five more faces crowd in, fall into the middle and burst into orange points that land on the OpenAI mark and *DevDay*, join up and fill; then *DevDay. 20 product launches.* |
| 9.3–13.3 s | The team | on the drop a black iris closes and the line's points fly up into the OpenAI mark; the chart grows from it on the beat: Sam Altman (CEO) at the top, then Mark Chen (Chief Research Officer), Greg Brockman (President) and Thibault Sottiaux (Codex lead), each in a ring of the teaser's colours, their names and roles built from points |
| 13.3–17.3 s | 78 countries | a crowd of exactly 78 of the teaser's faces, thirteen across and six deep, pops in while the number beside them counts up with them to *DEVELOPERS FROM 78 countries*; they look over at it, cheer when the bass comes back, and fold away into points |
| 17.3–21.3 s | Dots | OpenAI's agent bot, a Muse Agent and Grokbot competitor: the 78's points fly in to build *Dots* while the user's sheet of its looks comes alive beside it, nine tiles (round shades, sleepy lids, a monocle, sparkles, round specs, shiny eyes, wayfarers, ovals, googly eyes) that pop in on the groove and flip to the next look twice on the beat |
| 21.3–40.3 s | The launches | two a bar: Astra 6.1, Agent “O”, the $500 plan, Aeon, GPT-6.1 Sol, GPT-6.1 Luna, a Codex update (idk), Chat + Work merging, OpenAI acquiring Google, the first hardware device, a bunch of lil new models, Sora returning, a Sam Altman humanoid robot, Greg, 5 banked resets, cancer solved, OpenAI acquiring McDonald’s, agents escaping again, weather solved |
| 40.3–46.2 s | AGI | the faces crowd back in and count down in their eyes (3, 2, 1), fall into the middle when the bass drops out and burst into blue points that spell AGI, which fills when the bass comes back and throws them out again like confetti: *Official launch of AGI* |
| 46.2–51.6 s | The ending | on the teaser's long low note, AGI comes apart into the points of the OpenAI mark and *OpenAI DevDay[2026]*, built left to right as the teaser builds it, over *FAN-MADE PREDICTIONS. NOT AFFILIATED WITH OPENAI.*; then its points fly into the maker's mark, on a card of its own and spaced out: MADE BY VEEE |

Every drawing is in the teaser's own language: flat discs in its six colours with eyes drawn like typed glyphs
(* o - > < + x ^ / \\, and $ ? 3 2 1 from the font), white strokes on black. Every title is built the way the
teaser builds its type, from the points a type designer would draw (corners and extremes, read off the outlines,
the OpenAI mark's included), then the outline, then the fill; between launches the points fly from one title to
the next. The sound is the teaser's soundtrack and nothing else, cut on its bar lines (120 BPM): its first two
beats of clicks twice under *Introducing…*, its opening as it is, its four bars looped under the team, the 78
countries, Dots and the launches, its last bar and its long low note, held a little longer, at the end. Type is Geist,
with Geist Mono for the labels; the maker's mark is Archivo. The teaser's sound and the team's photographs, which
the user supplied (`photos/devday/`), are kept with it; anyone without a photograph there is shown by
initials.

## TOMO, a home robot

A 15 s, 1920×1080, 60 fps concept spot for Tomo, a home robot, made in the style of a product ad the user supplied
(a character on a clean white, one blue, cards, a phone, a black card, a wordmark) and cut to that ad's own
soundtrack (123 BPM), with its own story. Tomo is photoreal: a white shell head with a black glass visor, ear
lights, a ribbed neck and white shoulders, rendered in Blender (`blender/tomo.py`) in three head turns, with the
things it does (folded towels in terry cloth, a stack of plates, a succulent) rendered the same way. Its LED eyes are
lit by the film on the visor itself, at the points the render measured, so they can glance, blink, wink and smile.

| Time | Moment | What happens |
| --- | --- | --- |
| 0–2.4 s | The hook | Tomo peeks in, winks and says *hey!*; *// for busy homes* and *Could use / an extra hand?* build word by word, and the blue grows out of *hand?* |
| 2.4–4.4 s | The chores | on blue, three cards land on the beat: laundry, dishes, plants, each with its render |
| 4.4–7.3 s | The app | the blue folds into a phone: Tomo at home, charged, and today's three chores; beside it *tomo turns chores into / free time, / every day.*; a cursor taps Start and the camera whips into it |
| 7.3–11.2 s | Done | the dashboard: laundry day every Saturday at 10, time back counting up, on duty, power, safety, the day's chores ticking off, and *Done.* stamped across it; then the black grows out of the visor |
| 11.2–13.4 s | You | on black: *You rest. / Tomo does the rest.* |
| 13.4–15 s | The wordmark | white opens from its eyes, *tomo* drops in letter by letter with Tomo peeking over it: *The home robot that helps.*, *Reserve yours*, ships 2027, and the specs |

Type is Geist with Geist Mono for the corners, Instrument Serif italic for the word each line turns on, and Fraunces
for the wordmark. The reference ad's sound, which the user supplied, is kept in `photos/tomo/`.

## HORIZON, your AI-race intelligence

A 53 s, 1920×1080, 60 fps concept spot for an app that watches the AI race, made in the style of a product film
the user supplied (thin type on black and white, a laptop and a phone out in green hills, the sea at sunset) and cut
to that film's own soundtrack (112.5 BPM), but with its own story and brand: Horizon, a sunrise on three horizon
lines, and two agents, Scout (ask it) and Radar (it tells you). What Scout and Radar say is this week's talk from
our own chat, each item marked for what it is: likely, next, watch, rumour. Predictions, not news; the end card says
so.

| Time | Moment | What happens |
| --- | --- | --- |
| 0–4.6 s | The line | on white a pen draws a flourish that runs off into a line and leaves *The frontier moves every week.*; black bands sweep over *See it before it ships.* |
| 4.6–13.1 s | Introducing | *Introducing*, bars rising into a grid of tiles, the mark building (the lines slide in, the sun rises), *Your AI-race intelligence / for founders and builders* zooming out of its first word, a chart of the frontier (chat, code, agents, computer use, robots?) and a curve that sweeps up and out |
| 13.1–16.3 s | The race | a laptop on the green hills, *See the race behind the headlines*; the camera pushes into its screen, onto the Frontier Index, where a violet light passes |
| 16.3–25.9 s | Scout | the Scout icon; a phone slides in: *what's coming this week?*, thinking, and the read: Sonnet 5.5 rolling out (routed from Sonnet 5, same price, free users likely), a new OpenAI model and Agent “O” expected any day, Grok 4.8 maybe, Anthropic IPO talk (unconfirmed); the phone over a meadow, then close on the read |
| 25.9–37.7 s | Radar | a lens opens between two circles: RADAR, *Your early-warning engine*; birds cross the hills: *Watches, Spots, Alerts*; on black, *Searching…* and *NEW LAUNCH SPOTTED*, field by field |
| 37.7–45.1 s | The sea | a phone held up to the sea at sunset: *New launch spotted*; *Stay ahead of the race* in a crosshair; *Right from your pocket*, the phone rising out of the hills with its alerts; *Horizon* over the hills |
| 45.1–53 s | The mark | the mark built over the hills, then alone on black, with its name and the small print: a concept film, predictions not news, not affiliated with any lab named |

Everything out in the world is a Blender Cycles render. The countryside (`blender/hills.py`, `blender/country.py`)
is hand-placed rolling hills dressed as fields: one 2-D Voronoi pattern colours each field its own green (some mown
in stripes) and, through Geometry Nodes, lines every field's border with a hedgerow, with trees standing in the
hedges and a few oaks out in the fields; a sheet of noise high above, seen only by the sun, lays cloud shadows over
it, and the air hazes it with distance. The clouds (`blender/clouds.py`) are a field of real cumulus: each one a
heap of spheres worn into cauliflower billows by Worley noise, flat at the condensation level, baked into a volume
grid with Geometry Nodes and lit by the same low sun, rendered in three layers by distance so the film hazes the far
ones into its sky and drifts each layer at its own speed. The phone and the laptop (`blender/devices.py`) are black
titanium and aluminium rendered from the front with their screens cut out, so the film plays its own screens
behind the glass; the wildflowers and long grass in front of the lens in the meadow (`blender/meadow.py`) are
rendered wide open, in bokeh; the sea at sunset is a glossy plane under a painted dusk. The film grades the plates
vivid (the greens pushed toward a sunlit yellow-green) and moves over them in 2D. Type is Inter, light for what is
said. The reference film's sound, which the user supplied, is kept in `photos/horizon/`.

## SPARKS, a fan concept

A 49.6 s, 1920×1080, 60 fps fan concept for always-on Claude agents called sparks, made in the style of a product
film the user supplied (fuzzy toy agents on white, one heavy word under each) and timed to that film's own
soundtrack, with our own cast and story. Not affiliated with Anthropic; the end card says so.

The sparks are five plush toys rendered in fur with Blender (`blender/sparks.py`: a soft body with clumped hair
particles trimmed short on the face, bead eyes or stitched ones, felt cheeks, and one accessory each): the lead in
terracotta with a wire spark on top, a mint builder in a hard hat, a butter-yellow talker in a headset, a lavender
reader in round gold glasses and an indigo sleeper in a striped nightcap. Each is rendered in each expression and
its shadow on its own, so they can hop off the floor and land on it again; the film grades each toward its colour.

| Time | Line | What happens |
| --- | --- | --- |
| 0–5.4 s | meet · sparks · for you. | the lead stands in for the a of *sparks*; the five line up: *always-on Claude agents* |
| 5.4–12.4 s | its own computer · its own browser · all your apps | the lead writing a plan on its own computer, booking a table in its own browser, app chips orbiting it |
| 12.4–16.2 s | learns how you work | the reader and its memory: what you care about, how you write, when to ping you |
| 16.2–22.5 s | message it · or just · talk. | the talker among a Slack message, an email and a text, then a call ringing in |
| 22.5–32.6 s | a bug? · on it. · feedback. · tested fixes. · new numbers? · reruns itself. | a beetle in the code until the builder stomps it; reviews turned into a fix whose checks tick; the reader rerunning a chart on new data |
| 32.6–40.4 s | while you sleep · it asks first. · you set the rules. | the sleeper dozes by a report building overnight; it asks before sending it; the allow / ask first / never rules |
| 40.4–45.5 s | one spark. · or · a whole team. | the lead, then the five, then a grid of them hopping in waves |
| 45.5–49.6 s | sparks | *Your time, back.* and the small print: a fan concept, not affiliated with Anthropic |

Type is Inter, black weight, tightly tracked, with small grey captions. The reference film's sound, which the user
supplied, is kept in `photos/sparks/`.

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
blender/       the Cycles renders: monoliths, datacenter; Horizon's countryside, clouds, devices, meadow and sea at sunset; the sparks; Tomo
frontier/      film 1: score.py (timing shared by picture and sound), music.py, scenes, film.py
dario/         film 2: the same layout, plus photos.py for the optional photographs
interface/     film 3: score.py, film.py (board, camera, cursor), stream.py (the streamed answer), ui.py, music.py
arnauds/       the concept spot: table.py (the opening), intro.py (the end: the name, the credit), phone.py, words.py, cards.py, checkout.py, map.py, film.py, music.py
agiweek/       the news film: flash.py (wordmarks, sparkle, collage), gemini.py, chatgpt.py, claude.py, grok.py, look.py, marks.py, sound.py (the supplied sound), film.py
horizon/       the Horizon spot: opening.py (the line, the bands, Introducing, the mark, the chart), scout.py (the laptop, the index, the phone, the meadow), radar.py (the lens, the verbs, the card, the sunset), finale.py, marks.py (the mark, the icons), sky.py (the sky, birds), plates.py (grading the Blender plates, the cloud layers), devices.py (the rendered phone and laptop), chat.py (what Scout says), sound.py, film.py
sparks/        the sparks spot: cast.py (the plush sprites, their grade, shadows and hops), ui.py (the little screens), scenes.py, look.py, sound.py, film.py
tomo/          the Tomo spot: robot.py (the renders and the LED eyes), hook.py, work.py (the cards, the fold), studio.py (the phone, the whip), dash.py (the dashboard, the stamp), outro.py (the black card, the wordmark), look.py, sound.py (the supplied sound), film.py
devday/        the DevDay film: intro.py (Introducing…, the teaser redrawn), team.py (the OpenAI team), world.py (the 78), dots.py (Dots), chain.py (lines built from each other's points), items.py (the twenty launches), launches.py (the list), finale.py (AGI, the ending), faces.py, type.py (type built from its points), sound.py (the teaser's sound, cut on its bars), film.py
fonts/         Archivo, Fraunces, Inter, JetBrains Mono, Instrument Serif, Google Sans, Source Serif 4, Geist, Geist Mono (all SIL OFL); DejaVu for ∝ ⌘ ⏎
```

Picture and sound read the same timing sheet (`score.py`), so every cut, letter and flash lands on the beat it was
written for, and every on-screen event has its own sound: split-flap clacks, typewriter keys, decode chatter,
whooshes, and a euclidean click pattern under the drops. The HUD's level meter is measured from the finished mix.

### Rebuild

```sh
apt-get install ffmpeg libegl1
pip install skia-python numpy scipy opencv-python-headless uharfbuzz pyloudnorm fonttools brotli
pip install bpy==4.2.0            # only for the Blender renders

cd motion
python3 blender/monoliths.py  /tmp/plates/monoliths  1 150
python3 blender/datacenter.py /tmp/plates/datacenter 1 150
python3 -m frontier.main --plate /tmp/plates/monoliths
python3 -m dario.main    --plate /tmp/plates/datacenter
ffmpeg -i out/the-frontier.mp4 -vf fps=30,scale=1280:720 -q:v 3 out/player_frames/f%04d.jpg   # for the player
python3 -m interface.main
python3 -m arnauds.main            # needs the four photographs in photos/arnauds/
python3 -m agiweek.main            # needs the founders' photographs and the reference sound in photos/agiweek/
python3 -m devday.main             # needs the teaser's sound and the team's photographs in photos/devday/
python3 blender/hills.py out/plates/horizon all      # the Horizon plates: the countryside, the sea at sunset,
python3 blender/clouds.py out/plates/horizon all     # the cloud layers,
python3 blender/devices.py out/plates/horizon all    # the phone and the laptop,
python3 blender/meadow.py out/plates/horizon         # and the meadow
python3 -m horizon.main            # needs the reference film's sound in photos/horizon/
python3 blender/sparks.py out/plates/sparks          # the five sparks, each expression and shadow
python3 -m sparks.main             # needs the reference film's sound in photos/sparks/
python3 blender/tomo.py out/plates/tomo bust:0 bust:-16 bust:16 towels plates plant
python3 -m tomo.main               # needs the reference ad's sound in photos/tomo/
```

`--scale 0.5 --mb 3 --step 2` renders a quick half-resolution, 30 fps preview. Without a plate directory the
finales fall back to a drawn stand-in.

## Notes

Fan-made. Not affiliated with or endorsed by OpenAI, Google or Anthropic. The OpenAI, Google, Gemini, Anthropic
and Claude marks are trademarks of their owners and are drawn here only to identify them.
