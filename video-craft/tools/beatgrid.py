# Beat grid locked to the claps/snare (beats 2 and 4), bar downbeats, and where each cut lands.
#   python beatgrid.py <onsets.json> <metrics.json> <out.json> [fps] [bpm_guess]
# Cuts come from metrics.json (cuts.py): frames whose HSV-histogram distance jumps (hd > 0.35).
import sys, json
import numpy as np
on = json.load(open(sys.argv[1])); met = json.load(open(sys.argv[2])); out = sys.argv[3]
fps = float(sys.argv[4]) if len(sys.argv) > 4 else 25.0
per0 = 60 / float(sys.argv[5]) if len(sys.argv) > 5 else on['period']
C = np.array(on['clap']); K = np.array(on['kick'])
idx = np.round((C - C[0]) / (2 * per0))
for _ in range(4):
    A = np.vstack([idx, np.ones_like(idx)]).T; (p2, c0), *_ = np.linalg.lstsq(A, C, rcond=None)
    r = C - (c0 + p2 * idx); keep = np.abs(r) < max(0.006, 2.5 * r.std()); C, idx = C[keep], idx[keep]
per = p2 / 2; r = C - (c0 + p2 * idx)
# a clap is beat 2 or beat 4, so the downbeat is one or three beats before it: take the phase the kicks land on
def kicks_on(b1):
    ds = b1 + 4 * per * np.arange(-200, 200); ds = ds[(ds > K.min() - .1) & (ds < K.max() + .1)]
    return int(sum(np.min(np.abs(K - d)) < 0.06 for d in ds))
beat1 = max((c0 - per, c0 + per), key=kicks_on)
first = beat1 - 4 * per * np.floor(beat1 / (4 * per))
end = met[-1]['t'] + 1 / fps
down = [round(float(first + 4 * per * k), 4) for k in range(int((end - first) / (4 * per)) + 2)]
print(f'{60 / per:.3f} BPM, beat {1000 * per:.2f} ms, bar {4 * per:.4f} s, clap fit residual {1000 * r.std():.2f} ms rms (n={len(C)})')
print('downbeats:', down)
cuts = [m for m in met[1:] if m['hd'] > 0.35]
rows = []
for m in cuts:
    t = m['n'] / fps; k = (t - first) / per; kr = int(round(k)); nb = first + per * kr   # nearest beat
    rows.append(dict(frame=m['n'], t=round(t, 3), bar=kr // 4 + 1, beat=kr % 4 + 1, offset_ms=round(1000 * (t - nb)), hd=round(m['hd'], 2)))
    print(f"f{m['n']:4d} {t:7.3f}s  nearest: bar {kr // 4 + 1:2d} beat {kr % 4 + 1}  {1000 * (t - nb):+5.0f} ms  (hd {m['hd']:.2f})")
json.dump({'bpm': 60 / per, 'beat': per, 'downbeats': down, 'cuts': rows}, open(out, 'w'), indent=1)
