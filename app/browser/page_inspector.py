from playwright.sync_api import Page

from app.models.page_inspection import (
    PageElement,
    PageInspection,
)


class PageInspector:
    def inspect(self, page: Page) -> PageInspection:
        raw_elements = page.locator(
            "input, textarea, select, button, a, "
            "h1, h2, h3, p"
        ).evaluate_all(
            """
            elements => elements.map(element => {
                const id = element.id;

                const label = id
                    ? document.querySelector(
                        `label[for="${id}"]`
                    )?.innerText.trim()
                    : null;

                const text = (
                    element.innerText ||
                    element.textContent ||
                    ""
                ).trim();

                const style = window.getComputedStyle(element);

                const visible = Boolean(
                    element.offsetWidth ||
                    element.offsetHeight ||
                    element.getClientRects().length
                ) &&
                style.visibility !== "hidden" &&
                style.display !== "none";

                return {
                    tag: element.tagName.toLowerCase(),
                    element_type:
                        element.getAttribute("type"),
                    role:
                        element.getAttribute("role"),
                    name:
                        element.getAttribute("aria-label") ||
                        element.getAttribute("name"),
                    label: label,
                    placeholder:
                        element.getAttribute("placeholder"),
                    text: text || null,
                    visible: visible
                };
            })
            """
        )

        elements = [
            PageElement.model_validate(element)
            for element in raw_elements
        ]

        return PageInspection(
            title=page.title(),
            url=page.url,
            elements=elements,
        )