import sys, traceback
import re
from typing import List, Optional
from time import sleep
from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
    Locator,
)
from src.robot.actions import fb_utils
from src.my_types import RobotTaskType, BrowserWorkerSignals, RobotSettingsType

MIN = 60_000

SELECTORS = {
    "root": 'div[data-type="vscroller"]',
    "container": 'div[data-type="container"]',
    "product": '> div[data-mcomponent="ServerTextArea"]:nth-of-type(3)',
    "tabindex": 'div[tabindex="0"][data-type="container"]',
    "product_menu_button": 'div[role="button"][data-focusable="true"]',
    "bottom_sheet": 'div[role="presentation"]',
    "fixed_top": "div.fixed-container.top",
    "button": "div[role='button']",
    "group": "div.m",
    "focusable": "div[data-focusable='true']",
    "data_action_id": "div[data-action-id]",
    "fixed_bottom": "div.fixed-container.bottom",
    "loading": "div.loading-overlay",
}


def share_latest_product(
    page: Page,
    task: RobotTaskType,
    settings: RobotSettingsType,
    signals: BrowserWorkerSignals,
):
    try:
        goto_list_more_place_page(
            page=page, task=task, settings=settings, signals=signals
        )
        group_selectors = get_group_selectors(
            page=page,
            task=task,
            signals=signals,
        )
        if len(group_selectors) <15:
            return True
        while group_selectors:
            current_selector = group_selectors[:10]
            goto_list_more_place_page(
                page=page, task=task, settings=settings, signals=signals
            )
            list_more_place(
                group_selectors=current_selector, page=page, task=task, signals=signals
            )
            group_selectors = group_selectors[10:]
        # sleep(30)
        return True
    except Exception as e:
        if "ERR_PROXY_NOT_READY" == str(e) or "ERR_TIMED_OUT" in str(e):
            raise e
        error_type = type(e).__name__
        error_message = str(e)
        full_traceback = traceback.format_exc()
        

        # print(
        #     f"UNEXPECTED ERROR: A general error occurred during task execution:",
        #     file=sys.stderr,
        # )
        # print(f"  Error Type: {error_type}", file=sys.stderr)
        # print(f"  Message: {error_message}", file=sys.stderr)
        # print(f"  Traceback Details:\n{full_traceback}", file=sys.stderr)

        msg = f"\t\t❌ ERROR [{task.user_info.username} - {task.user_info.username}]({task.action_name}): {error_type}"
        print(msg)

        # signals.error_signal.emit(
        #     task,
        #     f"Unexpected error: {error_message}\nDetails: See console log for full traceback.",
        # )
        return False


