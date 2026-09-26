"""Render a grid of stills for quick review: python3 tools_stills.py film out.png t1 t2 ..."""
import os, sys, time
import cv2, numpy as np
from engine.render import Renderer
from engine.core import FPS

def grid(film, times, out, scale=0.33, cols=4, mb_cap=3):
    r = Renderer(film, scale)
    tiles = []
    for t in times:
        s = time.time()
        img = r.frame(int(round(t * FPS)), mb_cap)
        cv2.putText(img, f"{t:.2f}s", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 60, 60), 2)
        tiles.append(img)
        print(f"t={t:.2f} {1000*(time.time()-s):.0f}ms", flush=True)
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(out, cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR))

if __name__ == "__main__":
    which = sys.argv[1]
    P = os.environ.get("PLATES", "/tmp/plates") + "/"
    if which == "frontier":
        from frontier.film import Frontier
        film = Frontier("out/frontier_levels.npz", P + "monoliths")
    elif which == "interface":
        from interface.film import Interface
        film = Interface()
    else:
        from dario.film import Dario
        film = Dario("out/dario_levels.npz", P + "datacenter")
    grid(film, [float(x) for x in sys.argv[3:]], sys.argv[2])
