# The prompts

One-shot prompts for the three films, one per film. They were written after the fact from what was built; the
films themselves came out of a longer back-and-forth. Paste one into a coding agent that has Python, ffmpeg,
skia-python, numpy and Blender's `bpy` available.

[Motion](README.md) · [all projects](../README.md)

---

## 1 — THE FRONTIER

```text
Make THE FRONTIER: a 26-second motion-design film that introduces three frontier AI models like a fight card: Astra 6 (OpenAI), Gemini 3.8 (Google DeepMind) and Fable 5.1 (Anthropic). Deliver one MP4 with sound, 1920×1080 at 60 fps.

Every frame and every sound has to come from code. No video editor, no stock footage, no samples. Draw the 2D with skia-python, render the 3D shot with a Blender Python script (bpy, Cycles), and synthesise the whole soundtrack with numpy. It should still look like a top After Effects edit: real motion blur (accumulate sub-frames), cubic-bezier and spring easing, bloom and halation, anamorphic streaks, chromatic aberration on the hits, film grain and a vignette.

Sound: a 150 BPM hard-techno track in F minor, 16 bars plus a held last chord. Put the timing in one sheet that the picture and the music both read, so every cut, letter and flash lands on the beat. Every event on screen gets its own sound too: clicks, split-flap clacks, typewriter keys, whooshes and impacts.

Structure:
- Bars 1–2, cold open: THREE / LABS. / THREE / MINDS. / ONE / FRONTIER., one word per beat, then the three lab logos joined up as a constellation.
- Bars 3–5, ASTRA 6, green on black: the letters drop in on sixteenths, an italic 6 writes itself on, then zoom through the counter of the A into a sphere of stars around the OpenAI mark and out into hyperspace.
- Bars 6–8, GEMINI 3.8, electric blue: twin copies of the name slide together while two bodies orbit through them, then a double helix of nodes and a split marquee around the Gemini sparkle.
- Bars 9–11, FABLE 5.1, clay on warm paper: split-flap letters, a typewriter line with the Claude spark as its cursor, a 3D book turning a page on every beat, a ring of text around the spark.
- Bars 12–13, the clash: a triptych of the three names that squeeze from wide to condensed as the panels change width, then a strobing build that stamps one letter of THE FRONTIER per kick.
- Bars 14–16, the finale: three glowing monoliths rise out of a mirror floor (Blender, Cycles), the title prints itself under a light sweep, and each lab gets its mark.

Give each model its own colour, visual system and musical motif: a star arpeggio for Astra, twin arps panned hard left and right for Gemini, a music-box melody for Fable. The finale plays all three motifs at once. Keep a broadcast HUD over everything: corner brackets, timecode, bar counter, section name and a level meter measured from the final mix. Draw the logos from memory as vector paths, use only public facts about the labs, and end on a small "fan-made, not affiliated" line.

Render it, look at your own frames, and fix whatever looks off before you hand it over.
```

## 2 — DARIO AMODEI, a tribute

