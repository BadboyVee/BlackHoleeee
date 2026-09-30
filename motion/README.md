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
(`photos/agiweek/`) were supplied for the render and are not in the repository. Fan-made; not affiliated with any
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
the user supplied (`photos/devday/`), are not in the repository; anyone without a photograph there is shown by
initials.

## VEEE, a spot for the studio

A 15 s, 1920×1080, 60 fps spot for VEEE, the studio that signs these films, made in the style of a product ad the
user supplied (a mascot printed in 1-bit dots, a clean white, one blue, a black card, a wordmark) and cut to that
ad's own soundtrack (123 BPM), but with its own story, its own mascot and our own work on the cards. The grade
matches the reference's: white `#ffffff`, paper `#fafafa`, blue `#2361ea`, ink `#0a0a0a`.

| Time | Moment | What happens |
| --- | --- | --- |
| 0–2.4 s | The hook | Vee, the studio's mascot (a knitted beanie, round glasses, a hoodie with a V on it), slides in from the right, winks and whispers *psst…*; *Launch day coming soon?* builds word by word while he reads along, and the blue grows out of *soon?* |
| 2.4–4.4 s | The work | on blue, Vee rises and winks as three of our own films fly in as cards on the beat, each one playing, printed in dots: launch films (THE FRONTIER), AI news (AGI WEEK), keynotes (DevDay 2026) |
| 4.4–7.3 s | The studio | the blue folds into a phone that becomes *Your launch*, three cuts ready to watch; beside it *VEEE turns it into / a film / on the beat.*, the last word bumping on the beats; a cursor taps *Watch* and the camera whips into it |
| 7.3–11.2 s | Rendered | the camera pulls out of *Make it move* onto the render dashboard: the brief is typed, the tempo counts up to 123 BPM and its dots light on the beats, Vee dances on air, the cut on every beat and the vertical cut are ticked, the render farm's chips tick, the frames count to 1,800, and *Rendered.* is stamped across it all; then the black spills out of Vee's beanie |
| 11.2–13.4 s | You | on black: *You launch. / We make it move.*, the last word sliding in from Vee's side |
| 13.4–15 s | The wordmark | white spills out of *move.*, VEEE drops in letter by letter, Vee climbs up behind it and winks: *Launch films for the frontier.*, *Start a film*, and the small print, *6 films · 60 fps · every frame is code* |

Vee is drawn in soft greys like a little 3D toy and printed through an 8×8 Bayer screen on a small offscreen canvas,
so he comes out as hard 1-bit dots however he moves; the film clips on the cards and thumbnails are printed the
same way, from our own renders in `out/` (dark films inverted, ink on paper). The black and white wipes are discs
with dithered edges. Type is Geist, with Geist Mono for the comments in the corners (and a running 60 fps
timecode), Instrument Serif italic for the word each line turns on, and Archivo for the wordmark. The reference
ad's sound, which the user supplied (`photos/veee/`), is not in the repository, so the render stays local.

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
| 4.6–13.1 s | Introducing | *Introducing*, bars rising into a grid of tiles, the mark building (the lines slide in, the sun rises), *Your AI-race intelligence / for founders and builders* zooming out of its first word, a chart of the frontier (Sonnet 5, Gemini 3.8, Astra 6, Fable 5.1, Sonnet 5.5?) and a curve that sweeps up and out |
| 13.1–16.3 s | The race | a laptop on the green hills, *See the race behind the headlines*; the camera pushes into its screen, onto the Frontier Index, where a violet light passes |
| 16.3–25.9 s | Scout | the Scout icon; a phone slides in: *what's coming this week?*, thinking, and the read: Sonnet 5.5 rolling out (routed from Sonnet 5, same price, free users likely), a new OpenAI model and Agent “O” around DevDay, Grok 4.8 maybe, Anthropic IPO talk (unconfirmed); the phone in a meadow, then close on the read |
| 25.9–37.7 s | Radar | a lens opens between two circles: RADAR, *Your early-warning engine*; birds cross the hills: *Watches, Spots, Alerts*; on black, *Searching…* and *NEW LAUNCH SPOTTED*, field by field |
| 37.7–45.1 s | The sea | a phone held up to the sea at sunset: *New launch spotted*; *Stay ahead of the race* in a crosshair; *Right from your pocket*, the phone rising out of the hills with its alerts; *Horizon* over the hills |
| 45.1–53 s | The mark | the mark built over the hills, then alone on black, with the small print: a concept film, predictions not news, not affiliated with any lab named, made by VEEE |

The hills and the sunset are Blender Cycles renders (`blender/hills.py`): a hand-placed countryside of steep rolling
hills with trees, its sky left clear so the film paints its own (a blue gradient and noise-shaped cumulus that drift),
and a glossy sea under a painted dusk with a sun disc; the film grades them vivid (the greens pushed toward a sunlit
yellow-green) and moves over them in 2D. The laptop, the phones, the icons and every screen are drawn. Type is
Inter, light for what is said. The reference film's sound, which the user supplied (`photos/horizon/`), is not in
the repository, so the render stays local.

