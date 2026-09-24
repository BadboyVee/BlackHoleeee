# Earthside

A freight-tracking dashboard built around a live 3D Earth, with the rest of the solar system in
the sky behind it. One `index.html`, no build step. Three.js loads from a CDN and the Earth
imagery lives in [`tex/`](tex/).

**▶ https://badboyvee.github.io/BlackHoleeee/earthside/**

Or serve the folder locally. Browsers won't upload files opened straight from disk into WebGL,
so the Earth needs a web server:

```sh
python3 -m http.server 8000   # then open http://localhost:8000
```

## What's on screen

- **The Earth.** NASA Blue Marble imagery with bathymetry, graded toward deep blues, plus a
  drifting cloud layer that casts soft shadows. The night side shows city lights, and specular
  glint on the oceans. The atmosphere is worked out per pixel from how close each view ray passes
  the planet, so it is thin and bright at the limb and goes dusk-orange along the terminator.
- **One Sun.** A single light direction drives the Earth's terminator, the phases of every planet
  and the Moon, and the shadow Saturn throws across its own rings.
- **The neighbours.** Jupiter, Saturn with its rings (including the Cassini division and the Encke
  gap), Mars, Neptune and the Moon are procedural. Their surfaces are rendered once into textures
  at start-up, over a baked Milky Way and about 5,000 stars. The sky shifts with the pointer on
  desktop and with the scroll position on phones.
- **Live shipments.** Sea legs follow real lanes: Malacca, Suez, Gibraltar, the Luzon Strait.
  Air legs arc high along the great circle. The part already sailed is brighter, and each vessel
  sits at its real progress. Click a row to fly to it.
- **Risk watch.** Pulsing zones for a storm, port congestion and a canal draft limit. The storm
  sits on the lane SHP-2093 is about to sail through.
- **Route planner.** Pick two ports and a mode for the great-circle distance, an estimated
  transit time and arrival date, and CO₂ per tonne (about 12 g/t·km by sea, 600 g/t·km by air).
  The route draws itself on the globe.
- **Orbit view.** Pulls the camera back and up to show the Moon on its orbit.

All figures are sample data and are labelled that way on the page.

## Controls

| Input | Action |
| --- | --- |
| Drag the globe | Rotate (with inertia) |
| Scroll / pinch / `+` `−` buttons | Zoom |
| Arrow keys (globe focused) | Turn 8° at a time |
| Earth / Orbit | Switch camera |
| ⏸ | Pause or resume the slow spin |
| Shipment, risk or 🔔 | Fly to it |

## Layout

Desktop is a three-column instrument layout with the planet in the middle. Below 1100 px wide
(or 640 px tall) the page becomes a single scrolling column on phones and two columns on tablets.
The globe scrolls with the content while the sky stays put. The globe camera is re-framed every
frame onto whatever box `#globeSlot` occupies, so the planet always fits its slot.

## The prompt

Built with [Claude Code](https://claude.com/claude-code), starting from a screenshot of a
"Global View" logistics dashboard and:

> rebuilding a 3D globe dashboard from a reference image — pls quality and fast

then, a few minutes in:

> Don't make it identical to the reference. Something new and different. You can add solar
> planets in background

## Credits

Earth imagery is from NASA Visible Earth (public domain): Blue Marble: Next Generation with
topography and bathymetry, the Earth at Night city lights, and a cloud-cover composite. It was
taken from the example assets in the [`three-globe`](https://github.com/vasturiano/three-globe)
npm package (MIT) and repacked. `earth-data-2k.jpg` stores city lights, clouds and a water mask
in its red, green and blue channels. Fonts are Unbounded, Manrope and JetBrains Mono from Google
Fonts. three.js r160.