def goto_list_more_place_page(
    page: Page,
    task: RobotTaskType,
    settings: RobotSettingsType,
    signals: BrowserWorkerSignals,
):
    progress: List[int] = [0, 0]
    signals.info_signal.emit(task, "goto_list_more_place_page")

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])

    # Adjusted total steps based on detailed logging
    progress[1] = 10
    emit_progress_update(f"Step 0: Estimated total steps: {progress[1]}")

    listing_id_url = "https://m.facebook.com/marketplace/selling/?listing_id"

    # Step 1: Navigate to the listing ID page
    emit_progress_update(
        f"Step 1: Attempting to navigate to listing ID page: {listing_id_url}"
    )
    try:
        page.goto(listing_id_url, wait_until="domcontentloaded", timeout=MIN)
        is_049 = fb_utils.redirect_out_049(page)
        if is_049 == 2:
            page.goto(listing_id_url, wait_until="domcontentloaded", timeout=MIN)
        elif is_049 == 0:
            return False
        sleep(3)
        wait_loading(page)
        emit_progress_update("Step 1: Successfully navigated to listing ID page.")
    except PlaywrightTimeoutError as e:
        _msg = "ERROR: Step 1: Timeout while navigating to listing ID page."
        emit_progress_update(_msg)
        raise Exception("ERR_PROXY_NOT_READY")
    except Exception as e:
        if "ERR_TIMED_OUT" in str(e):
            _msg = "ERROR: Step 1: Timeout while navigating to listing ID page."
            emit_progress_update(_msg)
            raise Exception("ERR_PROXY_NOT_READY")
    # Step 2: Locate the root element
    emit_progress_update(
        f"Step 2: Locating root element with selector: {SELECTORS['root']}"
    )
    # page.wait_for_event("close", timeout=0)

    page.wait_for_selector(SELECTORS["root"], timeout=MIN)
    root_locators = page.locator(SELECTORS["root"])
    if root_locators.count():
        emit_progress_update(f"Step 2: Root locator found.")
    else:
        _msg = f"ERROR: Step 2: Root locator not found (selector: {SELECTORS['root']})."
        emit_progress_update(_msg)
        raise RuntimeError(_msg)

    # Step 3: Locate the container elements within the root
    emit_progress_update(
        f"Step 3: Locating container elements within the root (selector: {SELECTORS['container']})."
    )
    page.wait_for_selector(SELECTORS["tabindex"], timeout=MIN)
    tabindex_locators = root_locators.first.locator(SELECTORS["tabindex"])
    if tabindex_locators.count():
        emit_progress_update(f"Step 3: tabindex locator found.")
    else:
        _msg = f"ERROR: Step 3: tabindex locator not found (selector: {SELECTORS['container']})."
        emit_progress_update(_msg)
        raise RuntimeError(_msg)

    # Step 4: Filter for product locators
    emit_progress_update(
        "Step 4: Filtering for product locators based on child ServerTextArea element."
    )
    product_locators = tabindex_locators.filter(
        has=page.locator('div[data-type="container"][role="button"]')
    )
    # emit_progress_update(f"Step 4: Filtered for {product_locators.count()} potential product locators.") # Optional: add count

    # Step 5: Select the specific product locator (nth(1))
    emit_progress_update(
        "Step 5: Identifying the specific product locator (nth(1) of filtered results)."
    )
    latest_product_locator = product_locators.nth(0)
    ellipsis_button_locator = latest_product_locator.locator(SELECTORS["button"]).first
    ellipsis_button_locator.evaluate("elm => elm.click();")
    wait_loading(page)
    # Step 6: Wait for the bottom sheet to appear
    emit_progress_update(
        f"Step 6: Waiting for the bottom sheet to appear (selector: {SELECTORS['bottom_sheet']})."
    )
    try:
        page.wait_for_selector(SELECTORS["bottom_sheet"], timeout=30000)
        emit_progress_update("Step 6: Bottom sheet detected.")
    except PlaywrightTimeoutError:
        _msg = "ERROR: Step 6: Timeout while waiting for bottom sheet to appear."
        raise RuntimeError(_msg)

    # Step 7: Ensure the bottom sheet is visible and enabled
    emit_progress_update("Step 7: Verifying bottom sheet visibility and enabled state.")
    bottom_sheet_locators = page.locator(SELECTORS["bottom_sheet"])
    bottom_sheet_locator: Optional[Locator] = None
    count = bottom_sheet_locators.count()
    for i in range(count):
        if (
            bottom_sheet_locators.nth(i).is_visible()
            and bottom_sheet_locators.nth(i).is_enabled()
        ):
            bottom_sheet_locator = bottom_sheet_locators.nth(i)
            emit_progress_update("Step 7: Visible and enabled bottom sheet found.")
            break
    if not bottom_sheet_locator:
        _msg = "ERROR: Step 7: Invalid bottom sheet - could not find a visible and enabled instance."
        raise RuntimeError(_msg)

    # Step 8: Wait for buttons within the bottom sheet
    emit_progress_update(
        "Step 8: Waiting for general buttons to appear within the bottom sheet."
    )
    try:
        page.wait_for_selector(SELECTORS["button"], timeout=30000)
        emit_progress_update("Step 8: Buttons detected within the bottom sheet.")
    except PlaywrightTimeoutError:
        _msg = "ERROR: Step 8: Timeout while waiting for buttons in bottom sheet."
        raise RuntimeError(_msg)

    # Step 9: Search for 'List in more places' button
    emit_progress_update(
        "Step 9: Searching for 'List in more places' button by text content."
    )
    list_more_button_locators: Optional[Locator] = None
    sheet_button_locators = bottom_sheet_locator.locator(SELECTORS["button"])
    count = sheet_button_locators.count()
    for i in range(count):
        btn = sheet_button_locators.nth(i)
        text = btn.text_content()
        if text and "more places" in text.strip().lower():
            list_more_button_locators = btn
            emit_progress_update("Step 9: 'List in more places' button found.")
            break

    if not list_more_button_locators:
        _msg = "ERROR: Step 9: Failed to find 'List in more places' button."
        raise RuntimeError(_msg)

    # Step 10: Click 'List in more places' button
    emit_progress_update("Step 10: Clicking 'List in more places' button.")
    list_more_button_locators.first.evaluate("elm => elm.click();")
    wait_loading(page)
    emit_progress_update("Step 10: 'List in more places' button clicked successfully.")
    # Step 11: Wait for page redirection after clicking 'List in more places'
    emit_progress_update(
        "Step 11: Waiting for page redirection after clicking 'List in more places'."
    )
    try:
        page.wait_for_url(lambda new_url: new_url != listing_id_url, timeout=MIN)
        emit_progress_update(f"Step 11: Page redirected successfully to: {page.url}.")
    except PlaywrightTimeoutError:
        _msg = "ERROR: Step 11: Timeout while waiting for page redirection. Still on the product detail page."
        raise RuntimeError(_msg)

    # Final check after wait_for_url
    if page.url == listing_id_url:
        _msg = (
            "ERROR: Step 11: Page redirection failed. Still on the product detail page."
        )
        raise RuntimeError(_msg)

    # Step 12: Confirmation of successful process
    emit_progress_update("Step 12: Group selection and listing process completed.")
    return True


