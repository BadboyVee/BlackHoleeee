Create a 30-second, 1920x1080, 24 fps cinematic 3D montage called "Lagos 2090 by BreezeOg": an original solarpunk Lagos, video only, no audio. This must look production-grade and real — a theatrical short, not a game-engine blockout and not a low-poly Three.js demo. Work fully autonomously: locate or install what you need, fix every error yourself, never stop to ask, and finish only when ./output/lagos-2090.mp4 is rendered, verified at exactly 30 seconds, and one frame from each shot has been checked.

FIRST STEP (do this before anything else)
This lean pack does not include the 4K textures, HDRIs or high-detail Poly Haven models. They are free and public; download them into this folder first.
- On Windows: from this folder run `powershell -ExecutionPolicy Bypass -File .\fetch-assets.ps1`
- Or run `python fetch_assets.py` (Windows, macOS or Linux).
The script also converts each downloaded Poly Haven model to an Unreal-ready FBX with headless Blender if blender is on PATH (install or locate Blender first if needed). When it finishes, verify every path in ./assets-manifest.json exists on disk — the script prints a verification report. Re-run it if anything is missing. Do not start modelling, importing or rendering until that check is clean.

LOOK_MODE = cinematic
Default is high-fidelity cinematic (Lumen, Nanite, 4K materials, cinematic cameras, volumetric skies). A stylized anime-cinematic look is a toggle only: if, and only if, the user later asks for the anime version, switch to a toon post-process, painterly materials and softer cel lighting. Do not start in the anime look.

PIPELINE
Blender preps and restyles hero meshes headless (`blender -b -P script.py`, or blender-mcp if it is already set up). Export Unreal-ready FBX. Unreal Engine 5.4+ builds the project, levels, lighting, Niagara and a Level Sequence, then Movie Render Queue renders a PNG sequence. ffmpeg encodes the H.264 MP4. Do not use Three.js, Vite, Playwright or a browser screenshot pipeline.

