# The prompts

One-shot prompts for the four films, one per film. They were written after the fact from what was built; the
films themselves came out of a longer back-and-forth. Paste one into a coding agent that has Python, ffmpeg,
skia-python, numpy and Blender's `bpy` available. ARNAUD'S also needs its four photographs attached.

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

## 4 — ARNAUD'S

```text
Make ARNAUD'S, a 27.5-second fan-made concept ad for a real restaurant. The story: an AI concierge on a phone picks the perfect anniversary dinner. It should feel like a premium app-launch ad: springy UI, whip pans, and every move on the beat. Deliver one MP4 with sound (1920×1080, 60 fps, under 30 MB) and a separate clip of just the opening, the first 4.5 seconds.

The restaurant is real, so keep the facts straight:
- Arnaud's, 813 Bienville St, in the French Quarter of New Orleans, serving classic Creole since 1918.
- Dishes: Soufflé Potatoes, Shrimp Arnaud, Bananas Foster.
- Don't invent prices.
- End with a small line: "Fan-made concept · not affiliated with Arnaud's".

I'm attaching four photos: pizza.jpg, sushi.jpg, ramen.jpg, and dining.jpg (Arnaud's main dining room with its chandeliers). Cover-fit and sharpen them, and keep them out of the repository.

Every frame and every sound has to come from code: skia-python for the pictures, numpy for the audio, and ffmpeg for the encode. No editor, no stock footage, no samples.
- Timing: keep one timing sheet at 120 BPM (a beat is 0.5 s, a bar is 2 s; 13 bars plus a tail). The pictures and the music both read from it, so every cut, letter and hit lands on the grid.
- Motion blur: accumulate sub-frames, 6 per frame and 12 around cuts, with a 0.6 shutter.
- Effects: fine film grain, and a short chromatic-aberration hit on the big cuts. No bloom and no vignette, because both grey a light image.

LOOK: four colours, used the same way in every scene, with no scene getting its own colour scheme.
- Ground: one light green, #BDE9A0, lit from the middle (a radial gradient from #D6F2BF to #BDE9A0 to #9FD07D) with slow drifting glows of gold and white. Every scene sits on this ground, from the first frame to the last. There are no black backgrounds anywhere.
- White (#FFFFFF): everything physical, meaning the phone, cards, receipt, printer, terminal, map cards and the name frame.
- Gold (#E3B54F, deep #B8872A, pale #F3DC9A): everything that glows.
  - The signature "frame of light": a soft, blurred stroke of gold and white light that turns slowly around a card.
  - Also the route, the pin, the payment card, the stamp, the orb, and MADE BY VEEE.
- Black (#0A0A0A): type only. Shadows fall dark green (#1D3A12), never black.
- The one vibrant exception is the thinking ring: vivid gold #FFC400, emerald #12B85A and white.
- No purple, no pink, no neon.
- The app inside the phone has no name or mascot. The only signature is MADE BY VEEE at the end.

Type:
- Fonts: Inter for the UI; Instrument Serif for the name and every big display word, with italic for "special."; JetBrains Mono for the receipt and terminal; Archivo (weight 850, wide) for VEEE.
- Big display words are white serif with a black outline outside the letters and a soft shadow, so they read as classy and stay legible on the green.
- Never put gold text or photo-filled letters on the green.

STRUCTURE (times in seconds)

1. The table (0–3.95). A flat-lay kitchen table seen from straight above, in the ground's light green.
- Props: on the sixteenths from 0 to 0.875 s, these drop onto the table: a crusty loaf, two bananas, gold cutlery (a fork and two spoons), a wooden cutting board, a chef's knife, a whisk and a spaghetti server.
- Drops: each prop falls in bigger and higher with a soft, far shadow, then lands with a small overshoot and a tight shadow.
- Performance: bake each prop's blurred silhouette once and reuse it. Blurring full-frame layers per prop makes this scene ten times slower.
- Headline: it pops in letter by letter in big white Inter ExtraBold with a soft dark-green shadow (0.02 s stagger, back-out ease). Each line leaves up and out before the next one arrives:
  - "Choosing dinner" (0.15–0.95)
  - "for your anniversary" (1.02–1.85)
  - "is a lot." (from 2.0; bigger, with a punch on the downbeat of bar 2)
- Fruit: apples, orange halves, strawberries, chillies, tomatoes and green beans keep landing. They come on the eighths from 1.0 s, then on every sixteenth once "is a lot." hits, until the table is crowded.
- The card: at 3.0 a white card with the gold frame of light drops into the middle. From 3.45 the props fly off outward, the green stays, and the card becomes the phone's input box.

2. The ask (3.95–6.12).
- A big white phone, cropped at the bottom (status bar reads 9:30), rises behind the input card. It has a back arrow, an ×, a +, and a black round send button with a gold arrow.
- Slow push-in while the prompt types itself with a thin black caret: "It's our anniversary tonight. Pizza, sushi or ramen? I want something special."
- Send is pressed at 6.12.

3. Giant words (6.12–8.0).
- The camera dives in just behind the caret, through the white of the input.
- On the green, the words type at 420 px, one per half beat: "Pizza," "sushi," "ramen?" "something" "special." ("special." in italic).
- A whip pan between words keeps the caret at about 70% of the frame width. The caret here is a white bar lined in black.

4. Thinking (8.0–10.0).
- Spin in: rotate from −28° to 0° and scale from 1.5 to 1.
- The label "Finding something special", with animated dots, is in the white-serif-with-black-outline style.
- A ring of 44 glossy beads (vivid gold, emerald, white) spins like a loader, with a comet of bigger, brighter beads chasing round it.
- Pizza, sushi and ramen orbit inside the ring as round photo chips with white rims. On beats 2, 3 and 4, one is tossed out of the ring with a spin.
- On the "and" of beat 4, a bright gold Mardi Gras doubloon flips into the middle and lands with a glint and sparkles. It is stamped with an A, with "ARNAUD'S · 1918" round the rim.

5. Carousel and the dining room (10.0–12.1).
- White menu cards race in from the right over the green and brake with a quintic ease-out, so that Arnaud's stops dead centre on the downbeat.
- Each card has a photo, a badge pill, a rating pill, a serif title, a line of description, time and distance icons, and a gold price:
  - Pepperoni Pizza: Most Popular, 4.6, $18
  - Salmon Maki: Fresh Today, 4.7, $16
  - Shoyu Ramen: Cozy Pick, 4.8, $15
- Arnaud's card is white edged in gold, with a gold "Something special" badge, "Classic Creole in the French Quarter", "813 Bienville St" and a gold Book pill. It lifts out on a spring while the others dim.
- Its photo then opens to fill the frame: the dining room with a slow push-in, and the chandelier bulbs (detect them in the photo) glinting on the beat.
- Title: "Arnaud's", with "CLASSIC CREOLE · FRENCH QUARTER · SINCE 1918" beneath.

6. The cashier (12.1–16.0). A whip down to the counter, back on the green.
- The receipt: a white thermal printer feeds it out line by line:
  - Arnaud's
  - 813 BIENVILLE ST · NEW ORLEANS
  - CLASSIC CREOLE · EST. 1918
  - TONIGHT 8:00 PM
  - TABLE FOR 2 · MAIN DINING ROOM
  - PRE-ORDER: 1 SOUFFLÉ POTATOES, 1 SHRIMP ARNAUD, 1 BANANAS FOSTER FOR 2
  - NOTE: HAPPY ANNIVERSARY
  - DUE NOW $0.00
  - PAY AT THE TABLE
  - a barcode
  - RES 0926 · 1918
  - MERCI · THANK YOU
- The terminal: a white payment terminal springs in wearing the frame of light. It shows "Arnaud's", "Table for 2 · 8:00 PM" and "DUE NOW". The amount rolls like a till and lands on $0.00 as the receipt prints the same line. Below it: "Your card holds the table." and a pulsing contactless "Tap to confirm".
- The tap: a gold metal card (•••• 1918) flies in, taps with rings spreading out, and leaves.
- Confirmed: the screen floods gold from the tap point, with a white check, "Confirmed" and "See you at 8:00 PM". The receipt is stamped CONFIRMED in deep gold.

7. The walk (16.0–20.0).
- A gold circle blooms from the tap, and the map opens inside it.
- The map is a tilted 3D day map of the real French Quarter grid:
  - Streets: Decatur, Chartres, Royal, Bourbon, Dauphine, Burgundy and N Rampart, crossed by Canal through Dumaine.
  - Light-green blocks, white streets, the Mississippi in pale teal, and Jackson Square.
- A gold route with a white casing draws from Canal St down Bourbon to 813 Bienville. A white-and-gold dot walks it.
- A gold pin with an A carries a white label card.
- A white booking card drops in at the top: "Table for 2 at Arnaud's · Tonight · 8:00 pm · 813 Bienville St, New Orleans", with a gold check.
- A chip counts "7 min walk" down to "You're here".
- The camera follows the dot, then zooms into the pin and settles into the plain green.

8. The line (20.0–22.0).
- "You were craving" in black Inter, word by word.
- Then a slot rolls pizza → sushi → ramen, each with its round photo chip, and lands on "something special" in bold black with a soft white glow.
- Then "Now your table is waiting." rises in, word by word.

9. The end (22.0–27.5).
- Gold ribbons of light gather and burst on the downbeat into the white frame, edged in turning gold light, with a shockwave ring.
- Inside it:
  - "Arnaud's" rises letter by letter in black Instrument Serif, with a gold light sweep.
  - "813 BIENVILLE ST · FRENCH QUARTER · NEW ORLEANS" follows in tracked gold capitals.
  - "Tonight, something special." sits beneath in italic.
- At 24.25 the frame folds into a liquid gold orb that drifts left.
- At 24.5 the orb signs the film: "MADE BY" in small tracked gold, then "VEEE" in Archivo, graded from deep gold to gold, each letter popping in, followed by a white light sweep.
- Last come the disclaimer and a fade to the light green, not to black.

SOUND

A warm 120 BPM jazz-pop groove in F, synthesised in numpy. It starts on frame one.
- Instruments: kick, a rim-and-clap backbeat, swung sixteenth hats, Rhodes comping, a walking bass ducked under the kick, supersaw brass stabs, piano, bells and pads.
- Chords, one per bar: Fmaj7, Fmaj7, Gm9, C13, Fmaj7, D7, Gm9, C13, Fmaj7, Dm9, B♭maj9, Fmaj7.

Every event gets a sound on the grid:
- The table:
  - Every prop knocks as it touches down: a tom body with a papery clack, and the cutlery rings.
  - The fruit pops climb an F pentatonic scale, and the headline's letters click softly.
  - A reverse crash leads into "is a lot.", which hits with a brass chord, piano, a sub drop and an impact.
  - The card lands with a whoosh, a thud and a shimmer.
- The ask and the words: keys for the prompt, a click and a whoosh on send, and a punch on each giant word.
- Thinking: the beads rattle, each toss gets a whoosh and a blip, the coin spins and rings, and the groove is muffled behind a low-pass while it thinks.
- Carousel: clicks as the cards pass, and a brass swell as the dining room opens.
- Checkout: a printer zip per receipt line over a motor hum, a till roll, the terminal's double beep and approved bells, and a rubber-stamp thump.
- The walk: a rising tone as the route draws, and footsteps.
- The end: a final chord at 22.0, a reverse whoosh into the orb, and a hit plus a bell for each letter of VEEE.

Master to −12 LUFS with a −1 dB ceiling.

FINISH

Render in parallel chunks to a near-lossless master, then encode H.264 at about CRF 20 with an 8 Mb/s max rate. Look at contact sheets of your own frames, transitions included. Fix anything off before you hand it over: overlapping text, a cropped word, anything off-palette, anything hard to read on a phone screen.
```
