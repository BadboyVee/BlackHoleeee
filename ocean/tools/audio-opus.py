#!/usr/bin/env python3
"""Compact Opus copies of the sounds for the one-file build (tools/build-single.mjs).

The game served from a web server plays assets/audio/*.mp3; the one-file build
embeds these Ogg Opus copies instead (about a third of the size), which keeps
the single html small enough to pass around.

  pip install av
  python tools/audio-opus.py        # assets/audio/*.mp3 -> assets/audio/opus/*.ogg
"""
import pathlib

import av

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'assets' / 'audio'
DST = SRC / 'opus'
KBPS = 48          # per stream; plenty for these ambience beds and effects

DST.mkdir(exist_ok=True)
for mp3 in sorted(SRC.glob('*.mp3')):
    out = DST / (mp3.stem + '.ogg')
    with av.open(str(mp3)) as src, av.open(str(out), 'w', format='ogg') as dst:
        ins = src.streams.audio[0]
        enc = dst.add_stream('libopus', rate=48000, layout=ins.layout.name)
        enc.bit_rate = KBPS * 1000
        # 24 kHz sources hold nothing above 12 kHz: don't spend bits on it
        enc.options = {'cutoff': '12000' if ins.rate <= 24000 else '20000'}
        for frame in src.decode(ins):
            frame.pts = None
            for packet in enc.encode(frame):
                dst.mux(packet)
        for packet in enc.encode(None):
            dst.mux(packet)
    print(f'{out.relative_to(ROOT)}: {mp3.stat().st_size / 1024:.0f} KB -> {out.stat().st_size / 1024:.0f} KB')
