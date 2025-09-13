import random, os, sys, traceback
from time import sleep
from typing import List, Optional, Union
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, Locator
from src.my_types import (
    RobotTaskType,
    BrowserWorkerSignals,
    RobotSettingsType,
    BrowserTaskType,
    SellPayloadType,
)

# from src.robot import selector_constants as selectors
from src.robot.actions import fb_utils

MIN = 60_000


class Selectors:
    button_label = 'div[role="button"][aria-label]'
    button_without_label = 'div[role="button"]:not([aria-label])'
    button_expanded = 'div[role="button"][aria-expanded="false"]'
    button_condition = "label[role='combobox']"
    dialog = 'div[role="dialog"]'
    input_image = 'input[accept="image/*,image/heif,image/heic"][type="file"]'
    input_location = 'input[type="text"]'
    input_description = "textarea"
    location_box = "ul[role='listbox']"
    location_box_item = "li[role='option']"
    condition_box = "div[role='listbox']"
    condition_box_item = "div[role='option']"
    detail_dialog = 'div[role="dialog"][aria-labelledby]'
    ellipsis_button = 'div[aria-haspopup="menu"][aria-expanded="false"][role="button"]'
    action_menu = 'div[role="menu"]'
    status = 'div[role="status"]'
    group_checkbox = 'div[aria-checked="false"][role="checkbox"]'


def list_on_marketplace_group(
    page: Page,
    task: BrowserTaskType,
    settings: RobotSettingsType,
    signals: BrowserWorkerSignals,
    is_publish: bool = True,
):
    signals.info_signal.emit(task, "Action - list_on_marketplace_group")
    progress: List[int] = [0, 0]

    def emit_progress_update(message: str):
        progress[0] += 1
        signals.progress_signal.emit(task, message, [progress[0], progress[1]])

    try:
        page.goto(
            "https://www.facebook.com/groups/475205321869395/buy_sell_discussion",
            timeout=MIN,
        )
        join_group(page=page)
        create_dialog = get_create_dialog(page=page)
        if not create_dialog:
            return "List marketplace (False: get_create_dialog)"
        is_created = handle_create_dialog(page, create_dialog, task.action_payload)
        if not is_created:
            return "List marketplace (False: handle_create_dialog)"
        is_list_more_place = handle_detail_dialog(page)
        sleep(3)
        if not is_list_more_place:
            return "List more place (False: handle_detail_dialog)"
        sleep(3)
        return "True"

    except PlaywrightTimeoutError as e:
        emit_progress_update(
            "ERROR: Timeout while navigating to Marketplace creation page."
        )
        raise Exception("ERR_PROXY_NOT_READY")
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return f"Exception: {str(e)}"
    # ---------------------------------


def join_group(page: Page):
    label_locators = page.locator(Selectors.button_label)
    for i in range(label_locators.count()):
        btn_locator = label_locators.nth(i)
        if (
            btn_locator.get_attribute("aria-label").lower() == "invite"
            and btn_locator.is_visible()
        ):
            return
    for i in range(label_locators.count()):
        btn_locator = label_locators.nth(i)
        if (
            btn_locator.get_attribute("aria-label").lower() == "join group"
            and btn_locator.is_visible()
        ):
            btn_locator.click()
            return


def get_create_dialog(page: Page) -> Union[bool, Locator]:
    # label_locators = page.locator(Selectors.button_label)
    sell_btn_locator: Optional[Locator] = None
    sell_dialog_locator: Optional[Locator] = None
    times = 0
    while not sell_btn_locator and times < 60:
        button_locators = page.locator(Selectors.button_label)
        for i in range(button_locators.count()):
            btn_locator = button_locators.nth(i)
            if (
                btn_locator.get_attribute("aria-label").lower() == "sell something"
                and btn_locator.is_visible()
            ):
                btn_locator.wait_for(state="attached")
                sell_btn_locator = btn_locator
                break
        times += 1
        sleep(1)

    if not sell_btn_locator:
        print("Cannot get click 'Sell something' button.")
        return False

    sell_btn_locator.click()

    times = 0
    while not sell_dialog_locator and times < 60:
        dialog_locators = page.locator(Selectors.dialog)
        for dialog_locator in dialog_locators.all():
            if (
                dialog_locator.get_attribute("aria-label").lower()
                == "create new listing"
            ):
                sell_dialog_locator = dialog_locator
                break
        sleep(1)
        times += 1

    if not sell_dialog_locator:
        print("Cannot get 'Create new listing' dialog.")
        return False
    btn_locators = sell_dialog_locator.locator(Selectors.button_without_label)
    try:
        btn_locators.first.wait_for(timeout=MIN)
    except PlaywrightTimeoutError:
        print("Cannot get 'Item for sell' dialog.")
        return False
    btn_locators.nth(0).click()

    return sell_dialog_locator


