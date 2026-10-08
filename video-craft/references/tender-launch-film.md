# Tender launch film: a frame-by-frame study

Studied 2026-10-08 from `VID-20261008-WA0039.mp4`, a WhatsApp copy the user sent as a reference for
their own work. I watched every one of the 772 frames, measured the music to the millisecond, and
lined the two up. The raw measurements are in
[`tender-launch-film.data.json`](tender-launch-film.data.json). The reusable rules drawn from this
study are in [`../PLAYBOOK.md`](../PLAYBOOK.md).

**What it is:** a 30.9 s launch film for *Tender*, a crypto checkout ("Any coin in. One asset out.",
live on Monad, 30 chains). It's a premium mix of an Apple-style 3D product film and a fintech UI demo.
The design is white and near-black with one gold accent, serif headlines, monospace data labels,
and every move locked to a 124.6 BPM house track.

| | |
|---|---|
| Picture | 1280×720, **25 fps**, H.264 High ~4.95 Mbps, 772 frames |
| Sound | AAC 44.1 kHz stereo; **−11.4 LUFS** integrated, 2.3 LU range, true peak **+0.3 dBFS** |
| Length | 30.88 s = **exactly 16 bars** of the track (downbeat 1 at 0.104 s, bar 17 would land at 30.927 s) |
| Music | 124.58 BPM, 4/4, F major; beat 481.6 ms, **bar 1.926 s** |

---

## 1. Why it works, in ten lines

1. **One idea per bar.** Sixteen bars, about sixteen ideas. Every section change lands on a bar downbeat.
2. **Cut a frame early.** Hard cuts land 8–43 ms (≤ 1 frame) *before* the downbeat, so they feel exactly on it. Multi-frame transitions (white-outs, washes) start 2–3 frames early so they *resolve* on the beat.
3. **Words ride the rhythm.** Single words change on beats or on the syncopated chord stabs ("Tender", "Any coin", "in." all land on off-beat "ands").
4. **Every shot breathes.** It lands fast and decelerates, drifts while the content plays, then accelerates into the next cut. There's no dead stop and no constant speed.
5. **Type becomes product.** The "O" of "One" turns into a camera lens on the drop, the film's signature match-cut.
6. **The music's structure is the story's structure.** No-bass intro → drop on the product reveal → stutter break at the midpoint → "All new checkout design" opens the second half → final hit on the logo.
7. **Restraint.** A white void, near-black ink and one gold accent. Colour means something when it appears: gold = the brand and "done".
8. **A three-voice type system.** A serif for promises, a monospace for data and machine states, a native-looking sans for UI. "SETTLED" flips from mono to serif: machine → human.
9. **Real-world anchors.** The native iOS camera, lock screen, notification and home screen make it believable.
10. **Ring composition.** It opens on the logo and "Any coin in. One asset out." and closes on the logo and the same line in mono.

---

## 2. Macro structure

Two halves of 8 bars. The first sells the *idea*, the second shows the *product*.

