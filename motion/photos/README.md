# Photos and soundtracks

The Dario Amodei tribute can include photographs. Put them here and re-render with `python3 -m dario.main`:

| File | Where it appears |
| --- | --- |
| `dario.jpg` | the finale switches to a portrait layout: the photo on the right, the name on the left |
| `anthropic-hq.jpg` | chapter 04 shows it as a card beside the year, captioned *Anthropic · San Francisco* |
| `credit.txt` | one line of photo credit, printed small in the finale |

Photos are rendered in the film's ink-and-cream duotone. The photographs belong to their owners; they are kept
here, with the soundtracks below, so every film rebuilds as it was delivered.

AGI WEEK (`python3 -m agiweek.main`) needs `agiweek/amodei.jpg`, `altman.jpg`, `hassabis.jpg`, `zuckerberg.jpg`
and `musk.jpg` (the founders), and `agiweek/sound.wav`, the reference clip's soundtrack, which the film is cut to:
`ffmpeg -i clip.mp4 -vn -ac 2 -ar 48000 photos/agiweek/sound.wav`.

DEVDAY 2026 (`python3 -m devday.main`) needs `devday/sound.wav`, the teaser's soundtrack, which the film is cut to:
`ffmpeg -i teaser.mp4 -vn -ac 2 -ar 48000 photos/devday/sound.wav`. The team chart takes `devday/altman.jpg`,
`chen.jpg`, `brockman.jpg` and `sottiaux.jpg` (head and shoulders; anyone without one is shown by initials, and
`CROP` in `devday/team.py` sets the square to use).

HORIZON (`python3 -m horizon.main`), SPARKS (`python3 -m sparks.main`) and TOMO (`python3 -m tomo.main`) need
`horizon/sound.wav`, `sparks/sound.wav` and `tomo/sound.wav`, their reference films' soundtracks, which they are
cut to (extracted the same way). Their Blender renders are kept in `out/plates/` (see the main README). The VEEE
spot's soundtrack (`veee/sound.wav`) and the CLAUDE CODE spot's (`crew/sound.wav`) are kept too, though those spots
were replaced by TOMO and SPARKS. ARNAUD'S takes `arnauds/pizza.jpg`, `sushi.jpg`, `ramen.jpg` and `dining.jpg`.
