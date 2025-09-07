import random
import sys, traceback
from typing import List
from time import sleep
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from src.my_types import (
    RobotTaskType,
    BrowserWorkerSignals,
    SellPayloadType,
    RobotSettingsType,
)
from src.robot import selector_constants as selectors
from src.robot.actions import fb_utils

MIN = 60_000


def discussion(
    page: Page,
    task: RobotTaskType,
    settings: RobotSettingsType,
    signals: BrowserWorkerSignals,
):
    signals.info_signal.emit(task, "Action - discussion")
    action_payload: SellPayloadType = task.action_payload
    progress: List[int] = [0, 0]

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])

    try:
        groups_num = settings.group_num
        progress[1] = 5 + int(groups_num) * 5
        signals.progress_signal.emit(
            task,
            f"Estimated total steps: {progress[1]}. Number of groups to process: {groups_num}.",
            [progress[0], progress[1]],
        )
        current_group_processed = 0
        emit_progress_update("Navigating to Facebook general groups page.")
        try:
            page.goto("https://www.facebook.com/groups/feed/", timeout=MIN)
            is_049 = fb_utils.redirect_out_049(page)
            if is_049 == 2:
                page.goto("https://www.facebook.com/groups/feed/", timeout=MIN)
            elif is_049 == 0:
                return False

            signals.progress_signal.emit(
                task,
                "Successfully navigated to general groups page.",
                [progress[0], progress[1]],
            )
        except PlaywrightTimeoutError as e:
            signals.progress_signal.emit(
                task,
                f"ERROR: Timeout while navigating to general groups page. Details: {str(e)}",
                [progress[0], progress[1]],
            )
            raise Exception("ERR_PROXY_NOT_READY")
        emit_progress_update("Checking page language.")
        page_language = page.locator("html").get_attribute("lang")
        signals.progress_signal.emit(
            task,
            f"Detected page language: '{page_language}'.",
            [progress[0], progress[1]],
        )
        if page_language != "en":
            signals.progress_signal.emit(
                task,
                "WARNING: Page language is not English. Language conversion required.",
                [progress[0], progress[1]],
            )
            return False

        emit_progress_update(
            "Waiting for group sidebar to load (if loading icon is present)."
        )
        sidebar_locator = page.locator(
            f"{selectors.S_NAVIGATION}:not({selectors.S_BANNER} {selectors.S_NAVIGATION})"
        )

        group_locators = sidebar_locator.first.locator(
            "a[href^='https://www.facebook.com/groups/']"
        )

        loading_attempt = 0
        max_loading_attempts = 10
        while (
            sidebar_locator.first.locator(selectors.S_LOADING).count()
            and loading_attempt < max_loading_attempts
        ):
            loading_attempt += 1
            signals.progress_signal.emit(
                task,
                f"Loading indicator detected in sidebar. Waiting... (Attempt {loading_attempt}/{max_loading_attempts})",
                [progress[0], progress[1]],
            )
            _loading_element = sidebar_locator.first.locator(selectors.S_LOADING)
            try:
                sleep(random.uniform(1, 3))
                _loading_element.first.scroll_into_view_if_needed(timeout=100)
                signals.progress_signal.emit(
                    task,
                    "Loading indicator scrolled into view.",
                    [progress[0], progress[1]],
                )
            except PlaywrightTimeoutError as e:
                signals.progress_signal.emit(
                    task,
                    f"ERROR: Timeout while scrolling loading indicator. Details: {str(e)}. Exiting wait loop.",
                    [progress[0], progress[1]],
                )
                break
            except Exception as e:
                if "ERR_PROXY_NOT_READY" == str(e) or "ERR_TIMED_OUT" in str(e):
                    raise e
                signals.progress_signal.emit(
                    task,
                    f"ERROR: An unexpected error occurred while scrolling loading indicator. Details: {str(e)}. Exiting wait loop.",
                    [progress[0], progress[1]],
                )
                break
        if loading_attempt >= max_loading_attempts:
            signals.progress_signal.emit(
                task,
                f"WARNING: Exceeded maximum loading wait attempts ({max_loading_attempts}). Continuing without full sidebar load confirmation.",
                [progress[0], progress[1]],
            )
        else:
            signals.progress_signal.emit(
                task,
                "Group sidebar loaded or no loading indicator found.",
                [progress[0], progress[1]],
            )

        emit_progress_update("Searching for group URLs in the sidebar.")
        group_locators = sidebar_locator.first.locator(
            "a[href^='https://www.facebook.com/groups/']"
        )
        group_urls = [
            href
            for group_locator in group_locators.all()
            if (href := group_locator.get_attribute("href")) is not None
        ]
        signals.progress_signal.emit(
            task, f"Found {len(group_urls)} group URLs.", [progress[0], progress[1]]
        )
        if not group_urls:
            signals.progress_signal.emit(
                task,
                "WARNING: No group URLs could be retrieved. No groups to post in.",
                [progress[0], progress[1]],
            )
            signals.warning_signal.emit(
                task,
                "Could not retrieve any group URLs.",
            )
            return False

        signals.progress_signal.emit(
            task,
            f"Starting loop through groups to post. (Total groups found: {len(group_urls)})",
            [progress[0], progress[1]],
        )
        for i, group_url in enumerate(group_urls):
            if current_group_processed >= groups_num:
                signals.progress_signal.emit(
                    task,
                    f"Processed {groups_num} groups. Stopping group loop.",
                    [progress[0], progress[1]],
                )
                break

            emit_progress_update(
                f"Processing group {i+1}/{len(group_urls)} (Target: {groups_num} groups): {group_url}"
            )

            try:
                page.goto(group_url, timeout=MIN)
                is_049 = fb_utils.redirect_out_049(page)
                if is_049 == 2:
                    page.goto(group_url, timeout=MIN)
                elif is_049 == 0:
                    return False
                signals.progress_signal.emit(
                    task,
                    f"Successfully navigated to group: {group_url}",
                    [progress[0], progress[1]],
                )
            except PlaywrightTimeoutError as e:
                signals.progress_signal.emit(
                    task,
                    f"ERROR: Timeout while navigating to group {group_url}. Details: {str(e)}. Skipping this group.",
                    [progress[0], progress[1]],
                )
                continue

            main_locator = page.locator(selectors.S_MAIN)
            tablist_locator = main_locator.first.locator(selectors.S_TABLIST)

            signals.progress_signal.emit(
                task,
                "Checking group tabs for 'Discussion' or 'Buy/Sell Discussion' tab.",
                [progress[0], progress[1]],
            )
            is_discussion_tab_found = (
                True  # Default to True, then set to False if Buy/Sell is primary.
            )
            # This variable seems to control if posting should proceed.
            if tablist_locator.first.is_visible(timeout=5000):
                tab_locators = tablist_locator.first.locator(selectors.S_TABLIST_TAB)
                signals.progress_signal.emit(
                    task,
                    f"Found {tab_locators.count()} tabs in the group.",
                    [progress[0], progress[1]],
                )
                # Iterate through tabs to find the preferred discussion tab
                # and check for 'buy_sell_discussion' which might indicate not to post
                buy_sell_found_and_clicked = (
                    False  # Flag to indicate if we clicked buy/sell
                )
                discussion_clicked = (
                    False  # Flag to indicate if we clicked generic discussion
                )

                for tab_index in range(tab_locators.count()):
                    tab_locator = tab_locators.nth(tab_index)
                    try:
                        tab_url = tab_locator.get_attribute("href", timeout=5_000)
                        if not tab_url:
                            signals.progress_signal.emit(
                                task,
                                f"WARNING: Tab {tab_index} has no URL. Skipping.",
                                [progress[0], progress[1]],
                            )
                            continue

                        cleaned_tab_url = tab_url.rstrip("/")

                        signals.progress_signal.emit(
                            task,
                            f"Checking Tab {tab_index}: URL = '{cleaned_tab_url}'",
                            [progress[0], progress[1]],
                        )

                        fb_utils.close_dialog()

                        # Prioritize clicking "Discussion" if it exists
                        if cleaned_tab_url.endswith(
                            "discussion"
                        ) and not cleaned_tab_url.endswith("buy_sell_discussion"):
                            signals.progress_signal.emit(
                                task,
                                f"Found 'Discussion' tab at URL: {cleaned_tab_url}. Clicking this tab.",
                                [progress[0], progress[1]],
                            )
                            tab_locator.click()
                            discussion_clicked = True
                            is_discussion_tab_found = (
                                True  # Ensure this is true if we click discussion
                            )
                            # We can break here if clicking generic discussion is the primary goal
                            # If you want to check ALL tabs before deciding, then don't break
                            break  # Assume once generic discussion is clicked, we are good to go.

                        # If generic discussion isn't found/clicked yet, check for buy_sell
                        if cleaned_tab_url.endswith("buy_sell_discussion"):
                            signals.progress_signal.emit(
                                task,
                                f"Found 'Buy/Sell Discussion' tab at URL: {cleaned_tab_url}. This group might not be suitable for general posting.",
                                [progress[0], progress[1]],
                            )
                            # If buy/sell is found, we might want to prevent general posting
                            # This depends on your business logic. Assuming we want to skip if it's primary.
                            is_discussion_tab_found = False
                            # Do not break here if you still want to look for a generic "discussion" tab later in the loop.
                            # If finding 'buy_sell_discussion' means "stop, this group is no good", then `break` here.
                            # For now, let's assume if it's a buy/sell group, we skip it.
                            break  # Break if finding buy/sell discussion means we should skip this group.

                    except PlaywrightTimeoutError as e:
                        signals.progress_signal.emit(
                            task,
                            f"ERROR: Timeout while getting URL for tab {tab_index}. Details: {str(e)}. Skipping this tab.",
                            [progress[0], progress[1]],
                        )
                        continue
                    except Exception as e:
                        if "ERR_PROXY_NOT_READY" == str(e) or "ERR_TIMED_OUT" in str(e):
                            raise e
                        signals.progress_signal.emit(
                            task,
                            f"ERROR: An error occurred while processing tab {tab_index}. Details: {str(e)}. Skipping this tab.",
                            [progress[0], progress[1]],
                        )
                        continue

                # After iterating all tabs, if no generic discussion tab was clicked
                # and a buy_sell tab was found and is_discussion_tab_found got set to False
                if (
                    not discussion_clicked and not is_discussion_tab_found
                ):  # This means we found a buy/sell and didn't click generic discussion
                    signals.progress_signal.emit(
                        task,
                        "No general 'Discussion' tab clicked and 'Buy/Sell Discussion' tab was detected. Skipping group.",
                        [progress[0], progress[1]],
                    )
                    continue  # Skip this group if it's primarily a buy/sell group and no general discussion tab was clicked.

            else:  # if tablist_locator is not visible
                signals.progress_signal.emit(
                    task,
                    "WARNING: Tablist not visible for this group. Cannot determine discussion tab. Skipping group.",
                    [progress[0], progress[1]],
                )
                continue

            # This check is now redundant if the above logic correctly sets is_discussion_tab_found and continues
            # if not is_discussion_tab_found:
            #     signals.progress_signal.emit(
            #         task,
            #         "Found 'Buy/Sell Discussion' tab in this group or no suitable discussion tab found. Skipping group.",
            #         [progress[0], progress[1]],
            #     )
            #     continue

            emit_progress_update(
                "Waiting and scrolling to the post creation area in the group."
            )
            profile_locator = main_locator.first.locator(selectors.S_PROFILE)
            try:
                profile_locator.first.first.wait_for(state="attached", timeout=MIN)
                signals.progress_signal.emit(
                    task,
                    "Profile/post creation area is attached.",
                    [progress[0], progress[1]],
                )
            except PlaywrightTimeoutError as e:  # Catch specific error
                signals.progress_signal.emit(
                    task,
                    f"ERROR: Profile/post creation area not attached within timeout. Details: {str(e)}. Skipping this group.",
                    [progress[0], progress[1]],
                )
                continue
            except Exception as e:  # Catch other potential errors
                if "ERR_PROXY_NOT_READY" == str(e) or "ERR_TIMED_OUT" in str(e):
                    raise e
                signals.progress_signal.emit(
                    task,
                    f"ERROR: An unexpected error occurred while waiting for profile/post creation area. Details: {str(e)}. Skipping this group.",
                    [progress[0], progress[1]],
                )
                continue

            sleep(random.uniform(1, 3))
            profile_locator.first.scroll_into_view_if_needed()
            signals.progress_signal.emit(
                task, "Profile area scrolled into view.", [progress[0], progress[1]]
            )

            emit_progress_update(
                "Finding and clicking 'Discussion' or 'Write Something' button to open post creation dialog."
            )
            # Re-evaluating discussion_btn_locator logic. It should find a button related to creating posts
            # not just assign profile_locator to it. Assuming selectors.S_POST_INITIATOR_BUTTON is correct
            # or a more specific locator is needed within profile_locator
            # If the original intent was to search for the button *around* profile_locator, the walk is fine.

            # We need a robust way to find the "Write something..." or "Discussion" button
            # Let's assume S_POST_INITIATOR_BUTTON is a selector for this.
            # If not, the `while walk_count` loop attempts to find it by moving up parents.

            # The original line 'discussion_btn_locator = profile_locator'
            # needs to be followed by actual location logic.
            # The loop is trying to find it, which is good.
            # Make sure selectors.S_BUTTON is the correct general button selector

            # Start search for post initiation button from a relevant parent or sibling of profile_locator
            # For robustness, you might want a more direct selector if possible
            # Or assume profile_locator is the parent of the button.

            # Let's keep the existing walk-up logic, but ensure `discussion_btn_locator` starts
            # at a point where the button can actually be found.
            # Assuming profile_locator is a good starting point for the button search

            discussion_btn_candidate_locator = profile_locator.first.locator(
                selectors.S_BUTTON
            )  # Try direct children
            button_found = False

            if discussion_btn_candidate_locator.count() > 0:
                discussion_btn_locator = discussion_btn_candidate_locator.first
                signals.progress_signal.emit(
                    task,
                    f"Found 'Discussion' (or similar) button directly under profile area.",
                    [progress[0], progress[1]],
                )
                button_found = True
            else:
                # If not found directly, walk up parents as per original logic
                temp_locator_walk = profile_locator.first
                max_parent_walks = 5
                walk_count = 0
                while walk_count < max_parent_walks:
                    walk_count += 1
                    # Get the parent of the current temp_locator_walk and then look for a button
                    parent_locator = temp_locator_walk.locator("..")
                    temp_button_locator = parent_locator.locator(selectors.S_BUTTON)

                    if temp_button_locator.count():
                        discussion_btn_locator = temp_button_locator.first
                        signals.progress_signal.emit(
                            task,
                            f"Found 'Discussion' (or similar) button after {walk_count} DOM tree walks.",
                            [progress[0], progress[1]],
                        )
                        button_found = True
                        break
                    else:
                        temp_locator_walk = (
                            parent_locator  # Move up to the parent for next iteration
                        )
                        signals.progress_signal.emit(
                            task,
                            f"Button not found, moving up parent. (Attempt {walk_count})",
                            [progress[0], progress[1]],
                        )

            if not button_found:
                signals.progress_signal.emit(
                    task,
                    "WARNING: 'Discussion' or 'Write Something' button not found within limit. Skipping this group.",
                    [progress[0], progress[1]],
                )
                continue

            sleep(random.uniform(1, 3))
            try:
                discussion_btn_locator.scroll_into_view_if_needed()
                discussion_btn_locator.click()
                signals.progress_signal.emit(
                    task,
                    "Clicked 'Discussion' button to open post creation dialog.",
                    [progress[0], progress[1]],
                )
            except Exception as e:
                if "ERR_PROXY_NOT_READY" == str(e) or "ERR_TIMED_OUT" in str(e):
                    raise e
                signals.progress_signal.emit(
                    task,
                    f"ERROR: Could not click 'Discussion' button or scroll into view. Details: {str(e)}. Skipping this group.",
                    [progress[0], progress[1]],
                )
                continue

            emit_progress_update(
                f"Waiting for post creation dialog ('{selectors.S_DIALOG_CREATE_POST}') to appear and loading to complete."
            )
            dialog_locator = page.locator(selectors.S_DIALOG_CREATE_POST)
            try:
                dialog_locator.first.locator(selectors.S_LOADING).first.wait_for(
                    state="detached", timeout=30_000
                )
                signals.progress_signal.emit(
                    task,
                    "Loading in post creation dialog completed.",
                    [progress[0], progress[1]],
                )
            except PlaywrightTimeoutError as e:
                signals.progress_signal.emit(
                    task,
                    f"ERROR: Timeout while waiting for loading in post creation dialog. Details: {str(e)}. Skipping this group.",
                    [progress[0], progress[1]],
                )
                continue

            # Need to re-locate dialog_container_locator after wait_for detached
            # if the dialog itself might be re-rendered or change state, but usually it's fine.
            dialog_container_locator = dialog_locator.first.locator(
                "xpath=ancestor::*[contains(@role, 'dialog')][1]"
            )

            if action_payload.image_paths:
                signals.progress_signal.emit(
                    task,
                    f"Detected {len(action_payload.image_paths)} image paths. Processing upload.",
                    [progress[0], progress[1]],
                )
                try:
                    dialog_container_locator.locator(
                        selectors.S_IMG_INPUT
                    ).first.wait_for(state="attached", timeout=10_000)
                    signals.progress_signal.emit(
                        task,
                        "Image input is directly ready.",
                        [progress[0], progress[1]],
                    )
                except PlaywrightTimeoutError as e:
                    signals.progress_signal.emit(
                        task,
                        "WARNING: Image input not directly ready. Attempting to click image button. Details: {str(e)}",
                        [progress[0], progress[1]],
                    )
                    try:
                        image_btn_locator = dialog_container_locator.first.locator(
                            selectors.S_IMAGE_BUTTON
                        )
                        sleep(random.uniform(1, 3))
                        image_btn_locator.click()
                        signals.progress_signal.emit(
                            task,
                            "Clicked image button to open input.",
                            [progress[0], progress[1]],
                        )
                    except Exception as e:
                        signals.progress_signal.emit(
                            task,
                            f"ERROR: Could not click image button. Skipping image upload. Details: {str(e)}",
                            [progress[0], progress[1]],
                        )
                        action_payload.image_paths = (
                            []
                        )  # Clear paths to prevent further attempts
                finally:  # This finally block runs regardless of the try/except in the outer block
                    if action_payload.image_paths:  # Check again if paths were cleared
                        try:
                            image_input_locator = dialog_container_locator.locator(
                                selectors.S_IMG_INPUT
                            )
                            sleep(random.uniform(1, 3))
                            image_input_locator.set_input_files(
                                action_payload.image_paths, timeout=10000
                            )
                            signals.progress_signal.emit(
                                task,
                                "Successfully set image files.",
                                [progress[0], progress[1]],
                            )
                        except PlaywrightTimeoutError as e:
                            signals.progress_signal.emit(
                                task,
                                f"ERROR: Timeout while setting image files. Image might not be uploaded. Details: {str(e)}",
                                [progress[0], progress[1]],
                            )
                        except Exception as e:
                            signals.progress_signal.emit(
                                task,
                                f"ERROR: An error occurred while setting image files. Image might not be uploaded. Details: {str(e)}",
                                [progress[0], progress[1]],
                            )
            else:
                signals.progress_signal.emit(
                    task,
                    "No image paths provided. Skipping image upload.",
                    [progress[0], progress[1]],
                )

            emit_progress_update(
                "Filling title and description into the post creation text box."
            )
            textbox_locator = dialog_container_locator.first.locator(
                selectors.S_TEXTBOX
            )
            sleep(random.uniform(1, 3))
            try:
                content_to_fill = action_payload.description
                textbox_locator.fill(content_to_fill)
                signals.progress_signal.emit(
                    task,
                    f"Filled post content (Title: '{action_payload.title}', Description: '{action_payload.description}').",
                    [progress[0], progress[1]],
                )
            except Exception as e:
                signals.progress_signal.emit(
                    task,
                    f"ERROR: Could not fill content into the text box. Details: {str(e)}. Skipping this group.",
                    [progress[0], progress[1]],
                )
                continue

            emit_progress_update(
                "Waiting for 'Post' button to be enabled and clicking."
            )
            post_btn_locators = dialog_container_locator.first.locator(
                selectors.S_POST_BUTTON
            )
            try:
                # Wait for the button's disabled state to be removed
                dialog_container_locator.locator(
                    f"{selectors.S_POST_BUTTON}[aria-disabled='true']"
                ).first.wait_for(state="detached", timeout=30_000)
                signals.progress_signal.emit(
                    task, "'Post' button is now enabled.", [progress[0], progress[1]]
                )
                post_btn_locators.first.click()
                signals.progress_signal.emit(
                    task, "Clicked 'Post' button.", [progress[0], progress[1]]
                )
            except PlaywrightTimeoutError as e:
                signals.progress_signal.emit(
                    task,
                    f"ERROR: Timeout while waiting for 'Post' button to be enabled or clicked. Post might not have been published. Details: {str(e)}",
                    [progress[0], progress[1]],
                )
                signals.warning_signal.emit(
                    task,
                    "Could not click Post button or button remained disabled.",
                )
                continue

            emit_progress_update("Waiting for post creation dialog to close.")
            try:
                dialog_container_locator.first.wait_for(
                    state="detached", timeout=30_000
                )
                signals.progress_signal.emit(
                    task,
                    "Post creation dialog closed successfully.",
                    [progress[0], progress[1]],
                )
            except PlaywrightTimeoutError as e:
                signals.progress_signal.emit(
                    task,
                    f"ERROR: Timeout while waiting for post creation dialog to close. Post might not have been published successfully or dialog is stuck. Details: {str(e)}",
                    [progress[0], progress[1]],
                )
                signals.warning_signal.emit(
                    task,
                    "Post creation dialog did not close after publishing. Post might have failed.",
                )
                break  # If dialog doesn't close, it's a critical issue, break from group loop.

            sleep(random.uniform(1, 3))
            current_group_processed += 1
            signals.progress_signal.emit(
                task,
                f"Successfully processed {current_group_processed}/{groups_num} groups.",
                [progress[0], progress[1]],
            )

            if current_group_processed >= groups_num:
                signals.progress_signal.emit(
                    task,
                    f"Processed {groups_num} groups. Ending posting task.",
                    [progress[0], progress[1]],
                )
                break

        signals.progress_signal.emit(
            task,
            f"Completed group processing loop. Total groups posted: {current_group_processed}/{groups_num}.",
            [progress[0], progress[1]],
        )

        signals.progress_signal.emit(
            task, "Discussion task completed successfully.", [progress[0], progress[1]]
        )
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
