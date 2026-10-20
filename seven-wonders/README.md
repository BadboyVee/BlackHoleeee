# Seven Wonders — an interactive 3D atlas

The Seven Wonders of the Ancient World arranged around a floating island, built with
[three.js](https://threejs.org). One HTML file, no build step, no imported models or
textures — every wonder and surface is generated at runtime.

Open `index.html` in a browser, or serve the folder:

```sh
python3 -m http.server 8000
```

## Controls

| input                     | action                         |
| ------------------------- | ------------------------------ |
| drag / pinch / scroll     | orbit and zoom                 |
| click a wonder or its tag | fly to it and read about it    |
| `1`–`7`                   | jump to a wonder               |
| `T`                       | start or stop the guided tour  |
| `L`                       | toggle labels                  |
| `0` or `Esc`              | return to the overview         |