def get_group_selectors(
    page: Page,
    task,  # RobotTaskType,
    signals,  # BrowserWorkerSignals,
):
    progress: List[int] = [0, 0]
    signals.info_signal.emit(task, "get_group_selectors")

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])

    progress[1] = 7  # Estimated total steps for this function
    emit_progress_update(f"Step 0: Estimated total steps: {progress[1]}")
    wait_loading(page=page)
    # Step 1: Locate the root element
    emit_progress_update(
        f"Step 1: Locating root element with selector: {SELECTORS['root']}"
    )
    root_locators = page.locator(SELECTORS["root"])
    if root_locators.count():
        emit_progress_update(
            f"Step 1: Found `root_locator` (selector: {SELECTORS['root']})."
        )
    else:
        _msg = (
            f"ERROR: Step 1: `root_locator` not found (selector: {SELECTORS['root']})."
        )
        raise RuntimeError(_msg)

    # Step 2: Locate group elements within the root
    emit_progress_update(
        f"Step 2: Locating group elements with selector: {SELECTORS['group']} as direct children of root."
    )
    group_locators = root_locators.first.locator(f":scope > {SELECTORS['group']}")
    # group_locators = root_locators.first.locator(
    #     "./div[contains(@class, 'm') and contains(@class, 'displayed')]"
    # )

    count = group_locators.count()
    if not count:
        _msg = f"ERROR: Step 2: `group_locators` not found (selector: {SELECTORS['group']})."
        page.wait_for_event("close", timeout=0)
        raise RuntimeError(_msg)
    emit_progress_update(
        f"Step 2: Found {count} `group_locators` (selector: {SELECTORS['group']})."
    )

    unlisting_action_id_locators = []
    label_num = 0
    # Regex to find any class starting with 'bg'
    regex_pattern = r"\b" + re.escape("bg") + r"\w*\b"

    # Step 3: Analyze each group locator
    emit_progress_update(
        f"Step 3: Analyzing each found group locator to identify target groups (max 2 non-bg groups)."
    )
    for i in range(count):
        if label_num >= 2:
            break

        group_locator = group_locators.nth(i)
        group_locator_classes = group_locator.get_attribute("class")

        if not group_locator_classes:
            continue
        # Step 4: Check if the group has a class starting with 'bg-'
        if not bool(re.search(regex_pattern, group_locator_classes)):
            label_num += 1
        else:
            focusable_locators = group_locator.locator(SELECTORS["data_action_id"])
            if not focusable_locators.count():
                continue

            # Step 6: Extract data-action-id and add to list
            action_id = focusable_locators.first.get_attribute("data-action-id")
            if action_id:
                unlisting_action_id_locators.append(
                    f"div[data-action-id='{action_id}']"
                )
            else:
                continue
    # Step 7: Final summary
    emit_progress_update(
        f"Step 7: Found `{len(unlisting_action_id_locators)}` selectors for target groups."
    )

    return unlisting_action_id_locators


