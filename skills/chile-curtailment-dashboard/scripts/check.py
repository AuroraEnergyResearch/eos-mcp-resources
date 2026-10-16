#!/usr/bin/env python3
"""Optional visual check: render the dashboard headless, report JS errors, save screenshots.

Usage: python check.py <dashboard.html> <screenshot_prefix>
Needs playwright with chromium. If unavailable, skip this step.
"""
import asyncio, pathlib, sys
from playwright.async_api import async_playwright

async def main(html, prefix):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1280, "height": 1100})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        await pg.goto(pathlib.Path(html).resolve().as_uri())
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f"{prefix}_first.png", full_page=True)
        ticks = await pg.query_selector_all(".tick")
        await ticks[-1].click()
        await pg.wait_for_timeout(2500)
        await pg.screenshot(path=f"{prefix}_last.png", full_page=True)
        await b.close()
        print("JS errors:", errs or "none")
        print(f"Saved {prefix}_first.png and {prefix}_last.png")

asyncio.run(main(sys.argv[1], sys.argv[2]))
