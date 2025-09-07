import random
import sys, traceback
from time import sleep
from typing import List, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Locator
from src.my_types import RobotTaskType, BrowserWorkerSignals, RobotSettingsType
from src.robot import selector_constants as selectors
from src.robot.actions import fb_utils

MIN = 60_000


def list_on_marketplace(
    page: Page,
    task: RobotTaskType,
    settings: RobotSettingsType,
    signals: BrowserWorkerSignals,
    is_publish=True,
) -> bool:
    signals.info_signal.emit(task, "Action - list_on_marketplace")
    progress: List[int] = [0, 0]

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])

    progress[1] = 22
    emit_progress_update(f"Step 0: Estimated total steps: {progress[1]}")
    try:
        try:
            page.goto(
                "https://www.facebook.com/marketplace/create/item",
                timeout=MIN,
            )
            is_049 = fb_utils.redirect_out_049(page)
            if is_049 == 2:
                page.goto(
                    "https://www.facebook.com/marketplace/create/item",
                    timeout=MIN,
                )
            elif is_049 == 0:
                return False
            emit_progress_update(
                "Successfully navigated to Marketplace item creation page."
            )
        except PlaywrightTimeoutError as e:
            emit_progress_update(
                "ERROR: Timeout while navigating to Marketplace creation page."
            )
            raise Exception("ERR_PROXY_NOT_READY")

        emit_progress_update("Starting listing on marketplace.")
        page_language = page.locator("html").get_attribute("lang")
        if page_language != "en":
            failed_msg = (
                f"Cannot start {task.action_name}. Please switch language to English."
            )
            raise RuntimeError(failed_msg)

        emit_progress_update(
            f"Locating marketplace_form with selector: {selectors.S_MARKETPLACE_FORM}"
        )
        page.wait_for_selector(selectors.S_MARKETPLACE_FORM, timeout=MIN)
        marketplace_forms = page.locator(selectors.S_MARKETPLACE_FORM)
        if not marketplace_forms.count():
            _msg = f"marketplace_form locator not found (selector: {selectors.S_MARKETPLACE_FORM})."
            raise RuntimeError(_msg)
        marketplace_form: Optional[Locator] = None
        for marketplace_form_candidate in marketplace_forms.all():
            if (
                marketplace_form_candidate.is_visible()
                and marketplace_form_candidate.is_enabled()
            ):
                marketplace_form = marketplace_form_candidate
                break
        if not marketplace_form.count():
            _msg = f"marketplace_form is not found or is not interactive."
            raise RuntimeError(_msg)

        emit_progress_update("Try closing anonymous dialogs.")
        fb_utils.close_dialog(page)

        emit_progress_update(
            f"Locating expand_button with selector: {selectors.S_EXPAND_BUTTON}."
        )
        page.wait_for_selector(selectors.S_EXPAND_BUTTON, timeout=MIN)
        expand_btn_locators = marketplace_form.locator(selectors.S_EXPAND_BUTTON)
        if not expand_btn_locators.count():
            _msg = f"expand_button locator not found (selector: {selectors.S_EXPAND_BUTTON})"
            raise RuntimeError(_msg)
        sleep(random.uniform(0.2, 1.5))
        expand_btn_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        expand_btn_locators.first.click(timeout=MIN)
        emit_progress_update("Clicked the more details button.")

        emit_progress_update(
            f"Locating description with selector: {selectors.S_TEXTAREA}."
        )
        page.wait_for_selector(selectors.S_TEXTAREA, timeout=MIN)
        description_locators = marketplace_form.locator(selectors.S_TEXTAREA)
        if not description_locators.count():
            _msg = f"description locator not found (selector: {selectors.S_TEXTAREA})"
            raise RuntimeError(_msg)
        sleep(random.uniform(0.2, 1.5))
        description_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        description_locators.first.fill(
            value=task.action_payload.description, timeout=MIN
        )
        emit_progress_update("Filled data into the description field.")

        # --------------

        emit_progress_update(
            f"Locating title_locator, price_locator, location_locator with selector: {selectors.S_INPUT_TEXT}."
        )
        page.wait_for_selector(selectors.S_INPUT_TEXT, timeout=MIN)
        input_text_locators = marketplace_form.locator(selectors.S_INPUT_TEXT)
        title_locator = input_text_locators.nth(0)
        price_locator = input_text_locators.nth(1)
        location_locator = input_text_locators.nth(3)

        emit_progress_update("Filling data into the title field.")
        sleep(random.uniform(0.2, 1.5))
        title_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        title_locator.fill(value=task.action_payload.title, timeout=MIN)
        emit_progress_update("Filled data into the title field.")

        emit_progress_update("Filling data into the price field.")
        sleep(random.uniform(0.2, 1.5))
        price_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        price_locator.fill(value="0", timeout=MIN)
        sleep(random.uniform(0.2, 1.5))
        emit_progress_update("Filled data into the price field.")

        emit_progress_update("Filling data into the location field.")
        location_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        location_locator.fill("Da Lat")
        location_locator.press(" ")
        location_listbox_locators = page.locator(selectors.S_UL_LISTBOX)
        sleep(random.uniform(0.2, 1.5))
        location_listbox_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        location_listbox_locators.first.wait_for(state="attached", timeout=MIN)
        location_option_locators = location_listbox_locators.first.locator(
            selectors.S_LI_OPTION
        )
        sleep(random.uniform(0.2, 1.5))
        location_option_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        location_option_locators.first.click(timeout=MIN)
        emit_progress_update("Filled data into the location field.")

        combobox_locators = page.locator(selectors.S_LABEL_COMBOBOX_LISTBOX)
        category_locator = combobox_locators.nth(0)
        condition_locator = combobox_locators.nth(1)

        emit_progress_update("Filling data into the category field.")
        sleep(random.uniform(0.2, 1.5))
        category_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        category_locator.click(timeout=MIN)

        dialog_locators = page.locator(selectors.S_DIALOG_DROPDOWN)
        dialog_locators.first.wait_for(state="attached", timeout=MIN)
        dialog_button_locators = dialog_locators.first.locator(selectors.S_BUTTON)
        dialog_misc_button_locator = dialog_button_locators.nth(
            dialog_button_locators.count() - 2
        )
        sleep(random.uniform(0.2, 1.5))
        dialog_misc_button_locator.scroll_into_view_if_needed()
        dialog_misc_button_locator.click(timeout=MIN)
        dialog_locators.wait_for(state="detached")
        emit_progress_update("Filled data into the category field.")

        emit_progress_update("Filling data into the condition field.")
        sleep(random.uniform(0.2, 1.5))
        condition_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        condition_locator.click(timeout=MIN)
        listbox_locators = page.locator(selectors.S_DIV_LISTBOX)
        listbox_locators.first.wait_for(state="attached", timeout=MIN)
        listbox_option_locators = listbox_locators.first.locator(selectors.S_DIV_OPTION)

        sleep(random.uniform(0.2, 1.5))
        listbox_option_locators.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.2, 1.5))
        listbox_option_locators.first.click(timeout=MIN)
        dialog_locators.wait_for(state="detached")
        emit_progress_update("Filled data into the condition field.")

        emit_progress_update("Filling data into the images field.")
        image_input_locators = marketplace_form.locator(selectors.S_IMG_INPUT)
        sleep(random.uniform(0.2, 1.5))
        image_input_locators.first.set_input_files(task.action_payload.image_paths)
        emit_progress_update("Filled data into the images field.")

        # ------- click next

        emit_progress_update("Clicking the 'Next' button.")
        clicked_next_result = fb_utils.click_button(
            page, selectors.S_NEXT_BUTTON, 30_000
        )
        emit_progress_update(clicked_next_result["message"])
        if not clicked_next_result["status"]:
            clicked_publish_result = fb_utils.click_button(
                page, selectors.S_PUBLISH_BUTTON, 30_000
            )
            # if not clicked_publish_result["status"]:
            #     raise RuntimeError("Could not click Next button or Publish button")
            sleep(60)
            return True
        if is_publish:
            clicked_publish_result = fb_utils.click_button(
                page, selectors.S_PUBLISH_BUTTON, 30_000
            )
            sleep(60)
            return False
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
