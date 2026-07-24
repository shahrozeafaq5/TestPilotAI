from pathlib import Path

from playwright.sync_api import sync_playwright

from app.browser.page_inspector import PageInspector


PROJECT_ROOT = Path(__file__).resolve().parents[1]

html_file = (
    PROJECT_ROOT
    / "samples"
    / "locator_demo.html"
)


def test_page_inspector():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        page = browser.new_page()
        page.goto(html_file.as_uri())

        inspector = PageInspector()
        inspection = inspector.inspect(page)

        print(inspection.model_dump_json(indent=2))

        assert inspection.title == "Locator Practice"
        assert len(inspection.elements) > 0

        browser.close()