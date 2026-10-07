"""Record the FlameGuard demo video: drives the running site scene by scene, timed to the narration.

Prerequisites: API and website running (website at --site), voice files from make_voiceover.py.
Writes demo/out/raw.webm and demo/out/timings.json (actual start of every scene, for the audio mix).

    python demo/record_demo.py --site http://localhost:3000
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
import wave
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
GAP = 0.8  # seconds of breathing room after each narration segment
W, H = 1920, 1080

# A visible cursor (Playwright videos do not show the real one) and no Next.js dev badge.
INIT_JS = """
(() => {
  const style = document.createElement('style');
  style.textContent = 'nextjs-portal{display:none!important}' +
    '#__demo_cursor{position:fixed;left:-50px;top:-50px;width:26px;height:26px;border-radius:50%;' +
    'background:rgba(251,191,36,.28);border:2px solid #fbbf24;box-shadow:0 0 18px rgba(251,191,36,.6);' +
    'pointer-events:none;z-index:2147483647;transform:translate(-50%,-50%);transition:transform .12s}';
  const add = () => {
    document.head.appendChild(style);
    const c = document.createElement('div'); c.id = '__demo_cursor'; document.body.appendChild(c);
    const last = sessionStorage.getItem('__demo_cursor');
    if (last) { const [x, y] = JSON.parse(last); c.style.left = x + 'px'; c.style.top = y + 'px'; }
    addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px';
      sessionStorage.setItem('__demo_cursor', JSON.stringify([e.clientX, e.clientY])); }, true);
    addEventListener('mousedown', () => c.style.transform = 'translate(-50%,-50%) scale(.65)', true);
    addEventListener('mouseup', () => c.style.transform = 'translate(-50%,-50%)', true);
  };
  if (document.readyState === 'loading') addEventListener('DOMContentLoaded', add); else add();
})();
"""


def smooth_scroll(page: Page, y: float, ms: int = 1800) -> None:
    page.evaluate("""([y, ms]) => new Promise(done => {
      const el = document.scrollingElement, from = el.scrollTop, to = Math.max(0, y), t0 = performance.now();
      const step = now => { const k = Math.min(1, (now - t0) / ms), e = k < .5 ? 2*k*k : 1 - Math.pow(-2*k + 2, 2) / 2;
        el.scrollTop = from + (to - from) * e; k < 1 ? requestAnimationFrame(step) : done(); };
      requestAnimationFrame(step); })""", [y, ms])


def scroll_to(page: Page, selector: str, ms: int = 1800, offset: int = 96) -> None:
    y = page.evaluate("([s, o]) => { const el = document.querySelector(s); return el ? el.getBoundingClientRect().top + scrollY - o : scrollY; }",
                      [selector, offset])
    smooth_scroll(page, y, ms)


def glide_click(page: Page, locator, pause: int = 250) -> None:
    locator.scroll_into_view_if_needed()
    box = locator.bounding_box()
    if box is None:
        return
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=28)
    page.wait_for_timeout(pause)
    page.mouse.down()
    page.wait_for_timeout(90)
    page.mouse.up()


def goto(page: Page, url: str, ready: str | None = None) -> None:
    page.goto(url, wait_until="domcontentloaded")
    if ready:
        page.wait_for_selector(ready, timeout=30000)


# --- scenes -------------------------------------------------------------------------------------

def scenes(site: str) -> dict:
    def intro(p: Page):
        goto(p, (HERE / "title.html").as_uri())

    def landing(p: Page):
        goto(p, f"{site}/", "h1")
        p.wait_for_timeout(2200)
        smooth_scroll(p, 760, 3200)

    def mission(p: Page):
        goto(p, f"{site}/dashboard", "section[aria-label]")
        p.wait_for_timeout(1500)
        smooth_scroll(p, 650, 3500)

    def risk(p: Page):
        goto(p, f"{site}/risk", "button[type=submit]")
        p.wait_for_timeout(1200)
        glide_click(p, p.get_by_role("radio", name="n-Heptane"))
        p.wait_for_timeout(600)
        glide_click(p, p.get_by_role("button", name="Analyze fire risk"))
        p.wait_for_timeout(3200)
        scroll_to(p, '[aria-label="Why this prediction?"]', 2200)

    def whatif(p: Page):
        goto(p, f"{site}/what-if", 'text="Scenario comparison"')
        p.wait_for_timeout(1000)
        glide_click(p, p.get_by_role("button", name="Add 15% CO₂"))
        p.wait_for_timeout(1500)
        scroll_to(p, '[aria-label^="Fire Risk as"]', 2000)

    def experiments(p: Page):
        goto(p, f"{site}/experiments", "tbody tr")
        p.wait_for_timeout(1300)
        glide_click(p, p.locator("tbody tr").nth(2).locator("button"))
        p.wait_for_timeout(3400)
        p.keyboard.press("Escape")

    def ranking(p: Page):
        goto(p, f"{site}/ranking", "[role=tabpanel] ol li")
        p.wait_for_timeout(900)
        glide_click(p, p.locator("[role=tabpanel] ol li button").first)
        p.wait_for_timeout(800)
        smooth_scroll(p, 380, 1800)

    def suppressant(p: Page):
        goto(p, f"{site}/suppressants", 'text="The NASA data cannot rank these suppressants."')
        p.wait_for_timeout(2400)
        scroll_to(p, '[aria-label^="Oxygen needed"]', 2600)

    def similar(p: Page):
        goto(p, f"{site}/similar", '[aria-label="Distance map"]')
        p.wait_for_timeout(700)
        scroll_to(p, '[aria-label="Evidence check"]', 1600)

    def ask(p: Page):
        goto(p, f"{site}/knowledge", "text=What happened in test FLEX-094?")
        p.wait_for_timeout(600)
        glide_click(p, p.get_by_role("button", name="What happened in test FLEX-094?"))
        p.wait_for_selector('[aria-label="Sources"] li', timeout=30000)
        p.wait_for_timeout(1200)
        scroll_to(p, '[aria-label="Sources"]', 1800, offset=260)

    def science(p: Page):
        goto(p, f"{site}/science", "#gravity")
        p.wait_for_timeout(900)
        scroll_to(p, "#gravity", 1400)
        glide_click(p, p.get_by_role("radio", name="Earth (1 g)"))
        p.wait_for_timeout(1900)
        glide_click(p, p.get_by_role("radio", name="ISS (microgravity)"))

    def methodology(p: Page):
        goto(p, f"{site}/methodology", '[aria-label="Calibration"]')
        p.wait_for_timeout(900)
        scroll_to(p, '[aria-label="Performance on unseen tests"]', 2400)

    def outro(p: Page):
        goto(p, (HERE / "outro.html").as_uri())

    return dict(intro=intro, landing=landing, mission=mission, risk=risk, whatif=whatif, experiments=experiments,
                ranking=ranking, suppressant=suppressant, similar=similar, ask=ask, science=science,
                methodology=methodology, outro=outro)


def warm_up(browser, site: str) -> None:
    """Visit every route once off camera so the dev server has compiled them before recording."""
    ctx = browser.new_context(viewport={"width": W, "height": H})
    page = ctx.new_page()
    for path in ["/", "/dashboard", "/risk", "/what-if", "/experiments", "/ranking", "/suppressants", "/similar",
                 "/knowledge", "/science", "/methodology"]:
        page.goto(f"{site}{path}", wait_until="networkidle", timeout=120000)
    ctx.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="http://localhost:3000")
    args = ap.parse_args()

    segs = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))
    durations = {}
    for s in segs:
        with wave.open(str(OUT / "voice" / f"{s['id']}.wav"), "rb") as wf:
            durations[s["id"]] = wf.getnframes() / wf.getframerate()
    actions = scenes(args.site.rstrip("/"))

    video_dir = OUT / "video"
    shutil.rmtree(video_dir, ignore_errors=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        warm_up(browser, args.site.rstrip("/"))
        ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1,
                                  record_video_dir=str(video_dir), record_video_size={"width": W, "height": H})
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()
        t0 = time.monotonic()
        timings = []
        for s in segs:
            start = time.monotonic() - t0
            actions[s["id"]](page)
            slot = durations[s["id"]] + GAP
            left = slot - (time.monotonic() - t0 - start)
            if left > 0:
                page.wait_for_timeout(int(left * 1000))
            timings.append({"id": s["id"], "start": round(start, 3), "voice": round(durations[s["id"]], 3),
                            "text": s["text"], "overran_by": round(max(0.0, -left), 3)})
            print(f"{s['id']:<12} start {start:6.1f}s  {'(overran %.1fs)' % -left if left < 0 else ''}")
        total = time.monotonic() - t0
        video = page.video.path()
        ctx.close()
        browser.close()
    shutil.move(video, OUT / "raw.webm")
    (OUT / "timings.json").write_text(json.dumps({"total": round(total, 3), "segments": timings}, indent=2), encoding="utf-8")
    print(f"recorded {total:.1f}s -> {OUT / 'raw.webm'}")


if __name__ == "__main__":
    main()