def handle_create_dialog(
    page: Page, dialog: Locator, action_payload: SellPayloadType
) -> bool:
    # TODO Click expand button
    try:
        btn_expanded_locator = dialog.locator(Selectors.button_expanded)
        btn_expanded_locator.wait_for()
        btn_expanded_locator.first.click()
        sleep(random.uniform(0.5, 2))
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False
    # TODO Fill "input[type='text']" # title (0), price(1), location(2)
    try:
        input_text_locators = dialog.locator(Selectors.input_location)
        for i in range(input_text_locators.count()):
            input_locator = input_text_locators.nth(i)
            if input_locator.is_visible() and input_locator.is_enabled():
                input_locator.scroll_into_view_if_needed()
                sleep(random.uniform(0.5, 2))
                if i == 0:
                    input_locator.type(action_payload.title)
                elif i == 1:
                    input_locator.type("0")
                elif i == 2:
                    input_locator.clear()
                    sleep(random.uniform(0.5, 2))
                    input_locator.type("Da lat")
                    sleep(random.uniform(0.5, 2))
                    location_box_locator = page.wait_for_selector(
                        Selectors.location_box
                    )
                    location_box_locator.wait_for_selector(Selectors.location_box_item)
                    location_box_item_locators = (
                        location_box_locator.query_selector_all(
                            Selectors.location_box_item
                        )
                    )
                    sleep(random.uniform(0.5, 2))
                    location_box_item_locators[0].click()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False
    # TODO Fill condition
    try:
        btn_locator = dialog.locator(Selectors.button_condition)
        btn_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.5, 2))
        btn_locator.first.click()
        condition_box = page.wait_for_selector(Selectors.condition_box)
        condition_box.wait_for_selector(Selectors.condition_box_item)
        condition_item = condition_box.query_selector_all(Selectors.condition_box_item)
        condition_item[0].scroll_into_view_if_needed()
        sleep(random.uniform(0.5, 2))
        condition_item[0].click()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False
    # TODO Fill description
    try:
        description_locator = dialog.locator(Selectors.input_description)
        description_locator.first.scroll_into_view_if_needed()
        sleep(random.uniform(0.5, 2))
        description_locator.first.type(action_payload.description)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False

    # TODO Fill image
    try:
        parent_div_locator = dialog.locator(
            'xpath=//input[@accept="image/*,image/heif,image/heic"]/parent::*/parent::*'
        )
        btn_locator = parent_div_locator.first.locator(Selectors.button_without_label)
        sleep(random.uniform(0.5, 2))
        with page.expect_file_chooser() as fc_info:
            btn_locator.first.click()
        file_chooser = fc_info.value
        file_chooser.set_files(
            [
                img_path.strip()
                for img_path in action_payload.image_paths
                if os.path.exists(img_path.strip())
            ][:10]
        )
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False

    # TODO Click next btn
    try:
        next_btn_locator: Optional[Locator] = None
        times = 0
        while not next_btn_locator and times < 60:
            btn_locators = dialog.locator(Selectors.button_label)
            for i in range(btn_locators.count()):
                btn_locator = btn_locators.nth(i)
                if (
                    btn_locator.is_visible()
                    and btn_locator.get_attribute("aria-label").lower() == "next"
                ):
                    if not btn_locator.get_attribute("aria-disabled"):
                        next_btn_locator = btn_locator
                        break
            times += 1
            sleep(1)
        if not next_btn_locator:
            print("Cannot get 'Next' button.")
            return False
        next_btn_locator.scroll_into_view_if_needed()
        sleep(random.uniform(0.5, 2))
        next_btn_locator.click()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False

    # TODO Find publish btn
    publish_btn_locator: Optional[Locator] = None
    try:
        times = 0
        while not publish_btn_locator and times < 60:
            btn_locators = dialog.locator(Selectors.button_label)
            for i in range(btn_locators.count()):
                btn_locator = btn_locators.nth(i)
                if (
                    btn_locator.is_visible()
                    and btn_locator.get_attribute("aria-label").lower() == "post"
                ):
                    if not btn_locator.get_attribute("aria-disabled"):
                        publish_btn_locator = btn_locator
                        break
            times += 1
            sleep(1)
        if not publish_btn_locator:
            print("Cannot get 'Post' button.")
            return False
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False

    # TODO Click marketplace btn
    try:
        marketplace_btn_locators = dialog.get_by_role(
            role="button", name="Marketplace", exact=False
        )
        for i in range(marketplace_btn_locators.count()):
            btn_locator = marketplace_btn_locators.nth(i)
            if btn_locator.is_visible():
                btn_locator.scroll_into_view_if_needed()
                sleep(random.uniform(0.5, 2))
                btn_locator.click()
                break
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False

    # TODO Click publish btn
    try:
        sleep(random.uniform(0.5, 2))
        publish_btn_locator.scroll_into_view_if_needed()
        # publish_btn_locator.highlight()
        sleep(random.uniform(0.5, 2))
        publish_btn_locator.click()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False

    return True


