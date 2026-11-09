# Voxel Pagoda

A five-story Japanese pagoda in a spring garden, built entirely from cubic voxels and
path-traced: live in the browser, as a 4K still, and as a short orbit video.

![Voxel pagoda](render-4k.jpg)

- **`index.html`** is the interactive version. Open it and drag to orbit, scroll or pinch to
  zoom. It path-traces the scene on the GPU and keeps refining while the camera is still.
  It needs WebGL2 and about 70 MB of video memory; without those it shows the still instead.
- **`flythrough.mp4`** is a 1080p clip of the camera swinging around the pagoda.
- **`render-4k.jpg`** is the 3840 × 2160 still.

Nothing is modelled by hand or loaded from disk. The generator at the top of `index.html`
places every voxel procedurally into a 512 × 256 × 480 grid (about 14 million solid cubes): the pagoda with
its vermilion pillars, bracketed eaves, swept teal tile roofs and gold finial; cherry
trees, a bamboo grove, maples and ginkgos on stepped stone mounds, a pond with a bridge,
koi and lily pads, stone lanterns, and a few birds. The page and the offline renderer both
run that same code, so they show the same garden.

Open `index.html` directly, or serve the folder:

```sh
python3 -m http.server 8000
```

## Rendering the still and the video

```sh
node tools/export.js scene.bin                      # build the grid (~4 s)
gcc -O3 -march=native -ffast-math -pthread -o pt tools/pathtracer.c -lm
./pt scene=scene.bin out=frame.f32 w=3840 h=2160 spp=40
python3 tools/tonemap.py frame.f32 3840 2160 render-4k.jpg
python3 tools/flythrough.py ./pt scene.bin flythrough.mp4   # needs ffmpeg
```

`tools/pathtracer.c` is a small CPU path tracer (the page carries a GLSL port of it): a
disc sun with soft shadows, a sky dome, diffuse bounce light, light passing through leaves
and blossoms, reflective water and a little haze. More `spp` gives a cleaner image; it costs about 3.5 s per sample at
4K on four cores. `tonemap.py` needs `numpy` and `Pillow`.

The camera and sun are set at the end of the generator in `index.html`; `eye=`, `target=`, `fov=` and
`sun=` on the `pt` command line override them.
