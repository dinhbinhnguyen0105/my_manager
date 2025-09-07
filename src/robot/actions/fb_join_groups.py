import random, os, json, re
from typing import List
from time import sleep
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from src.my_types import RobotTaskType, BrowserWorkerSignals, RobotSettingsType
from src.robot import selector_constants as selectors
from src.robot.actions import fb_utils

MIN = 60_000


def join_groups(
    page: Page,
    task: RobotTaskType,
    settings: RobotSettingsType,
    signals: BrowserWorkerSignals,
):
    signals.info_signal.emit(task, "Action - check_group")
    robot_settings: RobotSettingsType = settings
    group_urls_from_file = get_groups_from_file(robot_settings.group_file_path)
    if not group_urls_from_file:
        signals.warning_signal.emit(task, "Invalid target groups")
        return False

    progress: List[int] = [0, 0]

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])

    group_urls = get_groups(page=page, task=task, signals=signals)
    # Remove any URLs from group_urls_from_file that are also present in group_urls
    target_group_urls = [url for url in group_urls_from_file if url not in group_urls]

    group_count = 0
    try:
        while group_count < robot_settings.group_num:
            _ = target_group_urls.pop(0)
            page.goto(_, timeout=60_000)
            is_049 = fb_utils.redirect_out_049(page)
            if is_049 == 2:
                page.goto(_, timeout=60_000)
            elif is_049 == 0:
                return False
            sleep(3)

            button_locator = page.locator('div[role="button"]')
            for i in range(button_locator.count()):
                label = button_locator.nth(i).get_attribute("aria-label")
                if label and label.lower() == "join group":
                    if button_locator.nth(i).is_visible():
                        button_locator.nth(i).scroll_into_view_if_needed(timeout=30_000)
                        button_locator.nth(i).click()
                        group_count += 1
                        sleep(3)
                        break
            # print(f"\t\t\t[{task.user_info.username}] Join {group_count} group.")
        return True
    except Exception as e:
        raise e


def get_groups(page: Page, task: RobotTaskType, signals: BrowserWorkerSignals):
    progress: List[int] = [0, 0]

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])

    emit_progress_update("Navigating to Facebook general groups page.")
    try:
        page.goto("https://www.facebook.com/groups/feed/", timeout=MIN)
        is_049 = fb_utils.redirect_out_049(page)
        if is_049 == 2:
            page.goto("https://www.facebook.com/groups/feed/", timeout=MIN)
        elif is_049 == 0:
            return False
        sleep(10)
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
    try:
        group_locators.last.scroll_into_view_if_needed()
        sleep(10)
    except Exception as e:
        print(e)
    loading_attempt = 0
    max_loading_attempts = 20
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
            _loading_element.first.scroll_into_view_if_needed(timeout=10_000)
            sleep(3)
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
        except Exception as ex:
            signals.progress_signal.emit(
                task,
                f"ERROR: An unexpected error occurred while scrolling loading indicator. Details: {str(ex)}. Exiting wait loop.",
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
        return []
    return group_urls


def get_groups_from_file(file_path: str) -> List[str]:
    if not os.path.exists(file_path):
        return []
    data: List[dict] = []
    with open(file_path, "r", encoding="utf8") as f:
        data = json.load(f)

    for item in data:
        member_info: str = item.get("memberInfo", "")
        member_raw_num = re.findall(r"-?\d+\.?\d*", member_info)[0]
        member = float(member_raw_num)
        if "k" in member_info.lower():
            member = float(member_raw_num) * 1000
        item["memberInfo"] = member
    data.sort(key=lambda x: x.get("memberInfo", 0), reverse=True)
    return [item.get("url", "") for item in data]
