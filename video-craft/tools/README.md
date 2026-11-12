# Reference-video study tools

How the [Tender study](../references/tender-launch-film.md) was measured, packaged so any reference
video can be broken down the same way.

```bash
python3 -m venv /tmp/cv && /tmp/cv/bin/pip install numpy scipy opencv-python-headless pillow
video-craft/tools/study_video.sh <video.mp4> <outdir> /tmp/cv/bin/python     # ~30 s for a 30 s clip
```

| Step | Script | Output |
|---|---|---|
| Frames + audio | ffmpeg (in the runner) | `frames/f%04d.jpg`, `audio/ref.wav` |
| Contact sheets | `sheets.py` | `sheets/sheet_NN.jpg`, 48 labelled frames each. **Look at every sheet.** |
| Cut metrics | `cuts.py` | `metrics.json`: luma diff, HSV-histogram distance (`hd`), edge change, brightness, saturation, hue |
| Motion + colour | `motion.py` | `motion.json`: per-frame zoom/roll/shift from tracked corners, dark-ink box on light frames, 5-colour palette |
| Spectrogram + tempo | `audio.py` | `aud/spectrogram.png` (+ `spec_N.png` crops), onset envelope, band energies, loudness curve |
| Precise onsets | `onsets.py` | `aud/onsets.json` (kick / clap / hat), `aud/envelopes.png` |
| Beat grid + sync | `beatgrid.py` | `aud/grid.json`: BPM, downbeats, every cut's bar/beat and offset |

Then:
- Read text and detail at full size: put 2×2 frames at 960×540 in one image.
- Find each section's palette by sampling saturated pixels, not fixed boxes.
- Compare each bar's band energies to find the arrangement (intro without bass, drop, breaks).

Notes:
- Kick onsets from a low band-pass come out ~30–40 ms late. Lock the grid to the claps/snare;
  the runner picks the downbeat phase where the kicks land.
- STFT-based beat trackers run ~20 ms early (half the window). Don't use them for frame-level sync claims.
- Per-frame zoom from `motion.json` shows easing directly: decelerating values = ease-out,
  growing values = ease-in.
