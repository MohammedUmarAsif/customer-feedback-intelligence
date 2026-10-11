"""Capture safe public dashboard screenshots for the README."""

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, width, height in [("desktop", 1440, 1000), ("mobile", 390, 844)]:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto("http://127.0.0.1:8080/", wait_until="networkidle")
        page.locator("#content").wait_for(state="visible")
        page.screenshot(path=str(ROOT / f"docs/dashboard-{name}.png"))
    browser.close()