| Bar | Time (s) | Chapter | What the bar says | Main image |
|---:|---|---|---|---|
| 1 | 0.10–2.03 | Hook | Introducing Tender. Any coin in. | Words on white, one per stab |
| 2 | 2.03–3.96 | Promise | One asset out. | The line, then a dive into its "O" |
| 3 | 3.96–5.88 | **Drop / reveal** | Scan with any camera | O → lens → phone; camera module |
| 4 | 5.88–7.81 | Use case | Always on. 24/7. | Sky time-lapse day→night behind a full checkout |
| 5 | 7.81–9.74 | Scale | 30 chains. Accepted. | Floating phones in a white void |
| 6 | 9.74–11.66 | Craft | (letters scatter) | Phones regroup, dive to a QR screen |
| 7 | 11.66–13.59 | Brand echo | (silent) | Three phones crossed into the logo's X |
| 8 | 13.59–15.52 | **Break** | (silent) | Macro of metal edges → strobe on stutter hits |
| 9 | 15.52–17.44 | Chapter 2 | All new checkout design. | Scattered kinetic type → Tender lockup on gold |
| 10 | 17.44–19.37 | Overview | (screens) | Fan of five phones |
| 11 | 19.37–21.30 | Feature | One QR, every chain. | QR cycling chains, then shattering |
| 12 | 21.30–23.22 | Feature | (scan) | Native camera detects the QR |
| 13 | 23.22–25.15 | Feature | (merchant view) | Payments list, chain picker, notification, card, home screen |
| 14 | 25.15–27.07 | Feature | How much have I been paid? | AI assistant answers "$1,284.50 this week" |
| 15 | 27.07–29.00 | Payoff | Scan. Send. Settled. | Three-word stack |
| 16 | 29.00–30.93 | Sign-off | That's Tender. → logo → tags | Line, logo, inverse flash, three mono tags |

Story devices:
- **Day to night = "24/7".** The sky goes from overcast day through sunset to night in about 1.8 s behind one checkout. The tagline is *shown*, not explained.
- **The X recurs:** logo → gold phone back → three phones crossed into an X (bar 7) → app icon → card → logo.
- **Merchant vs buyer:** the first half is the buyer paying, the second half is the merchant getting paid ("You just got paid", payments list, "How much have I been paid?").
- **Parallel copy:** "Any coin in. / One asset out." · "Scan. Send. Settled." · "That's Tender." Short declaratives with full stops; the full stop is a beat.

---

## 3. The soundtrack

**Track profile.** House / UK-garage style at **124.58 BPM** in **F major**, with the bass holding F
the whole way, which makes it endlessly loopable and easy to cut anywhere.

**Groove (measured):** claps on **beats 2 and 4**; the kick/808 hits on 16ths **0, 3, 6, 10** (on 1, on the "a" of 1, on the "and" of 2, on the "and" of 3); off-beat hats; long sub tails with sidechain pumping (the loudness rises sharply and decays on every hit).

**Arrangement, bar by bar** (sub energy relative to the drop):
- **Bars 1–2:** intro with *no sub or bass* (−64 dB vs −20 dB after), about 12 dB quieter overall. Syncopated chord stabs carry the rhythm. Build-up hits start at 2.6 s and grow toward the drop.
- **Bar 3 (3.957 s):** **the drop.** Sub and bass slam in (+44 dB in the sub band), the loudest bar of the film. This is exactly where the "O" becomes the lens.
- **Bars 4–7:** steady groove.
- **Bar 8:** brighter (spectral centroid ~3 kHz vs ~2.4 kHz) as a riser enters. Then **stutter hits at 14.54, 14.66, 14.79 and 15.02 s**, and a **0.36 s near-silent gap (15.14–15.50 s)** right before the bar-9 downbeat. This is the classic pre-drop hole.
- **Bars 9–15:** groove.
- **Bar 16:** brighter again (closing riser), **final hits at 29.96 and 30.06 s**, and the music stops around 30.56 s, just before where bar 17 would land.

**Mix:** −11.4 LUFS integrated (loud, made for social feeds), only 2.3 LU of loudness range, true peak +0.3 dBFS. That peak means it clips slightly; **don't copy it, keep ≤ −1 dBTP**.

**Sound design:** music-led, no voice-over. Added effects are sparse and sit on picture events
(found where the audio departs from the loop; the labels are inferred):
- a swipe at the slide-to-pay (~6.8 s);
- a glitch burst under the strobe (14.6–15.2 s);
- a pop on the QR detection (~22.2 s);
- an impact under the inverse logo flash (~30.2 s).

The intro words ride the chord stabs rather than added sounds.

---

## 4. Sync map: picture against music