## CLAUDE CODE, a fan-made spot

A 49.6 s, 1920×1080, 60 fps fan-made spot for Claude Code, made in the style of a product film the user supplied
(fuzzy toy agents on white, one heavy word under each) and timed to that film's own soundtrack, but with our own
crew and what Claude Code actually does. Not affiliated with Anthropic; the end card says so.

The crew are five plush agents, rendered in fur with Blender (`blender/plush.py`: a sphere with hair particles
and a principled hair shader, and one accessory each): a coral fixer in a hard hat, a mint tester with goggles, a
lavender reader in glasses, a sky-blue planner in a propeller beanie and an indigo night owl in a nightcap. Their
faces are drawn by the film, so they can look about, blink, smile, talk and doze, and they squash when they land.

| Time | Line | What happens |
| --- | --- | --- |
| 0–5.4 s | meet · Claude Code · for your code. | the fixer stands in for the o of *Code*; the crew line up: *agents in your terminal* |
| 5.4–10.7 s | reads your repo · runs your terminal · all your tools | the reader, a file tree it reads down, a terminal (`npm test`, `git status`), tool chips orbiting it |
| 10.7–15.5 s | learns your rules | the tester and CLAUDE.md, its rules ticked one by one |
| 15.5–22.5 s | ask it anything · or just @claude. | the planner among prompts (*fix the flaky test*, *why is login slow?*, *add dark mode*), then rings out from an @claude mention |
| 22.5–32.6 s | a bug? · on it. · reviewed. · tests pass. · CI red? · back to green. | a beetle in the code until the fixer lands on it; review comments and a pull request whose checks tick; CI bars going from red to green |
| 32.6–40.4 s | while you sleep · it asks first. · you're in control. | the night owl dozes by a migration running in the cloud; a permission prompt (`npm install zod`) it allows; the allow / ask / deny rules |
| 40.4–45.5 s | one agent. · or subagents, · a whole team. | the fixer, then the five, then a grid of them hopping in waves |
| 45.5–49.6 s | Claude Code | *Get back to building.* and the small print: fan-made, not affiliated with Anthropic, made by VEEE |

Type is Inter, black weight, tightly tracked, with small grey captions. The reference film's sound, which the user
supplied (`photos/crew/`), is not in the repository, so the render stays local.

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
blender/       the Cycles plates (monoliths, datacenter; hills and the sea at sunset) and the plush crew
frontier/      film 1: score.py (timing shared by picture and sound), music.py, scenes, film.py
dario/         film 2: the same layout, plus photos.py for the optional photographs
interface/     film 3: score.py, film.py (board, camera, cursor), stream.py (the streamed answer), ui.py, music.py
arnauds/       the concept spot: table.py (the opening), intro.py (the end: the name, the credit), phone.py, words.py, cards.py, checkout.py, map.py, film.py, music.py
agiweek/       the news film: flash.py (wordmarks, sparkle, collage), gemini.py, chatgpt.py, claude.py, grok.py, look.py, marks.py, sound.py (the supplied sound), film.py
horizon/       the Horizon spot: opening.py (the line, the bands, Introducing, the mark, the chart), scout.py (the laptop, the index, the phone, the meadow), radar.py (the lens, the verbs, the card, the sunset), finale.py, marks.py (the mark, the icons), sky.py (clouds, birds), plates.py (grading the Blender plates), devices.py, chat.py (what Scout says), sound.py, film.py
crew/          the Claude Code spot: cast.py (the plush crew and their drawn faces), ui.py (the little screens), scenes.py, sound.py, film.py
veee/          the studio spot: hook.py, work.py (the film cards, the fold), studio.py (the phone, the whip), dash.py (the render dashboard, the stamp), outro.py (the black card, the wordmark), mascot.py (Vee), dither.py (1-bit printing, film clips, dithered wipes), look.py, sound.py (the supplied sound), film.py
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
pip install bpy==4.2.0            # only for the two Blender plates

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
python3 -m veee.main               # needs the reference spot's sound in photos/veee/, and the films above rendered
python3 blender/hills.py out/plates/horizon all      # the Horizon plates
python3 -m horizon.main            # needs the reference film's sound in photos/horizon/
python3 blender/plush.py out/plates/plush            # the plush crew
python3 -m crew.main               # needs the reference film's sound in photos/crew/
```

`--scale 0.5 --mb 3 --step 2` renders a quick half-resolution, 30 fps preview. Without a plate directory the
finales fall back to a drawn stand-in.

## Notes

Fan-made. Not affiliated with or endorsed by OpenAI, Google or Anthropic. The OpenAI, Google, Gemini, Anthropic
and Claude marks are trademarks of their owners and are drawn here only to identify them.