def list_more_place(
    group_selectors: List[str],
    page: Page,
    task,  # RobotTaskType,
    signals,  # BrowserWorkerSignals,
):
    progress: List[int] = [0, 0]
    signals.info_signal.emit(task, "list_more_place")

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])

    progress[1] = (
        11 + len(group_selectors) * 2
    )  # Estimated total steps for this function
    emit_progress_update(f"Step 0: Estimated total steps: {progress[1]}")

    # Step 1: Iterate and click on each target group
    emit_progress_update(
        f"Step 1: Iterating through {len(group_selectors)} target group selectors and clicking them."
    )
    if not group_selectors:
        emit_progress_update("No group selectors provided. Skipping group clicks.")

    for idx, group_selector in enumerate(group_selectors):
        emit_progress_update(
            f"Step 1.{idx+1}: Locating group with selector: '{group_selector}'."
        )
        group_locators = page.locator(group_selector)
        if not group_locators.count():
            continue

        # Taking a short text snippet for logging
        try:
            text = group_locators.first.text_content().strip()[:50].replace("\n", " ")
            group_locators.first.scroll_into_view_if_needed()
            text_locators = page.locator('div[data-mcomponent="ServerTextArea"][data-type="text"][class="m displayed"]')
            if text_locators.count() > 2:
                # So sánh vị trí DOM: group_locators.first phải nằm trên text_locators.nth(1)
                group_handle = group_locators.first.element_handle()
                second_text_handle = text_locators.nth(1).element_handle()
                if group_handle and second_text_handle:
                    result = page.evaluate(
                        '''([elm1, elm2]) => {
                            if (!elm1 || !elm2) return null;
                            return elm1.compareDocumentPosition(elm2);
                        }''',
                        [group_handle, second_text_handle]
                    )
                    # Nếu group_locators.first nằm trên text_locators.nth(1) (FOLLOWING = 4)
                    if not (result & 4):
                        continue
            group_locators.first.evaluate("elm => elm.click();")
            wait_loading(page)
            emit_progress_update(f"Step 1.{idx+1}: Successfully clicked group.")
        except Exception as e:
            continue

    # Step 2: Locate the fixed bottom footer
    emit_progress_update("Step 2: Locating the fixed bottom footer.")
    fixed_bottom_locators = page.locator(SELECTORS["fixed_bottom"])
    if not fixed_bottom_locators.count():
        _msg = "ERROR: Step 2: Fixed bottom footer not found."
        emit_progress_update(_msg)
        raise RuntimeError(_msg)
    emit_progress_update("Step 2: Found the fixed bottom footer.")

    # Step 3: Locate the 'Post' button within the footer
    emit_progress_update("Step 3: Locating the 'Post' button within the footer.")
    post_button_locators = fixed_bottom_locators.locator(SELECTORS["focusable"])

    # A more robust check for the 'Post' button, using has_text
    # assuming SELECTORS["focusable"] is generic like 'div[data-focusable="true"]'
    post_button_locator: Optional[Locator] = None
    if post_button_locators.count():
        # Iterate to find the specific "Post" button
        for i in range(post_button_locators.count()):
            btn = post_button_locators.nth(i)
            text = btn.text_content()
            if text and "post" in text.strip().lower():
                post_button_locator = btn
                emit_progress_update(
                    f"Step 3: Found 'Post' button (text: '{text.strip()}')."
                )
                break

    if not post_button_locator:
        _msg = "ERROR: Step 3: 'Post' button not found within the footer."
        raise RuntimeError(_msg)

    # Step 4: Click the 'Post' button
    emit_progress_update("Step 4: Clicking the 'Post' button.")
    post_button_locator.evaluate("elm => elm.click()")
    wait_loading(page)
    emit_progress_update("Step 4: Successfully clicked the 'Post' button.")

    # Step 5: Final confirmation/cleanup
    emit_progress_update("Step 5: Group selection and listing process completed.")

    # Step 6: Wait for page redirection in 3s.
    emit_progress_update("Step 6: Wait for page redirection in 3s.")
    wait_loading(page)
    sleep(1)
    emit_progress_update("Step 6: Waited!")
    return True


def wait_loading(page: Page):
    # Wait until the loading overlay disappears from the DOM (if present)
    try:
        page.wait_for_selector(SELECTORS["loading"], state="detached", timeout=MIN)
    except PlaywrightTimeoutError:
        # If timeout, maybe loading overlay never appeared or took too long
        pass
