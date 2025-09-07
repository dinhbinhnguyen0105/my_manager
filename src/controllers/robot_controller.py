# src/controllers/robot_controller.py
import os
from typing import List, Dict, Optional, Tuple
from PyQt6.QtCore import pyqtSlot, pyqtSignal

# from src.robot.browser_manager import BrowserManager
from src.robot.browser_manager import BrowserManager
from src.controllers.base_controller import BaseController
from src.services.user_service import UserService
from src.services.setting_service import SettingProxyService, SettingUserDataDirService
from src.services.product_service import (
    MiscProductService,
    RealEstateProductService,
    RealEstateTemplateService,
)
from src.my_types import (
    UserType,
    BrowserTaskType,
    RealEstateProductType,
    MiscProductType,
    SellPayloadType,
    RobotSettingsType,
)
from src.my_constants import RE_TRANSACTION

from src.utils.re_template import replace_template, init_footer_content


class RobotController(BaseController):
    finished_signal = pyqtSignal()

    def __init__(
        self,
        user_service: UserService,
        misc_product_service: MiscProductService,
        re_product_service: RealEstateProductService,
        re_template_service: RealEstateTemplateService,
        setting_proxy_service: SettingProxyService,
        setting_udd_service: SettingUserDataDirService,
        parent=None,
    ):
        super().__init__(service=user_service, parent=parent)
        self._user_service = user_service
        self._misc_product_service = misc_product_service
        self._re_product_service = re_product_service
        self._re_template_service = re_template_service
        self._setting_proxy_service = setting_proxy_service
        self._setting_udd_service = setting_udd_service
        self._current_browser_progress: Optional[BrowserManager] = None

    def init_actions(
        self, list_user_data: List[UserType], action_payloads: List
    ) -> Dict[str, BrowserTaskType]:
        browser_actions = {}
        for user_data in list_user_data:
            user_type = user_data.type.strip().lower()
            browser_actions[user_data.uid] = []
            for action in action_payloads:
                if "pid" in action.keys():
                    pid = action["pid"]
                    action_payload: Optional[SellPayloadType] = None
                    product = None
                    if pid:
                        product_type = pid.split(".")[0]
                        if "re" in product_type.lower():
                            product = self._re_product_service.read_by_pid(pid)
                        elif "misc" in product_type.lower():
                            # TODO get random misc.
                            product = self._misc_product_service.read_by_pid(pid)
                            raise RuntimeError("Invalid logic for misc")
                    if not product:
                        if "re.s" in user_type.lower():
                            product = self._re_product_service.get_random(
                                RE_TRANSACTION["sell"]
                            )
                        elif "re.r" in user_type.lower():
                            product = self._re_product_service.get_random(
                                RE_TRANSACTION["rent"]
                            )
                        elif "misc." in user_type.lower():
                            # TODO get random misc.
                            pass
                            # raise RuntimeError("Invalid logic for misc")
                    if type(product) == RealEstateProductType:
                        temp_title = self._re_template_service.get_random(
                            part="title",
                            transaction_type=product.transaction_type,
                            category=product.category,
                        )
                        temp_desc = self._re_template_service.get_random(
                            part="description",
                            transaction_type=product.transaction_type,
                            category=product.category,
                        )
                        title = replace_template(
                            product_data=product, template=temp_title
                        ).upper()
                        desc = replace_template(
                            product_data=product, template=temp_desc
                        )
                        desc = (
                            title
                            + "\n"
                            + desc
                            # + "\n"
                            # + "Liên hệ ĐT/Zalo: 0375 155 525 ()"
                            # + "\n\n"
                            + init_footer_content(product)
                        )
                        image_paths = self._re_product_service.get_images_by_path(
                            product.image_dir
                        )
                        title = title[:90]
                        action_payload = SellPayloadType(
                            title=title, description=desc, image_paths=image_paths[:9]
                        )

                    elif type(product) == MiscProductType:
                        # TODO template misc
                        continue
                elif "content" in action.keys():
                    action_payload = SellPayloadType(
                        title=action["content"].get("title", ""),
                        description=action["content"].get("description", ""),
                        image_paths=action["content"].get("image_paths", []),
                    )
                # browser_id = str(uuid.uuid4())
                # user_data.my_id
                browser_actions[user_data.uid].append(
                    BrowserTaskType(
                        user_info=user_data,
                        action_name=action.get("action_name", None),
                        action_payload=action_payload,
                        is_mobile=False,
                        headless=False,
                        udd=os.path.join(
                            self._setting_udd_service.get_selected(),
                            str(user_data.my_id),
                        ),
                        browser_id=user_data.my_id,
                    )
                )
        return browser_actions

    def init_browser_tasks(
        self, browser_actions: Dict[str, BrowserTaskType]
    ) -> List[BrowserTaskType]:
        browser_tasks: List[BrowserTaskType] = []
        sorted_uid_s = sorted(browser_actions.keys())
        uid_num = len(sorted_uid_s)
        max_len = 0
        if browser_actions:
            max_len = max(len(action) for action in browser_actions.values())
        last_uid_contributed: Optional[str] = None
        for i in range(max_len):
            current_column_items_with_uid_s: List[
                Tuple[Optional[BrowserTaskType], str]
            ] = []
            for uid in sorted_uid_s:
                if i < len(browser_actions[uid]):
                    current_column_items_with_uid_s.append(
                        (browser_actions[uid][i], uid)
                    )
                else:
                    current_column_items_with_uid_s.append((None, uid))
            for task_obj, current_uid in current_column_items_with_uid_s:
                if task_obj is not None:
                    if task_obj.action_name == "share_latest_product":
                        task_obj.is_mobile = True
                    if last_uid_contributed is not None:
                        index_of_last_uid = sorted_uid_s.index(last_uid_contributed)
                        index_of_current_uid = sorted_uid_s.index(current_uid)
                        has_gap_of_skipped_uid_s = False
                        check_index = (index_of_last_uid + 1) % uid_num
                        while check_index != index_of_current_uid:
                            if current_column_items_with_uid_s[check_index][0] is None:
                                has_gap_of_skipped_uid_s = True
                                break
                            check_index = (check_index + 1) % uid_num
                        if has_gap_of_skipped_uid_s:
                            # browser_tasks.append(None)
                            pass
                            # continue
                    browser_tasks.append(task_obj)
                    last_uid_contributed = current_uid
        return browser_tasks

    def handle_run_bot(
        self,
        browser_tasks: List[BrowserTaskType],
        settings: RobotSettingsType,
    ):
        proxy_data = self._setting_proxy_service.read_all()
        raw_proxies = [raw_proxy.value for raw_proxy in proxy_data]

        if (
            self._current_browser_progress
            and self._current_browser_progress.is_all_task_finished()
        ):
            print(
                f"[{self.__class__.__name__}.handle_run_bot] Bot is already running. Adding browser task to the queue."
            )
            self._current_browser_progress.add_browsers(
                list_browsers=browser_tasks, list_raw_proxies=raw_proxies
            )
        else:
            print(f"[{self.__class__.__name__}.handle_run_bot] Starting new bot tasks.")
            self._current_browser_progress = BrowserManager(self)
            self._current_browser_progress.set_settings(settings=settings)
            self._current_browser_progress.manager_signals.info_signal.connect(
                self.controller_signals.info_signal
            )
            self._current_browser_progress.manager_signals.error_signal.connect(
                self.controller_signals.error_signal
            )
            self._current_browser_progress.manager_signals.warning_signal.connect(
                self.controller_signals.warning_signal
            )
            self._current_browser_progress.manager_signals.failed_signal.connect(
                self.controller_signals.failed_signal
            )
            self._current_browser_progress.manager_signals.task_succeed_signal.connect(
                self.controller_signals.task_succeed_signal
            )
            self._current_browser_progress.manager_signals.finished_signal.connect(
                self.controller_signals.finished_signal
            )
            self._current_browser_progress.manager_signals.progress_signal.connect(
                self.controller_signals.progress_signal
            )
            self._current_browser_progress.add_browsers(
                list_browsers=browser_tasks, list_raw_proxies=raw_proxies
            )
