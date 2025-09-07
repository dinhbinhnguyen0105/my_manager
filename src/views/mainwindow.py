# src/views/mainwindow.py
from typing import List
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QMainWindow, QLabel, QMessageBox, QProgressBar
from PyQt6.QtCore import QTimer

from src.my_types import (
    SettingProxyType,
    SettingUserDataDirType,
    RealEstateTemplateType,
)

from src.controllers.user_controller import UserController, UserListedProductController
from src.controllers.product_controller import (
    RealEstateProductController,
    RealEstateTemplateController,
    MiscProductController,
)
from src.controllers.setting_controller import (
    SettingProxyController,
    SettingUserDataDirController,
)
from src.controllers.robot_controller import RobotController

from src.views.product.real_estate_product_page import RealEstateProductPage
from src.views.user.user_page import UserPage
from src.views.robot.robot_page import RobotPage
from src.views.settings.dialog_settings import DialogSettings
from src.ui.mainwindow_ui import Ui_MainWindow
from src.views.utils.file_dialogs import dialog_open_file, dialog_save_file


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(
        self,
        user_controller: UserController,
        robot_controller: RobotController,
        user_listed_product_controller: UserListedProductController,
        real_estate_product_controller: RealEstateProductController,
        real_estate_template_controller: RealEstateTemplateController,
        misc_product_controller: MiscProductController,
        setting_proxy_controller: SettingProxyController,
        setting_user_data_dir_controller: SettingUserDataDirController,
        parent=None,
    ):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("My manager")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMinimumSize(960, 540)

        self._user_controller = user_controller
        self._user_listed_product_controller = user_listed_product_controller
        self._real_estate_product_controller = real_estate_product_controller
        self._real_estate_template_controller = real_estate_template_controller
        self._misc_product_controller = misc_product_controller
        self._setting_proxy_controller = setting_proxy_controller
        self._setting_user_data_dir_controller = setting_user_data_dir_controller
        self._robot_controller = robot_controller

        self.real_estate_product_page = RealEstateProductPage(
            product_controller=self._real_estate_product_controller,
            template_controller=self._real_estate_template_controller,
            setting_controller=self._setting_user_data_dir_controller,
            parent=self,
        )
        self.user_page = UserPage(
            user_controller=self._user_controller,
            setting_udd_controller=self._setting_user_data_dir_controller,
            setting_proxy_controller=self._setting_proxy_controller,
            parent=self,
        )
        self.robot_page = RobotPage(
            robot_controller=self._robot_controller,
            parent=self,
        )

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.setup_ui()
        self.setup_events()

        self.set_status_bar_message()

    def set_status_bar_message(self):
        self.status_bar.showMessage("My manager application is running ...", 2000)
        for controller in [
            self._user_controller,
            self._user_listed_product_controller,
            self._real_estate_product_controller,
            self._real_estate_template_controller,
            self._misc_product_controller,
            self._setting_proxy_controller,
            self._setting_user_data_dir_controller,
            self._robot_controller,
        ]:
            controller.controller_signals.info_signal.connect(
                lambda msg: self.set_status_bar(message=msg, log=False)
            )
            controller.controller_signals.error_signal.connect(
                lambda msg: self.set_status_bar(message=msg, log=True)
            )
            controller.controller_signals.warning_signal.connect(
                lambda msg: self.set_status_bar(message=msg, log=False)
            )
            controller.controller_signals.failed_signal.connect(
                lambda msg: self.set_status_bar(message=msg, log=True)
            )
            controller.controller_signals.task_succeed_signal.connect(
                lambda msg: self.set_status_bar(message=msg, log=False)
            )
            controller.controller_signals.finished_signal.connect(
                lambda msg: self.set_status_bar(message=msg, log=False)
            )
            controller.controller_signals.data_changed_signal.connect(
                lambda model = controller.service.model : self.reload_data(model)
            )
            controller.controller_signals.progress_signal.connect(self.set_progress)

    def setup_ui(self):
        self.content_container.addWidget(self.real_estate_product_page)
        self.content_container.addWidget(self.user_page)
        self.content_container.addWidget(self.robot_page)

        self.content_container.setCurrentWidget(self.user_page)

    def setup_events(self):
        self.sidebar_re_btn.clicked.connect(
            lambda: self.on_sidebar_btn_clicked("real_estate_product")
        )
        self.sidebar_misc_btn.clicked.connect(
            lambda: self.on_sidebar_btn_clicked("misc_product")
        )
        self.sidebar_user_btn.clicked.connect(
            lambda: self.on_sidebar_btn_clicked("user")
        )
        self.sidebar_robot_btn.clicked.connect(
            lambda: self.on_sidebar_btn_clicked("robot")
        )
        self.sidebar_robot_settings.clicked.connect(self.on_robot_settings_clicked)

    @pyqtSlot(str)
    def on_sidebar_btn_clicked(self, page_name: str):
        if page_name == "real_estate_product":
            self.content_container.setCurrentWidget(self.real_estate_product_page)
        # elif page_name == "misc_product":
        #     self.content_container.setCurrentWidget()
        elif page_name == "user":
            self.content_container.setCurrentWidget(self.user_page)
        elif page_name == "robot":
            self.content_container.setCurrentWidget(self.robot_page)

    @pyqtSlot()
    def on_robot_settings_clicked(self):
        dialog_settings = DialogSettings(
            proxy_setting_model=self._setting_proxy_controller.service.model,
            udd_setting_model=self._setting_user_data_dir_controller.service.model,
            re_template_model=self._real_estate_template_controller.service.model,
            parent=self,
        )
        dialog_settings.new_proxy_data_signal.connect(self.handle_create_new_proxy)
        dialog_settings.new_udd_data_signal.connect(
            self.handle_create_new_user_data_dir
        )
        dialog_settings.new_re_template_signal.connect(
            self.handle_create_new_re_template
        )
        dialog_settings.delete_proxy_signal.connect(self.handle_delete_proxy)
        dialog_settings.delete_udd_signal.connect(self.handle_delete_udd)
        dialog_settings.delete_re_template_signal.connect(
            self.handle_delete_re_template
        )
        dialog_settings.set_udd_selected_signal.connect(self.handle_set_udd_selected)
        dialog_settings.re_template_set_default_signal.connect(
            self.handle_set_to_default
        )
        dialog_settings.export_signal.connect(self.on_export_clicked)
        dialog_settings.import_signal.connect(self.on_import_clicked)
        dialog_settings.exec()

    @pyqtSlot(SettingProxyType)
    def handle_create_new_proxy(self, proxy_data: SettingProxyType):
        self._setting_proxy_controller.create_proxy(proxy_data)

    @pyqtSlot(SettingUserDataDirType)
    def handle_create_new_user_data_dir(self, udd_data: SettingUserDataDirType):
        self._setting_user_data_dir_controller.create_user_data_dir(udd_data)

    @pyqtSlot(RealEstateTemplateType)
    def handle_create_new_re_template(self, re_template_data: RealEstateTemplateType):
        self._real_estate_template_controller.create_template(re_template_data)

    @pyqtSlot(int)
    def handle_delete_proxy(self, record_id: int):
        self._setting_proxy_controller.delete_proxy(record_id)

    @pyqtSlot(int)
    def handle_delete_udd(self, record_id: int):
        self._setting_user_data_dir_controller.delete_user_data_dir(record_id)

    @pyqtSlot(int)
    def handle_delete_re_template(self, record_id: int):
        self._real_estate_template_controller.delete_template(record_id=record_id)

    @pyqtSlot(int)
    def handle_set_udd_selected(self, record_id: int):
        self._setting_user_data_dir_controller.set_selected_user_data_dir(
            record_id=record_id
        )

    @pyqtSlot(int)
    def handle_set_to_default(self, record_id: int):
        self._real_estate_template_controller.set_default_template(record_id)

    @pyqtSlot(str)
    def on_export_clicked(self, setting_option: str):
        file_path = dialog_save_file(self)
        if not file_path:
            return
        current_controller = None
        if "udd" == setting_option:
            current_controller = self._setting_user_data_dir_controller
        elif "proxy" == setting_option:
            current_controller = self._setting_proxy_controller
        elif "re_template" == setting_option:
            current_controller = self._real_estate_template_controller
        else:
            return
        is_exported = current_controller.export_to_file(file_path=file_path)
        if is_exported:
            QMessageBox.about(self, "Exported file", f"Export to {file_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to export data")

    @pyqtSlot(str)
    def on_import_clicked(self, setting_option: str):
        file_path = dialog_open_file(self)
        if not file_path:
            return
        current_controller = None
        if "udd" == setting_option:
            current_controller = self._setting_user_data_dir_controller
        elif "proxy" == setting_option:
            current_controller = self._setting_proxy_controller
        elif "re_template" == setting_option:
            current_controller = self._real_estate_template_controller
        else:
            return
        is_imported = current_controller.import_products(file_path)
        if is_imported:
            QMessageBox.about(self, "Imported file", f"Import to {file_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to import data")

    @pyqtSlot(str)
    def set_status_bar(self, message: str, log=False):
        if log:
            print(message)
        self.status_bar.showMessage(message, 2_500)

    @pyqtSlot(str, list)
    def set_progress(self, msg: str, progress: List):
        self.set_status_bar(message=msg)
        if not hasattr(self, "_progress_bar"):
            self._progress_bar = QProgressBar()
            self._progress_bar.setMaximumWidth(200)
            self.status_bar.addPermanentWidget(self._progress_bar)
        current, total = progress
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        if current >= total or total == 0:
            self._progress_bar.hide()
        else:
            self._progress_bar.show()

    @pyqtSlot(object)
    def reload_data(self, model:object):
        while model.canFetchMore():
            model.fetchMore()