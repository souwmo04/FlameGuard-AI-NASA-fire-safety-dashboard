# Demo video

A two-minute narrated walkthrough of FlameGuard AI, generated from the running site.

| File | Purpose |
|---|---|
| `narration.json` | Voiceover script, one segment per scene (edit freely) |
| `title.html`, `outro.html` | Intro and closing cards |
| `make_voiceover.py` | Speech synthesis with [Piper](https://github.com/OHF-Voice/piper1-gpl) (offline neural TTS) |
| `record_demo.py` | Drives the site with Playwright and records 1920×1080 video, timed to the narration |
| `make_video.py` | Places each voice segment at its scene's start and encodes `out/flameguard-demo.mp4` + `.srt` |

```bash
pip install playwright imageio-ffmpeg piper-tts
python -m playwright install chromium
python -m piper.download_voices en_US-lessac-high
# start the API and the website first (see the main README)
python demo/make_voiceover.py --voice en_US-lessac-high.onnx
python demo/record_demo.py --site http://localhost:3000
python demo/make_video.py
```

Outputs go to `demo/out/` (git-ignored).
