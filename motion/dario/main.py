"""Build the Dario Amodei tribute: soundtrack, levels, pictures, mux.

    python3 -m dario.main [--scale 1.0] [--workers 4] [--mb N]
"""
import argparse
import os

import numpy as np

from engine import audio as A
from engine.render import render
from . import music
from .film import Dario
from .score import DURATION

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--mb", type=int, default=None)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--plate", default=os.environ.get("DATACENTER_PLATE"))
    ap.add_argument("--out", default=os.path.join(OUT, "dario-amodei-tribute.mp4"))
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--maxrate", type=float, default=16.0, help="Mbit/s cap for the delivery encode")
    ap.add_argument("--master-dir", default=None, help="where the near-lossless master is kept")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(OUT, "dario.wav")
    x = music.render(wav)
    lv, rms = A.frame_levels(x, 60, 10, DURATION)
    lv_path = os.path.join(OUT, "dario_levels.npz")
    np.savez(lv_path, levels=lv, rms=rms)
    print(f"audio: {A.lufs(x):.1f} LUFS, peak {np.abs(x).max():.3f}")
    film = Dario(lv_path, args.plate)
    render(film, args.out, scale=args.scale, workers=args.workers, mb_cap=args.mb, audio=wav, step=args.step,
           crf=args.crf, maxrate=args.maxrate, master_dir=args.master_dir, label="dario")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