PREREQUISITES (detect these, do not guess)
- Unreal Engine 5.4 or newer. Find it from `C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat`, `C:\Program Files\Epic Games\UE_5.*\Engine\Binaries\Win64\UnrealEditor-Cmd.exe`, or the Epic Games Launcher. Use the newest 5.4+ install. If none is installed, install UE 5.5 or 5.6 via the Epic Games Launcher (include Engine, Visual Studio / IDE prerequisites if the installer asks) and continue.
- Blender 3.6 or newer, already installed on this PC. Find `blender.exe` with `where blender`, under `C:\Program Files\Blender Foundation\`, or in a user install. If it is missing, install Blender 4.5 LTS or newer and continue.
- ffmpeg, in PATH. If missing, install it (winget, choco, or a static build) and continue.
- This project folder, opened at its root (the folder that contains PROMPT.md, fetch-assets.ps1, fetch_assets.py, assets-manifest.json, models and fonts). After the fetch script runs, it will also contain textures, hdri and models/*/hd-*.

ASSETS (after the fetch script has succeeded)
Read ./assets-manifest.json end to end. It lists every file, which shots it suits, its licence, and any scale notes.
- Unreal imports the .fbx files. After a successful fetch, every model has one. High-detail Poly Haven assets live in models/*/hd-*/ with a .fbx plus a textures/ folder — import the FBX and those maps together. Kenney and other loose models are already in the pack as a self-contained .fbx (textures embedded) beside the original .glb.
- Blender can use the original .glb / .gltf files, or the .fbx files.
- PBR textures in ./textures are 4K JPG (Color, NormalGL, Roughness, and AO / Metalness where they exist): asphalt, concrete, plaster-wall, grass, wood, corrugated-metal, plus facade, rust, painted-metal and tiles. Use them as starting materials; Megascans should replace or complement them in the hero foreground.
- HDRIs in ./hdri: prefer the 4K EXR files (the_sky_is_on_fire_4k.exr for golden-hour / sunset, spruit_sunrise_4k.exr for brighter morning / park). The 2K .hdr files are a lighter fallback. Unreal and Blender both open EXR and HDR.
- Font: ./fonts/Montserrat-Light.ttf (SIL OFL) for every on-screen title.
- Prefer high-detail assets, in this order: (1) Quixel Megascans / Fab, free in UE5 — this is required, not optional; (2) the pack's models/hd-* Poly Haven scans; (3) Kenney and other low-poly meshes only as blockout, distant dressing, or a body you restyle in Blender. Kenney buildings and palms are toy-scale (often ~1–2 m); never leave them at imported size in a hero frame.

MEGASCANS / FAB (required)
Inside UE5, download and use Quixel Megascans (Fab) at 4K or 8K. You need tropical / West African palms (coconut or royal — not pines), broadleaf trees, ivy and vines, grass and weeds, lagoon-edge mud or concrete, 4K asphalt / plaster / concrete / corrugated metal, and any higher-quality vehicles or props the licence allows. Credit them in the summary. Leave them in the local project; do not add them to a redistributable zip.

SCALE NOTES (fix these before you light a shot)
- HD Poly Haven models (hd-*) are already in centimetres at real-world size. Use as-is.
- Kenney vehicles are stylized and short (~2.5–3.3 m long). Scale the hero danfo (from van.fbx) to a real Lagos midibus, about 7–8 m long, 2.5 m wide, 3 m tall.
- school-bus.fbx is wrongly scaled (~118 m tall). Either discard it or scale / reorient it to a 7.5 m midibus. Prefer the Kenney van as the danfo body.
- bicycle.fbx is wrongly scaled (~20 m long). Scale it to ~1.8 m long, ~1.1 m tall.
- motorcycle.fbx is slightly small (~1.0 m long). Scale it to a real okada, about 2.0 m long.
- butterfly.fbx is oversized (~1.5 m). Scale it to ~8–12 cm.
- Kenney city and nature kits are toy-scale. Use them only after scaling, or as distant blockout.

HERO PREP IN BLENDER
Build and export these as FBX (cm, Z-up, -Y forward, origin at the base, transforms applied):
- A yellow hover-danfo from van.fbx (preferred) or a corrected school-bus. Bright canary / chrome yellow with thick black horizontal stripes, worn paint, bumper stickers, a Lagos route board (CMS, Oshodi, Ikeja, Yaba or Third Mainland), and a 2090 hover undercarriage with a soft glow. This is not a US school bus and not a generic van.
- A glowing electric okada from motorcycle.fbx, scaled to real size. Lagos motorcycle-taxi stance, 2090 electric hub / battery, a visible night-time glow.
- Procedural vines and greenery wrapping an overpass for shot 1.
- Washing lines with cloth for the rooftop in shot 2.
- Two egrets posed and slightly restyled from bird.fbx (long neck, white, Lagos lagoon bird — not a generic cartoon bird).
Recolor freely: parasols and market umbrellas in bright Lagos colours (yellow, red, blue, patterned — not muted European cafe canvas); the shot-4 kiosk must be red. If something is still missing (water, clouds, dust, pollen, light leaks, hover glow, Nigerian shop signage), build it in Blender or UE. Do not download paid or copyrighted assets. If you add any extra free models, record author and licence in the summary.

AUTHENTIC LAGOS
This has to feel like Lagos, not a generic tropical city.
- Third Mainland Bridge: a long concrete viaduct over Lagos Lagoon, regularly spaced concrete pillars, a wide lagoon, city on both shores, golden sunset. Not a cable-stayed bridge, not Golden Gate, not a fantasy span.
- Architecture: mid-rise concrete apartments with water tanks, dishes and solar panels on the roofs; informal additions; corrugated sheets; painted facades (blue, yellow, terracotta, faded green); a mix of weathered and newer glass. Use the HD apartment facade as a starting kit.
- Signage: Nigerian shop signs, hand-painted typography, Yoruba / English mix. Examples: PURE WATER, GALA, PHONE CHARGING, OKADA PARK, route boards. Invent original 2090 solarpunk signs rather than copying real brand logos.
- Market: bright umbrellas, fruit (bananas, limes, apples, avocado and the pack fruit), crates, lanterns, dust in the light.
- Vegetation: coconut / royal palms, tropical broadleaf, bougainvillea. No pine or fir trees.
- Boats: small wooden lagoon canoes and fishing boats, not tall ships.
- Roadside: old tyres, utility boxes, electricity poles, chain-link, yellow-black kerbs where it helps.
People are optional. Prefer an atmospheric, lived-in city over a crowded street unless you can add legal, high-quality figures (e.g. MetaHumans) without breaking the frame.

UNREAL PROJECT
Create a UE5 film / cinematic project (or a blank project with the cinematic plugins). Enable Python Editor Script Plugin, Movie Render Queue, Niagara, and anything Lumen / Nanite needs. Drive as much as possible with `UnrealEditor-Cmd.exe <project> -ExecutePythonScript=...` (and the editor Python console when a command must run inside a running editor). Import FBX at scale 1.0, centimetres, with materials / textures, and enable Nanite on static meshes. Foliage that needs vertex-wind or WPO can stay off Nanite if quality is better that way. Build 8 shot levels or sublevels plus a persistent lighting level, and a Level Sequence with 8 static CineCamera cuts.

LOOK (cinematic default)
- Lumen global illumination and reflections. Nanite for dense meshes.
- Sky Atmosphere + Volumetric Clouds + Exponential Height Fog. Golden-hour sun. Use the 4K sunset EXR as the lighting HDRI / backdrop for sunset shots; the sunrise EXR for the park / brighter shots.
- CineCamera on every shot: focal length and aperture chosen for the frame, cinematic depth of field (foreground palms, background city falloff), slight barrel, film back 16:9.
- Colour: rich greens, sunset pinks and oranges, deep lagoon blues, warm golden air. A cinematic grade, not a raw viewport look. Slight bloom, anamorphic-style lens flares where the sun hits, subtle light leaks on shot 7, gentle film grain, a slight vignette. Do not crush blacks; do not overgrade into orange-and-teal cliché.
- Water: a real lagoon material with ripples, reflection and a soft sun glitter — not a flat plane.
- If LOOK_MODE is later switched to anime: keep the same cameras and layout, swap in a toon post-process, painterly textures, softer shadow bands and puffy stylized clouds.

SHOTS (8 static shots, 90 frames / 3.75 s each, hard cuts, 24 fps, 720 frames total):
1. Low angle: a yellow hover-danfo glides under a vine-covered overpass at golden hour, lens flare. Text fades in: "CREATED BY BREEZEOG".
2. Rooftop garden on a Lagos apartment block: solar panels, plants, washing lines swaying, skyline behind. "CONCEPT AND DESIGN BREEZEOG".
3. Market street: colourful umbrellas, fruit stalls, hanging lanterns, glowing signs, dust motes in the light.
4. An okada rider's glowing electric bike parked by a red kiosk, blurred palm leaves swaying in front. "3D ANIMATION BREEZEOG".
5. Third Mainland Bridge wrapped in greenery over the lagoon at sunset, small boats drifting, water rippling.
6. Roadside corner: a vending kiosk, stacked crates, a bicycle against a fence, dappled tree shadows, butterflies.
7. Inside a danfo looking out the window: the city passes, rainbow light leaks wash over the lens. "STORYLINE BREEZEOG".
8. Top-down view of a lush lagoon-side park, grass swaying, two egrets flying across, pollen drifting; fade to a "Lagos 2090 by BreezeOg" title card in the last second.

MOTION
Fixed cameras; only ambient motion. Use Niagara and/or wind on foliage, cloth, water, birds, butterflies, dust and pollen. Flickering signs and a soft hover shimmer on the danfo. No handheld shake. Thin clean Montserrat Light, smooth fades, crisp readable text.

RENDER
Movie Render Queue: 1920x1080, 24 fps, PNG sequence (8-bit or 16-bit). Anti-aliasing at production quality — at least 8 spatial samples (16 preferred) on these static cameras, temporal 1 unless a shot needs it. Lumen at high quality, virtual shadow maps, motion blur only as a subtle foliar touch. Deterministic (sequence time, not wall-clock). Encode with ffmpeg to H.264 yuv420p, high bitrate (e.g. CRF 16–18 or ~20 Mbps), ./output/lagos-2090.mp4, no audio, exactly 30 seconds / 720 frames.

QUALITY GATES
Zero project or render errors. After the first render, export one frame from the middle of each shot and inspect them. If a frame looks flat, toy-like, empty, mis-scaled, generic, or not Lagos, fix art direction, lighting, scale or assets and re-render that shot (or the whole sequence). Text must be sharp. Duration must be exactly 30 s. Do not deliver a viewport play-blast.

DELIVER
./output/lagos-2090.mp4, the Blender scripts, the Unreal Python, the .uproject, and a short summary (what you used, including Megascans and any extra free assets with author and licence, plus anything you had to rescale).
