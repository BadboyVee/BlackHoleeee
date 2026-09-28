# Photos (optional, not committed)

The Dario Amodei tribute can include photographs. Put them here and re-render with `python3 -m dario.main`:

| File | Where it appears |
| --- | --- |
| `dario.jpg` | the finale switches to a portrait layout: the photo on the right, the name on the left |
| `anthropic-hq.jpg` | chapter 04 shows it as a card beside the year, captioned *Anthropic · San Francisco* |
| `credit.txt` | one line of photo credit, printed small in the finale |

Photos are rendered in the film's ink-and-cream duotone. They are git-ignored on purpose: the photographs
belong to their owners, so the repository carries only the code that places them.

AGI WEEK (`python3 -m agiweek.main`) needs `agiweek/amodei.jpg`, `altman.jpg`, `hassabis.jpg`, `zuckerberg.jpg`
and `musk.jpg` (the founders), and `agiweek/sound.wav`, the reference clip's soundtrack, which the film is cut to:
`ffmpeg -i clip.mp4 -vn -ac 2 -ar 48000 photos/agiweek/sound.wav`. The sound is git-ignored for the same reason.

DEVDAY 2026 (`python3 -m devday.main`) needs `devday/sound.wav`, the teaser's soundtrack, which the film is cut to:
`ffmpeg -i teaser.mp4 -vn -ac 2 -ar 48000 photos/devday/sound.wav`. It is git-ignored for the same reason.
