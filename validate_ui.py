"""Bounded desktop/mobile flows and exported-model parity in a fresh browser context."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

from serving import EXAMPLES, predict

ROOT = Path(__file__).parent


def validate(url: str) -> dict:
    output = ROOT / "work/ui"
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, width, height in [("desktop", 1440, 1000), ("mobile", 390, 844)]:
            context = browser.new_context(
                viewport={"width": width, "height": height}, reduced_motion="reduce"
            )
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
            response = page.goto(url, wait_until="networkidle", timeout=60000)
            assert response.status == 200
            page.locator("#content").wait_for(state="visible")
            assert page.locator(".recommendation").count() == 3
            assert page.locator("#trend-chart .trend-svg").count() == 1
            assert page.locator("#accuracy-comparison .bar-fill").count() == 2
            page.screenshot(path=str(output / f"{name}-overview.png"))
            for finding in page.locator("[data-priority]").all():
                finding.click()
                assert page.locator("#product").input_value() != ""
                assert page.locator("#issue").input_value() != ""
                assert page.locator("#issue-table tbody tr").count() == 1
                assert page.locator("#trend-chart path").count() == 1
            page.screenshot(path=str(output / f"{name}-evidence.png"))
            page.locator("#reset").click()
            page.screenshot(path=str(output / f"{name}.png"), full_page=True)
            page.locator("#product").select_option("Mortgage")
            page.locator("#issue").select_option("Trouble during payment process")
            assert "Mortgage" in page.locator("#filter-summary").inner_text()
            assert page.locator("#issue-table tbody tr").count() > 0
            page.locator("#reset").click()
            assert page.locator("#product").input_value() == ""
            for example, text in EXAMPLES.items():
                page.locator("#example").select_option(example)
                page.locator("#predict").click()
                assert predict(text)["category"] in page.locator("#prediction").inner_text()
                browser_result = page.evaluate("(text) => infer(model,text)", text)
                assert abs(browser_result["confidence"] - predict(text)["confidence"]) < 1e-10
                assert browser_result["review"] == predict(text)["review"]
            page.locator("nav a[href='#routing']").click()
            page.screenshot(path=str(output / f"{name}-model.png"))
            page.get_by_text("See cases flagged for human review", exact=True).click()
            first_case = page.locator("#queue tbody tr").first.inner_text()
            page.locator("#queue-next").click()
            assert page.locator("#queue tbody tr").first.inner_text() != first_case
            page.locator("#queue-prev").click()
            assert page.locator("#queue tbody tr").first.inner_text() == first_case
            page.locator("#queue-filter").select_option("errors")
            assert page.locator("#queue tbody tr").count() > 0
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            assert not errors, errors
            results.append(
                {
                    "viewport": name,
                    "width": width,
                    "height": height,
                    "flows": "3 finding links/filters/reset/4 routing examples/review filter/pagination",
                    "browser_errors": errors,
                    "horizontal_page_overflow": False,
                    "inference_max_tolerance": 1e-10,
                }
            )
            context.close()
        # A missing example model must not take the analytical story offline.
        context = browser.new_context()
        page = context.new_page()
        page.route("**/model.json", lambda route: route.abort())
        page.goto(url, wait_until="networkidle")
        assert page.locator("#content").is_visible()
        assert page.locator("#predict").is_disabled()
        assert "could not load" in page.locator("#prediction").inner_text()
        context.close()
        context = browser.new_context()
        page = context.new_page()
        page.route("**/data.json", lambda route: route.abort())
        page.goto(url, wait_until="networkidle")
        assert page.locator("#retry").is_visible()
        assert not page.locator("#content").is_visible()
        context.close()
        browser.close()
    report = {
        "url": url,
        "authentication": "fresh contexts without stored credentials",
        "checks": results,
    }
    (output / "validation.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8080/")
    parser.add_argument("--self-host", action="store_true")
    args = parser.parse_args()
    process = None
    if args.self_host:
        args.url = "http://127.0.0.1:8082/"
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "serving:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8082",
                "--no-access-log",
            ],
            cwd=ROOT,
        )
        for _ in range(40):
            try:
                if requests.get(args.url + "health", timeout=1).ok:
                    break
            except requests.RequestException:
                pass
            time.sleep(0.25)
    try:
        validate(args.url)
    finally:
        if process:
            process.terminate()
            process.wait(timeout=10)