def handle_detail_dialog(page: Page) -> bool:
    try:
        dialog_locator = handle_open_list_more_place(page)
        sleep(random.uniform(0.5, 2))
        group_locators = dialog_locator.locator(Selectors.group_checkbox)
        group_num = group_locators.count()
        sleep(random.uniform(0.5, 2))
        close_btn_locator = dialog_locator.get_by_role(
            role="button", name="Close", exact=False
        )
        close_btn_locator.click()
        while group_num > 0:
            new_dialog_locator = handle_open_list_more_place(page)
            new_group_locators = new_dialog_locator.locator(Selectors.group_checkbox)
            for i in range(20 if group_num > 20 else group_num):
                try:
                    if group_num >= 0:
                        current_group_locator = new_group_locators.nth(group_num - 1)
                        current_group_locator.click()
                        sleep(random.uniform(0.1, 0.5))
                        group_num -= 1
                except Exception:
                    continue
            times = 0
            while times < 60:
                button_locators = page.locator(Selectors.button_label)
                is_posted = False
                for i in range(button_locators.count()):
                    button_locator = button_locators.nth(i)
                    try:
                        if button_locator.get_attribute("aria-label").lower() == "post":
                            button_locator.scroll_into_view_if_needed(timeout=1000)
                            button_locator.click(timeout=1000)
                            sleep(1)
                            is_posted = True
                            break
                    except Exception:
                        continue
                if is_posted == True:
                    break
                times += 1
                sleep(1)
        return True
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False


def handle_open_list_more_place(page: Page) -> Optional[Locator]:
    # TODO Get detail dialog
    detail_dialog_locator: Optional[Locator] = None
    try:
        sleep(random.uniform(0.5, 2))
        times = 0
        while not detail_dialog_locator and times < 60:
            dialog_locators = page.locator(Selectors.detail_dialog)
            for i in range(dialog_locators.count()):
                dialog_locator = dialog_locators.nth(i)
                if dialog_locator.is_visible():
                    detail_dialog_locator = dialog_locator
                    break
            if not detail_dialog_locator:
                times += 1
                sleep(1)
        if not detail_dialog_locator:
            print("Cannot get '<User>'s Post' dialog.")
            return False
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False

    # TODO wait ellipsis btn
    try:
        sleep(random.uniform(0.5, 2))
        times = 0
        is_clicked_ellipsis_btn = False
        while not is_clicked_ellipsis_btn and times < 60:
            is_clicked_ellipsis_btn = False
            ellipsis_btn_locators = detail_dialog_locator.locator(
                Selectors.ellipsis_button
            )
            ellipsis_btn_locators.wait_for(timeout=MIN)
            for i in range(ellipsis_btn_locators.count()):
                if ellipsis_btn_locators.nth(i).is_visible():
                    ellipsis_btn_locators.nth(i).click()
                    is_clicked_ellipsis_btn = True
                    break
            times += 1
            sleep(1)
        if not is_clicked_ellipsis_btn:
            return False
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False

    # TODO click to list more place
    try:
        sleep(random.uniform(0.5, 2))
        menu_locator = page.get_by_role(role="menu", name="Feed story", exact=False)
        list_more_place_btn_locator = menu_locator.get_by_role(
            role="menuitem", name="List in More Places", exact=False
        )
        list_more_place_btn_locator.click()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False

    # TODO get list more place dialog
    more_place_dialog_locator: Optional[Locator] = None
    try:
        sleep(random.uniform(0.5, 2))
        times = 0
        while not more_place_dialog_locator and times < 60:
            dialog_locators = page.locator(Selectors.dialog)
            for i in range(dialog_locators.count()):
                dialog_locator = dialog_locators.nth(i)
                aria_label = dialog_locator.get_attribute("aria-label")
                if (
                    dialog_locator.is_visible()
                    and aria_label
                    and aria_label.lower() == "list in more places"
                ):
                    more_place_dialog_locator = dialog_locator
                    break
            if not more_place_dialog_locator:
                times += 1
                sleep(1)
        if not more_place_dialog_locator:
            print("Cannot get 'List in more places' dialog.")
            return False
        return more_place_dialog_locator
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_list = traceback.extract_tb(exc_traceback)
        for tb in reversed(tb_list):
            if os.path.abspath(__file__) == os.path.abspath(tb.filename):
                file_name = tb.filename
                line_number = tb.lineno
                function_name = tb.name
                print(
                    f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
                )
                break
        else:
            # Nếu không tìm thấy, in frame cuối cùng như cũ
            last_call = tb_list[-1]
            file_name = last_call.filename
            line_number = last_call.lineno
            function_name = last_call.name
            print(
                f"[\n\tError: {type(e).__name__}\n\tOccurred in file: {file_name}\n\tIn function: {function_name}\n\tAt line: {line_number}\n\t]"
            )
        return False