Downbeats: 0.104 · 2.030 · 3.957 · 5.883 · 7.810 · 9.736 · 11.663 · 13.589 · 15.516 · 17.442 ·
19.368 · 21.295 · 23.221 · 25.148 · 27.074 · 29.001 (· 30.927)

| Frame | Time | Bar.beat | Event | Offset to the musical point |
|---:|---:|---|---|---|
| 14 | 0.56 | 1.2 | "Introducing" | −26 ms to beat 2 |
| 21 | 0.84 | 1.2& | "Tender" | +14 ms to the "and" of 2 |
| 33 | 1.32 | 1.3& | "Any coin" | +12 ms to the "and" of 3 |
| 45 | 1.80 | 1.4& | "in." | +10 ms to the "and" of 4 |
| 51 | 2.04 | 2.1 | "One asset out." | +10 ms |
| 98 | 3.92 | 3.1 | **O → lens (drop)** | −37 ms |
| 146 | 5.84 | 4.1 | lens → sky | −43 ms |
| 193 | 7.72 | 5.1 | white-out → phones | −90 ms (end of a 4-frame white-out) |
| 206 / 218 / 230 | 8.24 / 8.72 / 9.20 | 5.2 / 5.3 / 5.4 | "30" / "chains" / "Accepted" | −51 / −53 / −55 ms |
| 293 | 11.72 | 7.1 | three phones X | +57 ms (lands at the end of a dive) |
| 363 / 366 / 369 / 375 | 14.52 / 14.64 / 14.76 / 15.00 | 8.3–8.4 | strobe frames | each within ~25 ms of a stutter hit |
| 400 | 16.00 | 9.2 | "checkout" | +3 ms |
| 424 | 16.96 | 9.4 | Tender lockup | 0 ms |
| 437 | 17.48 | 10.1 | phone fan | +38 ms |
| 484 | 19.36 | 11.1 | cut to black, "One QR…" | −8 ms |
| 532 | 21.28 | 12.1 | native camera | −15 ms |
| 557 | 22.28 | 12.3 | QR detected pill | +22 ms |
| 579 | 23.16 | 13.1 | payments list | −61 ms |
| 592 | 23.68 | 13.2 | chain checklist | −23 ms |
| 689 | 27.56 | 15.2 | "Send." | +4 ms |
| 701 | 28.04 | 15.3 | "SETTLED" | +3 ms |
| 725 | 29.00 | 16.1 | "That's" | −1 ms |
| 737 | 29.48 | 16.2 | "Tender." | −2 ms |
| 748 | 29.92 | 16.3 | logo | −44 ms |
| 751 | 30.04 | — | inverse flash | on the 30.06 s final hit |
| 760 | 30.40 | 16.4 | "ANY COIN IN. ONE ASSET OUT." | −45 ms |

Rules this shows:
- **Hard cuts land on downbeats, 0–1 frame early.** The eye needs ~1 frame longer than the ear, so an early cut reads as on-beat. Transitions spanning several frames start 2–3 frames early and resolve on the beat (the white-out ends −90 ms, the payments wash settles at +19 ms).
- **Words land on beats (2, 3, 4) or on the stabs' "ands".** Text never lands at a random time.
- **Moves that *arrive* at a beat end on it.** The dive into the "O" peaks on the drop; the dive into the X lands just after (+57 ms).
- **The strobe is the sound made visible:** one flash frame per stutter hit.
- **Inside a bar, UI micro-events land on 8ths:** QR swaps every 5–6 frames (≈ an 8th note, 241 ms); chain checks on 16ths/8ths.
- **The closing words are sample-tight** (±4 ms): "Send." on 2, "SETTLED" on 3, "That's" on 1, "Tender." on 2.

---

## 5. Shot by shot

Frames are at 25 fps (frame n starts at n/25 s). The motion figures are per-frame zoom measured with tracked features.

