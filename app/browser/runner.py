import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.sync_api import sync_playwright


class BrowserTestRunner:
    def __init__(
        self,
        artifacts_directory: str = "artifacts",
        headless: bool = False,
    ) -> None:
        self.artifacts_directory = Path(artifacts_directory)
        self.artifacts_directory.mkdir(parents=True, exist_ok=True)
        self.headless = headless

    def run_smoke_test(self, url: str) -> dict[str, Any]:
        timestamp = datetime.now(timezone.utc).strftime(
            "%Y%m%d_%H%M%S"
        )

        screenshot_path = (
            self.artifacts_directory
            / f"screenshot_{timestamp}.png"
        )

        result: dict[str, Any] = {
            "test_name": "Website smoke test",
            "url": url,
            "status": "failed",
            "page_title": None,
            "screenshot": None,
            "error": None,
        }

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=self.headless
                )

                page = browser.new_page()

                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )

                result["page_title"] = page.title()

                page.screenshot(
                    path=str(screenshot_path),
                    full_page=True,
                )

                result["screenshot"] = str(screenshot_path)

                if response is None:
                    raise RuntimeError(
                        "The website returned no HTTP response."
                    )

                if response.status >= 400:
                    raise RuntimeError(
                        f"Website returned HTTP {response.status}."
                    )

                result["status"] = "passed"

                browser.close()

        except PlaywrightTimeoutError:
            result["error"] = "The website took too long to load."

        except Exception as error:
            result["error"] = str(error)

        self._save_report(result, timestamp)

        return result

    def _save_report(
        self,
        result: dict[str, Any],
        timestamp: str,
    ) -> None:
        report_path = (
            self.artifacts_directory
            / f"report_{timestamp}.json"
        )

        report_path.write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )