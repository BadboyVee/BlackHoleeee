# BlackHoleeee: notes for Claude

A sandbox of single-file browser projects (Three.js, canvas) plus video work for veee (GitHub
`badboyvee`). GitHub Pages serves the whole repo; Netlify publishes only `bmw-m5-cs/`.

## Video work: read first

When the user asks for a video, an edit, a launch film or anything with motion and music, read
**[`video-craft/PLAYBOOK.md`](video-craft/PLAYBOOK.md)** before planning. It holds their standards,
the 16-bar template, timing, type and colour rules, the rendering/encoding pipeline that works here,
the QA checklist and the mistakes already made.

- Reference studies (frame-by-frame, measured): [`video-craft/references/`](video-craft/references/)
  - [Tender launch film](video-craft/references/tender-launch-film.md): the user's style target
    (white + ink + one gold accent, serif/mono type, 124.6 BPM, one idea per bar).
- When they send a new reference video to study, run
  [`video-craft/tools/study_video.sh`](video-craft/tools/README.md), look at every contact sheet,
  then add a new file in `video-craft/references/` and fold new rules into the playbook.

## The essentials

- **COPY ALL:** when they give a reference, reproduce all of it: every timing, size, colour, frame rate
  and loudness. No "improvements".
- They want it **beautiful, no mistakes, fast**. Send short progress lines; deliver MP4 via SendUserFile
  (≤ 30 MiB), 1080p at the reference's frame rate. Offer **"made by veee"** as the closing signature (their AI edit used it).
- Lock everything to the music: one idea per bar, cuts on downbeats 0–1 frame early, words on beats.
- Each shot: decelerate after the cut → drift → accelerate into the next cut.
- Extend music only by whole loop phrases joined on downbeats; check the chord flow and listen for clicks.
- Before sending:
  - crop all text at 100%;
  - scan for one-frame flashes;
  - SSIM ≥ 0.998 against the rendered frames;
  - check spelling of every name.