**Bar 1: hook (f0–50).** Pure white, nothing but type.
- f0–13: the logo mark (54×58 px at 720p, 4% of the width), dead centre and static.
- f14 "Introducing", f21 "Tender", f33 "Any coin", f45 "in.": each **hard-swaps in place** at the centre, with no fade, no motion and no blur. Hard swaps on stabs read as confident.
- Hero serif cap height is 42 px at 720p (5.8% of the height, ~62 px font). Tiny type, huge white space.

**Bar 2: the promise and the dive (f51–97).**
- "One asset out." holds still for 12 frames (one beat).
- Then the camera dives: zoom per frame goes +1, +2, +3.6, +4.6 … +11.6, +19.8, +22, **+36.9%**, a pure ease-in.
- The camera also rolls +62° and the line goes into 3D perspective: depth of field blurs "asset out." while "One" stays sharp, with directional motion blur.
- By f86 the "O" is an extruded 3D ring trailing **stepped echo copies** (discrete ghosts, not smooth blur). Its inside turns grey glass: a lens.

**Bar 3: drop → product (f98–145).**
- **f98: the morph cut on the drop.** The ring becomes a macro of an iPhone Pro camera cluster (graphite and titanium).
- Instant **ease-out pull-back**: −40.7, −24.8, −13.2, −13.4, −13.0, −5.2 … −1.1% per frame. Lens elements fly in with stepped echo trails and the phone back is revealed, rotating.
- f116: a **whip** to the phone's edge (black on white).
- f126–129: a warm **light-streak wipe** reveals the camera module again.
- "Scan with any camera" builds word by word (f129, 131, 134, 137) on a **curved baseline above the phone, in the phone's perspective**. Each word fades in from light grey to black.
- The push accelerates (+3 → +11%, then +19% and +83%) **into the lens**, whose centre blooms into a starburst (the "scan").

**Bar 4: always on (f146–192).**
- After a whip-in, the phone lies tilted against a **sky time-lapse**.
- **"Always on. 24/7."** sits on the same 3D plane as the phone (in perspective, light grey-blue).
- Slow constant push (+1.0–1.8% per frame, about 35° of roll over the bar) while the UI plays the whole payment, roughly 3 frames per state:
  1. 9:41 lock screen
  2. TENDER CHECKOUT $49.00
  3. Pay with 0.00046 BTC ≈ $49.00
  4. Slide to pay (the orange » knob slides)
  5. Paying…
  6. a Detected / Confirmed / Settled tracker
  7. **$49.00 Payment Settled!** ("Fee = 0.4%, arrived in < 60s")
  8. **You just got paid** ("Your buyer paid in Bitcoin. You received USDC on Monad.")
