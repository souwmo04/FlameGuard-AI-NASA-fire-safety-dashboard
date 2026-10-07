# 4-minute pitch video (motion graphics)

A "240 Seconds of Glory" pitch for NASA Space Apps local judging. NASA footage, the live site in animated
browser frames, kinetic typography, an original music bed and a Kokoro AI voiceover. Total length 3:48.

## Pipeline

| Step | Script | Output (`demo/out/pitch2/`, git-ignored) |
|---|---|---|
| 1. Voiceover | Kokoro `am_michael`, speed 1.1, from `script.json` | `voice/*.wav`, `voice/durations.json` |
| 2. Timeline | `build_timeline.py` (scene order, music sections) | `timeline.json`, `timeline.js` |
| 3. Music | `make_music.py` (original, synthesised in code, no samples) | `music.wav` |
| 4. Screen clips | `record_clips.py` (Playwright, one clip per feature + the Space Apps pages) | `clips/*.webm` |
| 5. Stock clips | NASA Image and Video Library downloads, cut and re-encoded keyframe-only (see below) | `seek/stock/*.webm` |
| 6. Render | `render.py`: `director.html` is rendered frame by frame on a virtual clock (30 fps, no dropped frames), then voice and ducked music are mixed | `flameguard-pitch-4min.mp4`, `.srt` |

`director.html` holds all motion design (transitions, 3D browser frames, kinetic text, counters, montage).
Scene timing comes from the timeline, so changing a line in `script.json` and re-running steps 1, 2, 3 and 6
re-times everything.

## NASA footage used

All clips are from the [NASA Image and Video Library](https://images.nasa.gov). NASA media is generally not
subject to copyright in the United States; it is credited on screen and here. No NASA insignia is used as a
FlameGuard logo, and no NASA endorsement is implied. None of these clips show the FLEX experiment itself; each is
captioned with what it actually shows.

| On screen | NASA ID | What it is |
|---|---|---|
| Opening flame | `jsc2021m000185_Cool_Flames_Created_Aboard_International_Space_Station` | Hot flame aboard the ISS (Cool Flames Investigation with Gases) |
| Earth from orbit | `jsc2021m000138_4K_Earth_Views_Extended_Cut_for_Earth_Day_ 2021_210422-4KMP4` | 4K Earth views from the ISS |
| Booster fire | `NHQ_2020_0902_NASA CONDUCTS SPACE LAUNCH SYSTEM ROCKET FULL-SCALE BOOSTER TEST_FIX` | SLS solid rocket booster ground test |
| Astronaut at the rack, ISS exterior | `GRC-2020-CM-0152` | ISS 20th-anniversary B-roll (Combustion Integrated Rack) |
| ISS over Earth, Dragon | `GRC-2016-CM-0129.9` | CIR/FIR feature B-roll |
| Blue flame | `SoFIE-GEL` | Solid Fuel Ignition and Extinction experiment |
| Green flame spread | `GRC-2021-CN-00008` | Saffire-V burning a PMMA sample |

The Space Apps pages shown are the public
[2026 Space Apps site](https://www.spaceappschallenge.org/2026/) and the
[Flame in Freefall challenge page](https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall-ai-powered-fire-safety-insights-from-microgravity-combustion-data/).
