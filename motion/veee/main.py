"""Build VEEE: sound, pictures, mux.  python3 -m veee.main [--scale 1.0]

Needs the reference spot's sound, which is not in the repository, as photos/veee/sound.wav
(ffmpeg -i spot.mp4 -vn -ac 2 -ar 48000 photos/veee/sound.wav): the film is cut to it. Its cards and thumbnails
play our own films, printed in dots, so render those first (out/the-frontier.mp4, out/agiweek.mp4,
out/devday.mp4); a missing one prints as a plain dot pattern."""
import argparse
import os
import sys

import numpy as np

from engine.render import render
from . import sound
from .film import Veee

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")
SOUND = os.path.join(HERE, "..", "photos", "veee", "sound.wav")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--mb", type=int, default=None)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(OUT, "veee.mp4"))
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--maxrate", type=float, default=8.0)
    ap.add_argument("--master-dir", default=None)
    ap.add_argument("--sound", default=SOUND)
    args = ap.parse_args()
    if not os.path.exists(args.sound):
        sys.exit(f"no sound at {args.sound}: the film is cut to the reference spot's soundtrack")
    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(OUT, "veee.wav")
    x = sound.prepare(args.sound, wav)
    print(f"sound: {len(x) / 48000:.2f} s, peak {np.abs(x).max():.3f}")
    render(Veee(), args.out, scale=args.scale, workers=args.workers, mb_cap=args.mb, audio=wav, step=args.step,
           crf=args.crf, maxrate=args.maxrate, master_dir=args.master_dir, label="veee")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
