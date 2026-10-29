# Sound credits

Every sound in the film is a real recording or a composed piece made by people. Nothing is
synthesised in code: `mix.py` only cuts, places, re-pitches (by resampling), filters, pans and
mixes these files, with a little reverb.

## Music

**"Silvan Sanctuary"** by Matthias "West" Westlund, from *The Battle for Wesnoth*,
GPL-2.0-or-later. Taken from the Ubuntu package `wesnoth-1.16-music`. The film uses two
sections of the piece (4.18–21.5 s and 39.3–82.3 s), cut together on a phrase boundary.

## Sound effects and ambiences

| Source | Licence | Used for |
| --- | --- | --- |
| [Sonic Pi sample pack](https://github.com/sonic-pi-net/sonic-pi/tree/dev/etc/samples) (recordings from freesound.org) | CC0 | swooshes, the climax boom, snaps, bells, chimes, glass hum and rub, soft drum thumps, vinyl hiss |
| [Moodist](https://github.com/remvze/moodist) sound library | Pixabay Content License / CC0 | keyboard and typewriter recordings (sliced into single key clicks), crickets, clock, birds, wind, wind in trees, wind chimes, singing bowl, footsteps in snow (soft crunches), bubbles (pops), leaves |
| [SND](https://snd.dev) UI sounds by Dentsu, from the `snd-lib` npm package | free for any use, see snd.dev | cursor taps, blinks, a toggle |

Which file is used where is in `mix.py`. `fetch-sounds.sh` downloads every source.