- Meanwhile the sky goes overcast → golden sunset → deep blue night (#DBDCDC → #D2AF8D → #1D253C).
- f189–192: **white-out** while phones fly out at the camera.

**Bar 5: scale (f193–251).** A white void with three or four phones floating at different depths and angles.
- The motion **decelerates** after the cut (flow 94 → 3 px per frame over about 20 frames), then **"30"** lands on beat 2, **"chains"** on 3 and **"Accepted"** on 4.
- In "Accepted" the letters are **coloured by what passes behind them**: black "Acc", white "ept" over the silver phone, gold "ed". Phones pass in front of and behind the word, so the type lives in the 3D space.

**Bar 6: craft (f252–292).**
- "Accepted" **explodes into individual 3D glyphs** (gold and white letters tumbling).
- The phones regroup into a triptych: white, black (QR screen), gold back with the X.
- The camera then dives toward the black phone's screen (+4 … +40% per frame) to set up the next cut.

**Bar 7: brand echo (f293–332).**
- Three phones seen edge-on (gold, black, silver) **cross into an X**, the logo made of product.
- Zoom +13% easing to +1.2% per frame over about 20 frames, then a slow drift. The calmest bar, the eye of the storm.

**Bar 8: break (f333–383).**
- The background slides white → studio grey (#989792) while the push accelerates (+1.4 → +66%) along the gold side rail and buttons.
- Then into an **abstract macro**: a cream/dark diagonal split (#FBF7EB / #2D2C2A).
- f363–383: a **strobe**, one frame per stutter hit:
  1. white with a diagonal line
  2. black (#101010)
  3. white
  4. black
  5. **gold (#C68535)**
  6. white
- The gold frame sits in the musical gap: colour as a drumbeat.

**Bar 9: chapter 2 (f384–436).**
- **"All new checkout design"** builds word by word ("All", "new", "checkout", "design"), each word gliding into place with its own ease-out (flow 50 → 13 px per frame).
- The final layout is staggered, with mixed sizes and baselines, and fills 73% of the width. The camera then zooms (ease-in) into…
- …"Tender" small, then the **lockup**: white "Tender" serif + logo in a black tile, on a **blurred bronze-gold gradient** (#DA9B51 centre, #E9C18B lighter corners).
- The lockup desaturates to grey as it hands off.

**Bar 10: overview (f437–483).**
- A symmetrical **fan of five phones** on white, each screen different:
  - a piggy bank with "You just got paid"
  - Review payment, then Slide to pay
  - the 9:41 lock screen with three Tender notifications
  - TENDER CHECKOUT with a QR
  - gold coins with "$49.00 Payment Settled!"
- The zoom shows the grammar exactly: +16% easing to ~1.9% per frame, steady, then +3.6 → +17.6% into a **whip** that hands off on the downbeat.

**Bar 11: one QR (f484–531).**
- Black. **"One QR, every chain."** in white serif, left-aligned at 5.9% of the width.
- On the right, the checkout QR **swaps chain every 8th note** (BTC → SOL → USDT → USDC → ETH …), each swap with a one-frame glitch dim.
- From f515 the QR **shatters into Voronoi shards with gold rims** that fly toward the camera and dissolve.

**Bar 12: the native camera (f532–578).**
- An iOS camera recreation (EXPOSURE / STYLES / FILTER / ASPECT / NIGHT MODE menu → VIDEO / **PHOTO** in yellow) points at a printed "$12.50 – SCAN OR TAP TO PAY" card.
- It holds still about 1.4 s while the **yellow detection brackets** (f552) and the **"tenderr.xyz" pill** (#F3DC2C, on beat 3) appear.
- Then it accelerates into the pill (+0.4 → +13.9% per frame). This is the zoom-through transition.

**Bar 13: the merchant (f579–622).** Four UI beats in one bar:
1. **Payments list** on warm off-white: All / Paid / Seen on chain / Needs recovery. The black selection pill slides along. Rows show the coin icon, amount in bold sans, "0.2141 SOL · Solana", and a status chip in tracked mono caps ("● SETTLED" on cream, "● SEEN ON CHAIN" on grey) with a relative time.
2. **Chain checklist:** Bitcoin, Solana, Base, Ethereum, Arbitrum, Tron. Each row *lifts with a shadow* when pressed, then fills black with a white check, in rhythm.
3. **Lock-screen notification** "You just got paid · $49.00" over the **black metal Tender card** (gold chip, NFC mark, engraved tracked "TENDER", orange rim light, dot-grid texture).
4. **Home screen:** a pull-back from a giant Settings icon (badge 3) to the grid with the Tender app (X on black).

**Bar 14: assistant (f623–674).**
- **App-open zoom** (from the icon) into a peach gradient (#E8B16B → #DFA156) with a faint dot grid.
- A glossy 3D **mascot**; "Good afternoon" in serif with a sparkle; "Ask anything about your money."
- The field **types "How much have I been paid?"** with an orange caret (about 1–2 characters per frame).
- The send button gets a **glow** (f659–661), then the text **becomes a black chat bubble** that slides up.
- The **answer card** reads "■ ANSWER" in mono, "**$1,284.50** this week, from 38 payments. All settled to USDC on Monad.", with the amount in serif. The mascot switches from neutral to a big smile, and the view pushes in (+10% per frame) to the cut.

**Bar 15: payoff (f675–723).** White.
- **"Scan."** rises out of a baseline mask (about 5 frames, ease-out). **"Send."** rises in grey on beat 2. On beat 3 **"Settled."** rises while *flipping typefaces*: bold black sans → **gold mono caps "SETTLED"** → serif "Settled.".
- The stack is left-aligned at 36% of the width, so the block sits optically centred.

**Bar 16: sign-off (f724–771).**
- "That's" (beat 1) and **"Tender."** (beat 2, gold gradient #9C6A2C → #C88B45) rise out of masks.
- Then the logo on beat 3, an **inverse flash** (white mark on #101010, 3 frames) on the final hit, then three mono tags of about 6 frames each:
  - LIVE ON MONAD · 30 CHAINS
  - ANY COIN IN. ONE ASSET OUT.
  - TENDERR.XYZ
- The tags are 20 px caps at 720p (2.8% of the height), widely tracked and centred, and the film ends.

---

## 6. Typography

| Voice | Use | Look | Free stand-ins |
|---|---|---|---|
| **Editorial serif** | promises, taglines, numbers in the assistant | high x-height transitional serif, regular weight, slightly tight; *Tiempos Headline / Lyon* family feel | Newsreader (Display opsz), Source Serif 4 Display, Libre Caslon Text |
| **Monospace caps** | data labels, machine states, end tags | neutral grotesque mono, all caps, tracking +12–20% | Geist Mono, JetBrains Mono, IBM Plex Mono |
| **UI sans** | anything that's "the product" | SF Pro-like; bold numerals, regular secondary text | Inter, Geist |

How the type behaves:
- **Size:** one hero size all film (cap height ≈ 5.8% of the frame height). The scattered "All new checkout design" is the only big moment (73% of the width). End tags are about a third of the hero size.
- **Position:** dead centre for single statements; left column for stacks and for text beside a device; text *on* 3D planes when it belongs to the object.
- **Colour:** #111111 ink; grey for "pending" ("Send."); **gold only for the brand and for "done"** ("Tender.", "SETTLED", "$49.00", "You just got paid").
- **Animation:**
  - hard swap in place on a stab
  - per-word fade from light grey to ink along a curved path
  - perspective text locked to a 3D plane
  - scattered words, each with its own ease-out, then a camera move through them
  - mask-rise reveal (~5 frames, ease-out)
  - typeface-flip scramble (sans → mono → serif) for transformation
  - typing with a caret in UI
  - glitch-dim swap for data changes
- **Copy:** sentence case, full stops, 1–4 words per beat, parallel triads, concrete numbers ($49.00, 0.00046 BTC, 30 chains, < 60s, $1,284.50, 38 payments).

---

## 7. Imagery and colour

**3D product:** generic iPhone Pro bodies in graphite, natural titanium, white and **gold** (gold ties to the brand). Soft studio light on white, warm rim light on dark; shallow depth of field in macros; **stepped echo trails** instead of motion blur on fast object moves; true motion blur on whips.

**UI design system:**
- **Buyer checkout:** black glass with gold/orange accents and mono labels.
- **Merchant dashboard:** warm off-white, black selection pills and mono status chips.
- **Assistant:** peach gradient, glossy mascot.

UI is never flat on screen for long. It sits on phones in 3D, or the camera zooms through it.

**Real-world anchors:** iOS camera QR detection (yellow brackets, pill), a lock-screen notification, the home screen with badges, the keyboard suggestion bar. Familiar system UI makes a new product feel shipped.

**Colour script** (light ↔ dark alternation is part of the rhythm):

| Bars | Field | Notes |
|---|---|---|
| 1–2 | white #FFFFFF | ink #111111 |
| 3 | white + graphite | metal greys |
| 4 | **sky**: #DBDCDC → #D2AF8D → #1D253C | the only "nature" hues |
| 5–7 | white | gold/black/silver phones |
| 8 | grey #989792 → macro cream/dark → strobe incl. **gold #C68535** | |
| 9 | white → **bronze-gold gradient** lockup | |
| 10 | white | dark screens |
| 11–12 | **black** #0D0D0D | gold shards; iOS yellow #F3DC2C |
| 13 | warm off-white UI → **black card** with gold rim | |
| 14 | **peach-gold** #E8B16B → #DFA156 | |
| 15–16 | white → inverse flash #101010 → white | gold "Tender." |

The palette is white + near-black + **one** gold hue family (#9C6A2C, #BB823A, #C68535, #C88B45, #E8B16B), plus the iOS yellow and a red badge only where the system demands them.

**Composition:**
- centred single elements surrounded by white space;
- a symmetrical fan;
- diagonals in macros;
- text left / device right;
- depth layering (phones in front of and behind words).

---

## 8. Motion language

**The three-phase shot** (measured in nearly every bar):
1. **Impact:** the cut lands moving fast and decelerating (expo-out), e.g. −40.7 → −1.1% zoom per frame after the drop, or +16 → +2% in the fan.
2. **Drift:** slow, near-constant motion (≈ +1–2% per frame or a gentle roll) while text/UI does its job. Never fully static on 3D shots (UI and type shots can sit still).
3. **Throw:** accelerate (expo-in) through the last 0.3–0.6 s into the next downbeat, often finishing in a whip, a white-out, a dive-through or a flash.

**Transition vocabulary:**

| Transition | Where | How it's built |
|---|---|---|
| Morph cut (shape → object) | O → lens (f97→98) | dive into the shape so it fills the frame, cut on the drop to an object with the same silhouette |
| Whip | f115→116, f482→484 | 1–3 frames of heavy directional blur |
| Light-streak wipe | f126–129 | a warm vertical bloom sweeping across |
| White-out | f189–192 | the scene bleaches to white while objects fly at the camera |
| Dive-through | into the lens, phone screen, pill, app icon | accelerating zoom until a detail fills the frame |
| Strobe | f363–383 | one solid frame per stutter hit, one in brand gold |
| Background slide | f333–345 | white void shifts to studio grey under a move |
| Glitch swap | QR chain changes | one dim frame between states |
| Shatter | f515–531 | Voronoi shards with gold rims fly toward the camera |
| Mask-rise | closing words | text rises from behind its baseline in ~5 frames |
| Inverse flash | f751–753 | 3 frames of the logo inverted on the final hit |

---

## 9. How it all flows together

- **The music is the edit's metronome *and* its story arc.** The quiet intro carries the words, the drop carries the product reveal, the break separates the halves, and the final hit lands on the logo.
- **The energy curves line up:** loudness, cut density and camera speed rise and fall together. In the bar-8 break everything accelerates then stops, and the 0.36 s audio hole holds a gold frame and white.
- **Type and image are one material.** Words sit in 3D space, become objects, get coloured by objects, and explode into glyphs; objects form the logo.
- **Tempo inside tempo:** bars carry sections, beats carry words, 8ths/16ths carry UI micro-changes.
- **Contrast keeps attention:** white↔black fields, still↔rushing, tiny type↔huge macro, serif↔mono.

## 10. What not to copy

- **True peak +0.3 dBFS:** it clips. Master to −1 dBTP, around −12 to −14 LUFS for social.
- **25 fps:** fine on the web, but 60 fps is smoother for fast 3D moves (our earlier edit's feedback was "quality so low" at 30 fps).
- **Small text:** the end tags are 2.8% of the frame height, hard to read on a phone. Go ≥ 3.5% for anything that must be read.
- Some UI states flash by in 2–3 frames (e.g. "Paying…"). They're legible only on a pause; fine as texture, not for key information.
