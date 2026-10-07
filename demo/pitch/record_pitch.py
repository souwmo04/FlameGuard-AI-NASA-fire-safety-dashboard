"""Record the 4-minute "240 Seconds of Glory" pitch: cards + live site scenes, timed to pitch.json narration.

Prerequisites: API and website running; voice files from demo/pitch/make_voiceover.py.
Writes demo/out/pitch/raw.webm and demo/out/pitch/timings.json.

    python demo/pitch/record_pitch.py --site http://localhost:3000
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import wave
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from record_demo import INIT_JS, W, H, glide_click, goto, scroll_to, smooth_scroll, warm_up  # noqa: E402

OUT = HERE.parent / "out" / "pitch"
GAP = 0.9
SECTIONS = {1: "Who", 2: "Why", 3: "What", 4: "How"}
SUBTITLE = {1: "attention & authenticity", 2: "the problem", 3: "the big idea", 4: "impact & needs"}


def badge(page: Page, section: int) -> None:
    """Chapter chip on live-site scenes, matching the cards (01 WHO … 04 HOW)."""
    page.evaluate("""([n, name, sub]) => {
      document.getElementById('__pitch_badge')?.remove();
      const b = document.createElement('div'); b.id = '__pitch_badge';
      b.innerHTML = `<b>0${n}</b>${name}<span>${sub}</span>`;
      Object.assign(b.style, {position:'fixed', right:'28px', bottom:'28px', zIndex: 2147483646, display:'flex',
        alignItems:'center', gap:'12px', padding:'10px 18px 10px 10px', borderRadius:'16px', fontFamily:'Segoe UI, sans-serif',
        fontSize:'20px', letterSpacing:'.14em', textTransform:'uppercase', color:'#f1f5f9',
        background:'rgba(8,12,24,.88)', border:'1px solid rgba(255,255,255,.14)', boxShadow:'0 10px 40px rgba(0,0,0,.5)'});
      const k = b.querySelector('b'); Object.assign(k.style, {fontFamily:'Consolas, monospace', letterSpacing:'0', color:'#05070d',
        background:'linear-gradient(90deg,#fbbf24,#fb923c)', padding:'3px 10px', borderRadius:'9px'});
      const s = b.querySelector('span'); Object.assign(s.style, {color:'#a3b1c6', letterSpacing:'.08em', textTransform:'none'});
      document.body.appendChild(b);
    }""", [section, SECTIONS[section], SUBTITLE[section]])


def card(page: Page, name: str) -> None:
    goto(page, (HERE / "cards.html").as_uri() + f"?s={name}")


def scenes(site: str) -> dict:
    def special(p: Page):
        goto(p, f"{site}/", "h1")
        badge(p, 1)
        p.wait_for_timeout(5500)
        smooth_scroll(p, 760, 4200)
        p.wait_for_timeout(1500)
        smooth_scroll(p, 1500, 4200)

    def what_idea(p: Page):
        goto(p, f"{site}/risk", "button[type=submit]")
        badge(p, 3)
        p.wait_for_timeout(1500)
        glide_click(p, p.get_by_role("radio", name="n-Heptane"))
        p.wait_for_timeout(900)
        slider = p.get_by_role("slider", name="Oxygen")
        box = slider.bounding_box()
        p.mouse.move(box["x"] + box["width"] * 0.42, box["y"] + box["height"] / 2, steps=24)  # point at the thumb
        slider.focus()  # keyboard steps of 0.5 points: 21% -> 24%, no click-jump
        for _ in range(6):
            p.keyboard.press("ArrowRight")
            p.wait_for_timeout(180)
        p.wait_for_timeout(700)
        glide_click(p, p.get_by_role("button", name="Analyze fire risk"))
        p.wait_for_timeout(3000)

    def what_explain(p: Page):
        scroll_to(p, '[aria-label="Why this prediction?"]', 2600)
        p.wait_for_timeout(3500)
        scroll_to(p, '[aria-label="Most similar NASA tests"]', 2400)

    def what_evidence(p: Page):
        goto(p, f"{site}/methodology", '[aria-label="Calibration"]')
        badge(p, 3)
        p.wait_for_timeout(600)
        scroll_to(p, '[aria-label="Performance on unseen tests"]', 2200)
        p.wait_for_timeout(4200)
        scroll_to(p, '[aria-label="Risk bands and their track record"]', 2200)

    def what_tools(p: Page):
        goto(p, f"{site}/what-if", 'text="Scenario comparison"')
        badge(p, 3)
        p.wait_for_timeout(700)
        glide_click(p, p.get_by_role("button", name="Lower O₂ by 4 points"))
        p.wait_for_timeout(2600)
        goto(p, f"{site}/experiments", "tbody tr")
        badge(p, 3)
        p.wait_for_timeout(500)
        glide_click(p, p.locator("tbody tr").nth(6).locator("button"))  # test 007: kept burning, correctly flagged
        p.wait_for_timeout(2600)
        p.keyboard.press("Escape")
        goto(p, f"{site}/suppressants", 'text="The NASA data cannot rank these suppressants."')
        badge(p, 3)

    def what_ask(p: Page):
        goto(p, f"{site}/knowledge", "text=What happened in test FLEX-094?")
        badge(p, 3)
        p.wait_for_timeout(300)
        glide_click(p, p.get_by_role("button", name="What happened in test FLEX-094?"))
        p.wait_for_selector('[aria-label="Sources"] li', timeout=30000)
        p.wait_for_timeout(600)
        scroll_to(p, '[aria-label="Sources"]', 1400, offset=300)

    def what_honest(p: Page):
        goto(p, f"{site}/risk?fuel=Methanol&o2=21&supp=none&supp_pct=0&d0=3", "button[type=submit]")
        badge(p, 3)
        p.wait_for_selector("text=Contamination check", timeout=30000)
        p.wait_for_timeout(1200)
        p.evaluate("""() => { const el = [...document.querySelectorAll('span')].find(s => s.textContent === 'Contamination check');
          el?.closest('div.space-y-2')?.scrollIntoView({behavior: 'smooth', block: 'center'}); }""")

    plan = {name: (lambda p, n=name: card(p, n)) for name in
            ["hook", "who", "why_question", "why_atmos", "why_data", "why_problem", "how_impact", "how_needs",
             "how_vision", "outro"]}
    plan.update(special=special, what_idea=what_idea, what_explain=what_explain, what_evidence=what_evidence,
                what_tools=what_tools, what_ask=what_ask, what_honest=what_honest)
    return plan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="http://localhost:3000")
    args = ap.parse_args()
    site = args.site.rstrip("/")

    segs = json.loads((HERE / "pitch.json").read_text(encoding="utf-8"))
    durations = {}
    for s in segs:
        with wave.open(str(OUT / "voice" / f"{s['id']}.wav"), "rb") as wf:
            durations[s["id"]] = wf.getnframes() / wf.getframerate()
    actions = scenes(site)

    video_dir = OUT / "video"
    shutil.rmtree(video_dir, ignore_errors=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        warm_up(browser, site)
        ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1,
                                  record_video_dir=str(video_dir), record_video_size={"width": W, "height": H})
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()
        t0 = time.monotonic()
        timings = []
        for i, s in enumerate(segs):
            start = time.monotonic() - t0
            actions[s["id"]](page)
            hold = 2.0 if s["id"] == "outro" else GAP
            left = durations[s["id"]] + hold - (time.monotonic() - t0 - start)
            if left > 0:
                page.wait_for_timeout(int(left * 1000))
            timings.append({"id": s["id"], "start": round(start, 3), "voice": round(durations[s["id"]], 3),
                            "text": s["text"], "overran_by": round(max(0.0, -left), 3)})
            print(f"{s['id']:<14} start {start:6.1f}s {'(overran %.1fs)' % -left if left < 0 else ''}")
        total = time.monotonic() - t0
        video = page.video.path()
        ctx.close()
        browser.close()
    shutil.move(video, OUT / "raw.webm")
    (OUT / "timings.json").write_text(json.dumps({"total": round(total, 3), "segments": timings}, indent=2), encoding="utf-8")
    print(f"recorded {total:.1f}s -> {OUT / 'raw.webm'}")


if __name__ == "__main__":
    main()