```text
Make a 33-second motion-design tribute to Dario Amodei, co-founder and CEO of Anthropic, told in chapters from his public record. Deliver one MP4 with sound, 1920×1080 at 60 fps.

Every frame and every sound has to come from code: skia-python for the 2D, one Blender Python script (Cycles) for the 3D plate, numpy for the music. No editor, no stock footage, no samples. Go for an editorial look: a serif display face with italics, small mono labels, a palette of warm off-black, paper and clay, grain, halation, motion blur, and a quiet HUD with the chapter name, timecode and a bar counter.

Sound: 120 BPM, 16 bars plus a held chord, moving from B minor to D major. Picture and music read the same timing sheet, and every event on screen has its own sound.

Chapters:
- Prologue: "It started with neurons." over a live extracellular recording trace whose spikes fall on the tempo.
- 01 Physics: Stanford, B.S. in physics; Princeton, Ph.D. studying neural circuits. A spike raster that fires in sync on the beat.
- 02 Safety: "Concrete Problems in AI Safety" (2016), with its five problems ticking off, then "Deep Reinforcement Learning from Human Preferences" (2017).
- 03 Scale: VP of Research at OpenAI. A network that doubles its width on every beat, a scaling-law line drawing itself on log-log axes, and GPT-2, GPT-3 and the scaling-laws paper.
- 04 Anthropic: the year rolls from 2016 to 2021 like an odometer. "Co-founds Anthropic with Daniela Amodei and colleagues", the Anthropic mark, a photo card, then Claude, 2023.
- 05 Machines of Loving Grace, his October 2024 essay: "a country of geniuses in a datacenter" over a Blender flyover of a city built from server racks with light pulses running through it, then "the compressed 21st century" and the essay's five domains.
- 06 Finale: his name, "Co-founder & CEO, Anthropic", his portrait, the list of chapters, and the trace from the prologue firing once on the last chord.

A portrait is supplied at photos/dario.jpg. Use it on the chapter 04 card and in the finale, graded into the film's duotone. Stick to public facts only, and end on a small "fan-made, not affiliated" line.

Render it, look at your own frames, and fix whatever looks off before you hand it over.
```

## 3 — INTERFACE

```text
Make INTERFACE: a 25-second square motion reel, 1440×1440 at 60 fps, one MP4 with sound. It shows an AI model making a film, told entirely through product UI.

Every frame and every sound has to come from code: skia-python for the pictures, numpy for the audio. No editor, no samples. Use a clean, premium product look: a warm light-grey canvas with a dot grid, white rounded cards with soft shadows, black pill buttons, Inter with JetBrains Mono, and a single clay accent. Every toggle, pill and pop runs on a spring, the easing is snappy cubic-bezier, reveals blur in, and a real cursor moves in arcs, presses down and leaves a ripple on each click. Put motion blur on everything.

Lay every component out on one big board and fly a camera over it: pan, zoom, roll and a 3D tilt (a homography), with whip pans between scenes. The music is 120 BPM garage-flavoured house in F♯ minor, 12 bars. Every click, keystroke, streamed token, toggle and chime gets its own sound on the grid.

Beats:
1. Model picker: the selection pill springs from Astra 6 to Gemini 3.8 to Fable 5.1, each shown with its logo, and Fable's model card drops in.
2. Composer: type "make a motion film about the three frontier models, every frame in code". Chips pop in (1920 × 1080, 60 fps, Fable 5.1, Effort · max), then press Send.
3. Fable 5.1 streams its answer live. A "Thinking" shimmer shows grey thought lines that fold away into "Thought for 12s". The plan streams in word by word, with fresh tokens tinted clay. A numbered list follows, with inline logos, then a syntax-highlighted Python block that types itself out and gets copied. Last comes a "Render the-frontier.mp4" tool call with a progress bar, a frame counter running up to 1,584 and a film strip that fills with thumbnails, and a "ready" toast.
4. Player: click Open and the camera whips to a player that plays the finished film with its soundtrack coming out of the player, then scrubs at varispeed to the Fable section. Use real frames and audio from THE FRONTIER if you made it; otherwise render a stand-in.
5. Settings: toggle Film grain, then Dark mode. The whole board flips dark in a circular wipe that starts at the switch. Drag Effort to max.
6. Stats: a segmented control switches between the three films, and the numbers roll digit by digit over a loudness chart with a hover tooltip.
7. The drop: the camera pulls back and the board tilts into a 3D overview. A light sweep glints across it, the cursor's path draws itself through every click with numbered markers, and counters roll up (clicks, keystrokes, words streamed, frames).
8. Ship: press ⌘K, type "ship", press Enter. The palette collapses into a pill that reads "Every frame is code", with the three model logos under it.

Render it, look at your own frames, and fix whatever looks off before you hand it over.
```
