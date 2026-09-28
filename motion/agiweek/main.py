"""Build AGI WEEK: soundtrack, pictures, mux.  python3 -m agiweek.main [--scale 1.0]

Needs the founders' photographs in photos/agiweek/ (amodei, altman, hassabis, zuckerberg, musk .jpg); they are not
in the repository. Without them the portraits render as empty frames."""
import argparse
import os

import numpy as np

from engine import audio as A
from engine.render import render
from . import music
from .film import AgiWeek

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--mb", type=int, default=None)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(OUT, "agiweek.mp4"))
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--maxrate", type=float, default=8.0)
    ap.add_argument("--master-dir", default=None)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(OUT, "agiweek.wav")
    x = music.render(wav)
    print(f"audio: {A.lufs(x):.1f} LUFS, peak {np.abs(x).max():.3f}")
    render(AgiWeek(), args.out, scale=args.scale, workers=args.workers, mb_cap=args.mb, audio=wav, step=args.step,
           crf=args.crf, maxrate=args.maxrate, master_dir=args.master_dir, label="agiweek")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
