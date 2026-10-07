"""Record the short screen clips used inside the motion-graphics pitch (one WebM per clip, 1920x1080).

    python demo/pitch2/record_clips.py --site http://localhost:3000

Outputs demo/out/pitch2/clips/<name>.webm. Each clip is recorded in its own browser context so it can be
placed, zoomed and transitioned independently by the director page.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from record_demo import INIT_JS, W, H, glide_click, goto, scroll_to, smooth_scroll, warm_up  # noqa: E402

OUT = HERE.parent / "out" / "pitch2" / "clips"
CHALLENGE = ("https://www.spaceappschallenge.org/2026/challenges/"
             "flame-in-freefall-ai-powered-fire-safety-insights-from-microgravity-combustion-data/")


def dismiss_banners(p: Page) -> None:
    """Close cookie/consent banners choosing the privacy-preserving option when one is offered."""
    for name in ["Reject all", "Reject", "Decline", "Only necessary", "Necessary only", "Close"]:
        btn = p.get_by_role("button", name=name)
        if btn.count() and btn.first.is_visible():
            btn.first.click()
            p.wait_for_timeout(400)
            return


def clips(site: str) -> dict:
    def spaceapps(p: Page):
        p.goto("https://www.spaceappschallenge.org/2026/", wait_until="domcontentloaded", timeout=60000)
        p.wait_for_timeout(2500)
        dismiss_banners(p)
        p.wait_for_timeout(2500)
        smooth_scroll(p, 500, 2500)
        p.goto(CHALLENGE, wait_until="domcontentloaded", timeout=60000)
        p.wait_for_timeout(2500)
        dismiss_banners(p)
        p.wait_for_timeout(2000)
        smooth_scroll(p, 650, 4000)
        p.wait_for_timeout(2000)

    def landing(p: Page):
        goto(p, f"{site}/", "h1")
        p.wait_for_timeout(2500)
        smooth_scroll(p, 760, 3500)
        p.wait_for_timeout(1500)

    def risk(p: Page):
        goto(p, f"{site}/risk", "button[type=submit]")
        p.wait_for_timeout(900)
        glide_click(p, p.get_by_role("radio", name="n-Heptane"))
        p.wait_for_timeout(500)
        slider = p.get_by_role("slider", name="Oxygen")
        box = slider.bounding_box()
        p.mouse.move(box["x"] + box["width"] * 0.42, box["y"] + box["height"] / 2, steps=20)
        slider.focus()
        for _ in range(6):
            p.keyboard.press("ArrowRight")
            p.wait_for_timeout(140)
        glide_click(p, p.get_by_role("button", name="Analyze fire risk"))
        p.wait_for_timeout(4200)

    def explain(p: Page):
        goto(p, f"{site}/risk?fuel=Heptane&o2=24&supp=none&supp_pct=0&d0=3", "button[type=submit]")
        p.wait_for_selector('[aria-label="Why this prediction?"]', timeout=30000)
        p.wait_for_timeout(800)
        scroll_to(p, '[aria-label="Why this prediction?"]', 2200)
        p.wait_for_timeout(5000)

    def evidence(p: Page):
        goto(p, f"{site}/methodology", '[aria-label="Calibration"]')
        p.wait_for_timeout(500)
        scroll_to(p, '[aria-label="Performance on unseen tests"]', 1800)
        p.wait_for_timeout(3000)
        scroll_to(p, '[aria-label="Risk bands and their track record"]', 1800)
        p.wait_for_timeout(2500)

    def whatif(p: Page):
        goto(p, f"{site}/what-if", 'text="Scenario comparison"')
        p.wait_for_timeout(600)
        glide_click(p, p.get_by_role("button", name="Add 15% CO₂"))
        p.wait_for_timeout(1800)
        scroll_to(p, '[aria-label^="Fire Risk as"]', 2000)
        p.wait_for_timeout(2500)

    def experiments(p: Page):
        goto(p, f"{site}/experiments", "tbody tr")
        p.wait_for_timeout(700)
        glide_click(p, p.locator("tbody tr").nth(6).locator("button"))
        p.wait_for_timeout(4500)

    def suppressant(p: Page):
        goto(p, f"{site}/suppressants", 'text="The NASA data cannot rank these suppressants."')
        p.wait_for_timeout(2200)
        scroll_to(p, '[aria-label^="Oxygen needed"]', 2400)
        p.wait_for_timeout(2500)

    def similar(p: Page):
        goto(p, f"{site}/similar", '[aria-label="Distance map"]')
        p.wait_for_timeout(500)
        scroll_to(p, '[aria-label="Evidence check"]', 1500)
        p.wait_for_timeout(4000)

    def ask(p: Page):
        goto(p, f"{site}/knowledge", "text=What happened in test FLEX-094?")
        p.wait_for_timeout(400)
        glide_click(p, p.get_by_role("button", name="What happened in test FLEX-094?"))
        p.wait_for_selector('[aria-label="Sources"] li', timeout=30000)
        p.wait_for_timeout(500)
        scroll_to(p, '[aria-label="Sources"]', 1400, offset=300)
        p.wait_for_timeout(3000)

    def science(p: Page):
        goto(p, f"{site}/science", "#gravity")
        p.wait_for_timeout(500)
        scroll_to(p, "#gravity", 1200)
        glide_click(p, p.get_by_role("radio", name="Earth (1 g)"))
        p.wait_for_timeout(1800)
        glide_click(p, p.get_by_role("radio", name="ISS (microgravity)"))
        p.wait_for_timeout(2500)

    def honest(p: Page):
        goto(p, f"{site}/risk?fuel=Methanol&o2=21&supp=none&supp_pct=0&d0=3", "button[type=submit]")
        p.wait_for_selector("text=Contamination check", timeout=30000)
        p.wait_for_timeout(600)
        p.evaluate("""() => { const el = [...document.querySelectorAll('span')].find(s => s.textContent === 'Contamination check');
          el?.closest('div.space-y-2')?.scrollIntoView({behavior: 'smooth', block: 'center'}); }""")
        p.wait_for_timeout(5500)

    return dict(spaceapps=spaceapps, landing=landing, risk=risk, explain=explain, evidence=evidence, whatif=whatif,
                experiments=experiments, suppressant=suppressant, similar=similar, ask=ask, science=science,
                honest=honest)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="http://localhost:3000")
    ap.add_argument("--only", nargs="*")
    args = ap.parse_args()
    site = args.site.rstrip("/")
    OUT.mkdir(parents=True, exist_ok=True)
    plan = clips(site)
    names = args.only or list(plan)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        warm_up(browser, site)
        for name in names:
            tmp = OUT / f"_{name}"
            shutil.rmtree(tmp, ignore_errors=True)
            ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1, locale="en-US",
                                      record_video_dir=str(tmp), record_video_size={"width": W, "height": H})
            ctx.add_init_script(INIT_JS)
            page = ctx.new_page()
            try:
                plan[name](page)
            finally:
                video = page.video.path()
                ctx.close()
            shutil.move(video, OUT / f"{name}.webm")
            shutil.rmtree(tmp, ignore_errors=True)
            print(f"{name} ok")
        browser.close()


if __name__ == "__main__":
    main()
