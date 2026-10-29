#!/bin/bash
# Downloads every sound source used by mix.py into $SOUND_SRC (default /opt/dl) and cuts the
# single hits into $SOUND_CACHE (default /opt/film/audio/cache).
set -euo pipefail
SRC="${SOUND_SRC:-/opt/dl}"
CACHE="${SOUND_CACHE:-/opt/film/audio/cache}"
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
mkdir -p "$SRC" "$CACHE"
cd "$SRC"

# music: The Battle for Wesnoth soundtrack (Ubuntu archive)
mkdir -p debs && (cd debs && apt-get download wesnoth-1.16-music && mkdir -p x/wesnoth-1.16-music && dpkg-deb -x wesnoth-1.16-music_*.deb x/wesnoth-1.16-music)

# Moodist sound library
[ -d moodist ] || git clone --depth 1 --filter=blob:none --sparse https://github.com/remvze/moodist
(cd moodist && git sparse-checkout set public/sounds)

# Sonic Pi CC0 samples
[ -d sonicpi ] || git clone --depth 1 --filter=blob:none --sparse https://github.com/sonic-pi-net/sonic-pi sonicpi
(cd sonicpi && git sparse-checkout set etc/samples)

# SND UI sounds
mkdir -p npm && (cd npm && npm pack snd-lib@1.2.4 >/dev/null && tar xzf snd-lib-1.2.4.tgz)

# slice single hits from the longer recordings and unpack the SND sprites
M=moodist/public/sounds
"$PY" "$HERE/slice.py" $M/things/keyboard.mp3 "$CACHE/keys" key 0.22
"$PY" "$HERE/slice.py" $M/things/typewriter.mp3 "$CACHE/tw" tw 0.3
"$PY" "$HERE/slice.py" $M/nature/walk-in-snow.mp3 "$CACHE/snow" snow 0.45
"$PY" "$HERE/slice.py" $M/things/bubbles.mp3 "$CACHE/bub" bub 0.3
"$PY" "$HERE/prepare.py" "$SRC" "$CACHE"
