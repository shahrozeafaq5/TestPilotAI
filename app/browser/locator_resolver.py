from playwright.sync_api import Locator, Page


def resolve_locator(
    page: Page,
    locator_type: str,
    locator_value: str,
    locator_name: str | None = None,
) -> Locator:
    if locator_type == "role":
        if locator_name:
            return page.get_by_role(
                locator_value,
                name=locator_name,
            )

        return page.get_by_role(locator_value)

    if locator_type == "label":
        return page.get_by_label(locator_value)

    if locator_type == "placeholder":
        return page.get_by_placeholder(locator_value)

    if locator_type == "text":
        return page.get_by_text(locator_value)

    if locator_type == "css":
        return page.locator(locator_value)

    raise ValueError(
        f"Unsupported locator type: {locator_type}"
    )