# python -m src.robot.actions.fb_list_on_marketplace_group
##

if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    from src.my_types import UserType, SellPayloadType

    user_info = UserType(
        id=0,
        uid="",
        my_id="",
        username="",
        password="",
        two_fa="",
        email="",
        email_password="",
        phone_number="",
        note="",
        type="",
        user_group=0,
        mobile_ua="",
        desktop_ua="",
        status=0,
        created_at="",
        updated_at="",
    )
    action_name = ""
    action_payload = SellPayloadType(
        title="️🏏 CHO THUÊ NHÀ MẶT TIỀN PHƯỜNG 4 ĐÀ LẠT GIÁ ƯU ĐÃI 16.0 TRIỆU/THÁNG",
        description="""
 ️🏀 Cho thuê Nhà mặt tiền Phường 4, Đà Lạt, Lâm Đồng.
️🎧 4.0 tầng.
️🏹 Nội thất cơ bản.
+ nhà ngay mặt tiền đường, thuận tiện di chuyển
+ bancol thông thoáng
🆔: Re.r.67834118
☎ Liên hệ: 0375155525 - Đ. Bình 

------------------------------
🌺Ký gửi mua, bán - cho thuê, thuê bất động sản xin liên hệ 0375155525 - Đ. Bình🌺
------------------------------
[
    PID: <RE.R.67834118>
    updated_at: <2025-09-04 09:02:33.293665>
    published_at: <2025-09-04 19:27:05.551030>
]

        """,
        image_paths=[
            # "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/_.jpg ",
            # "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/RE.R.67834118_1.jpg ",
            # "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/RE.R.67834118_3.jpg ",
            # "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/RE.R.67834118_4.jpg ",
            # "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/RE.R.67834118_5.jpg ",
            # "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/RE.R.67834118_6.jpg ",
            # "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/RE.R.67834118_7.jpg ",
            # "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/RE.R.67834118_8.jpg ",
            # "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/RE.R.67834118_9.jpg ",
            "/Volumes/KINGSTON/Dev/python/my-manager.data/images/RE.R.67834118/RE.R.67834118_10.jpg",
        ],
    )
    settings = RobotSettingsType(
        is_mobile=0,
        headless=False,
        thread_num=1,
        group_num=5,
        delay_num=0,
        group_file_path="",
    )

    task = BrowserTaskType(
        user_info=user_info,
        action_name=action_name,
        action_payload=action_payload,
        is_mobile=False,
        headless=False,
        udd="",
        browser_id="",
    )

    signals = BrowserWorkerSignals()

    context_kwargs = dict(
        user_data_dir="/Volumes/KINGSTON/Dev/python/my-manager.data/user_data_dirs/test_browser",
        # user_agent="",
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            f"--app-name=Chromium - test",
        ],
        ignore_default_args=["--enable-automation"],
    )
    window_width = 960
    window_height = int(window_width * 0.56)
    context_kwargs["device_scale_factor"] = 0.68

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(**context_kwargs)

        page = context.new_page()
        list_on_marketplace_group(
            page=page,
            task=task,
            settings=settings,
            signals=signals,
            is_publish=False,
        )
        page.wait_for_event("close", timeout=0)
