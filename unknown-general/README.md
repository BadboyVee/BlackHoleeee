# 名もなき将軍 · The Unknown General

A 15-second feudal-Japan NFT crossover trailer. Four generals meet in a castle courtyard at dusk.
Then a stranger with green eyes rides in through the gate, and none of them knows who he is.

**▶ [Watch the MP4](the-unknown-general.mp4)** · [play it live](https://badboyvee.github.io/BlackHoleeee/unknown-general/)

| Time | Scene | What happens |
| --- | --- | --- |
| 0–5 s | The Royal Summit | A black-and-gold castle in mist and cherry blossom, then the four generals trading nods in the courtyard |
| 5–10 s | An Unexpected Arrival | The light dims and hooves sound. The gate opens and the rider comes out of the light. A low-angle tilt shows him from hooves to hood |
| 10–15 s | Who Is He? | He halts in front of the generals. 「誰だ、あの男は？」 *Who is that man?* 「なんという威圧感だ……」 *What an overwhelming presence…* Then a close-up and a cut to black |

## Characters

The NFT art is used as drawn. Each original sits in `assets/ref/`, and `tools/cutouts.py` only removes
the background around it.

- **The stranger (green eyes)**: the eyes, red flame and green-bladed katana are taken straight from
  the NFT. The final close-up keeps the NFT's own layout, with the eyes above the blade, framed by a
  hood. He wears a hood and mantle over lacquered shoulder armour, with a black haori and crimson and gold trim.
- **The generals** (bucket hat, crowned bear, pixel shades, blindfolded fish): faces and outfits are
  untouched. Shoulder plates, tassets, hakama and a cape are fitted around each one. Each also carries
  a war flag based on their own art: the bear's crown, the fish's blindfold and bubble, the bucket hat's
  swirl, and the pixel general's red-and-white rays. The pixel general's armour is drawn in its own pixel grid.
- The bucket-hat NFT is cropped by its own frame, so the hat crown and right cheek are closed off in
  the same thick-outline style. That way he can stand full-figure in the wide shots.

## How it's made

`index.html` draws every frame on a canvas as a pure function of time. The castle, gate, banners,
sakura, mist, horse (with an IK walk cycle) and rider are all procedural. The score is synthesised with
Web Audio: taiko, koto, shakuhachi, wind, a creaking gate, and hoofbeats driven by the same gait clock
as the picture. Japanese dialogue appears as subtitles. It isn't voiced.

```sh
python3 -I tools/cutouts.py            # re-cut the characters (needs Pillow + NumPy)
node tools/render.cjs video            # -> the-unknown-general.mp4 (1920x1080, 30 fps, AAC)
node tools/render.cjs stills out 3.4 11.8   # grab frames
```

Rendering uses Playwright's Chromium and ffmpeg. Fonts are Shippori Mincho B1 and Cormorant Garamond,
loaded from Google Fonts.
