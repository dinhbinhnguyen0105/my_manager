# src/views/user/page_user.py
from typing import Optional
from PyQt6.QtWidgets import QWidget, QMenu, QMessageBox
from PyQt6.QtCore import (
    Qt,
    QPoint,
    pyqtSlot,
)
from PyQt6.QtGui import QAction, QShortcut, QKeySequence

from src.my_types import UserType
from src.controllers.user_controller import UserController
from src.controllers.setting_controller import (
    SettingUserDataDirController,
    SettingProxyController,
)
from src.ui.page_user_ui import Ui_PageUser
from src.views.user.dialog_create_user import DialogCreateUser
from src.views.user.dialog_update_user import DialogUpdateUser
from src.views.utils.multi_field_model import MultiFieldFilterProxyModel
from src.views.utils.file_dialogs import dialog_open_file, dialog_save_file


class UserPage(QWidget, Ui_PageUser):
    def __init__(
        self,
        user_controller: UserController,
        setting_udd_controller: SettingUserDataDirController,
        setting_proxy_controller: SettingProxyController,
        parent=None,
    ):
        super(UserPage, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("User")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._user_controller = user_controller
        self._setting_udd_controller = setting_udd_controller
        self._setting_proxy_controller = setting_proxy_controller
        self.base_user_model = user_controller.service.model
        self.proxy_model = MultiFieldFilterProxyModel()
        self.proxy_model.setSourceModel(self.base_user_model)

        self.setup_ui()
        self.setup_events()

    def setup_ui(self):
        self.set_user_table()

    def setup_events(self):
        self.set_filters()
        self.action_create_btn.clicked.connect(self.on_create_user)
        shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut.activated.connect(self.on_create_user)
        self.action_import_btn.clicked.connect(self.on_import_clicked)
        self.action_export_btn.clicked.connect(self.on_export_clicked)

    def set_user_table(self):
        self.users_table.setModel(self.proxy_model)
        self.users_table.setSortingEnabled(True)
        self.users_table.setSelectionBehavior(
            self.users_table.SelectionBehavior.SelectRows
        )
        self.users_table.setEditTriggers(self.users_table.EditTrigger.NoEditTriggers)
        for i in range(self.base_user_model.columnCount()):
            column_name = self.base_user_model.headerData(
                i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
            )
            if column_name in [
                "id",
                "status",
                "mobile_ua",
                "desktop_ua",
                "my_id",
            ]:
                self.users_table.setColumnHidden(i, True)
        self.users_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.users_table.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos: QPoint):
        proxy_index = self.users_table.indexAt(pos)
        if not proxy_index.isValid():
            return

        # Chuyển sang index của source model
        source_index = self.proxy_model.mapToSource(proxy_index)
        source_model = self.proxy_model.sourceModel()

        # Tìm cột status
        status_col = (
            source_model.fieldIndex("status")
            if hasattr(source_model, "fieldIndex")
            else 0
        )
        status_index = source_model.index(source_index.row(), status_col)
        status_value: int = source_model.data(status_index, Qt.ItemDataRole.DisplayRole)

        id_col = (
            source_model.fieldIndex("id") if hasattr(source_model, "fieldIndex") else 0
        )
        id_index = source_model.index(source_index.row(), id_col)
        id_value = source_model.data(id_index, Qt.ItemDataRole.DisplayRole)

        global_pos = self.users_table.mapToGlobal(pos)
        menu = QMenu(self.users_table)

        set_status_action: Optional[QAction] = None
        if status_value == 1:
            set_status_action = QAction("Change to dead", self)
            set_status_action.triggered.connect(
                lambda _, record_id=id_value, current_status=status_value: self.handle_change_status(
                    record_id,
                    current_status,
                )
            )
        else:
            set_status_action = QAction("Change to live", self)
            set_status_action.triggered.connect(
                lambda _, record_id=id_value, current_status=status_value: self.handle_change_status(
                    record_id,
                    current_status,
                )
            )

        launch_as_desktop_action = QAction("Launch as desktop", self)
        launch_as_desktop_action.triggered.connect(
            lambda: self.handle_launch_browser(is_mobile=False)
        )
        launch_as_mobile_action = QAction("Launch as mobile", self)
        launch_as_mobile_action.triggered.connect(
            lambda: self.handle_launch_browser(is_mobile=True)
        )
        check_action = QAction("Check live", self)
        check_action.triggered.connect(self.on_check_live)
        update_action = QAction("Update", self)
        update_action.triggered.connect(
            lambda _, record_id=id_value: self.on_update_product(record_id)
        )
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(
            lambda _, record_id=id_value: self.handle_delete_product(record_id)
        )

        menu.addAction(launch_as_desktop_action)
        menu.addAction(launch_as_mobile_action)
        menu.addAction(check_action)
        if set_status_action:
            menu.addAction(set_status_action)
        menu.addAction(update_action)
        menu.addAction(delete_action)
        menu.popup(global_pos)

    def set_filters(self):
        filter_widgets = [
            (self.uid_input, self.base_user_model.fieldIndex("uid")),
            (self.note_input, self.base_user_model.fieldIndex("note")),
            (self.type_input, self.base_user_model.fieldIndex("type")),
            (self.email_input, self.base_user_model.fieldIndex("email")),
            (
                self.email_password_input,
                self.base_user_model.fieldIndex("email_password"),
            ),
            (self.group_input, self.base_user_model.fieldIndex("user_group")),
            (self.two_fa_input, self.base_user_model.fieldIndex("two_fa")),
            (self.username_input, self.base_user_model.fieldIndex("username")),
            (self.password_input, self.base_user_model.fieldIndex("password")),
            (self.phone_number_input, self.base_user_model.fieldIndex("phone_number")),
        ]

        for widget, column in filter_widgets:
            widget.textChanged.connect(
                lambda text, col=column: self.proxy_model.set_filter(col, text)
            )

    def get_selected_ids(self):
        selected_indexes = self.users_table.selectionModel().selectedRows()
        ids = []
        for proxy_index in selected_indexes:
            # Chuyển sang index của source model
            source_index = self.proxy_model.mapToSource(proxy_index)
            source_model = self.proxy_model.sourceModel()
            # Tìm cột id
            id_col = (
                source_model.fieldIndex("id")
                if hasattr(source_model, "fieldIndex")
                else 0
            )
            id_index = source_model.index(source_index.row(), id_col)
            id_value = source_model.data(id_index, Qt.ItemDataRole.DisplayRole)
            ids.append(id_value)
        return sorted(ids)

    @pyqtSlot()
    def on_create_user(self):
        current_time = self._user_controller.handle_new_time()
        self.create_user_dialog = DialogCreateUser(
            {
                "password": self._user_controller.handle_new_password(),
                "note": self._user_controller.handle_init_note(),
                "created_at": current_time,
                "updated_at": current_time,
                "user_group": "-1",
                "mobile_ua": self._user_controller.handle_new_mobile_ua(),
                "desktop_ua": self._user_controller.handle_new_desktop_ua(),
            }
        )
        self.create_user_dialog.user_data_signal.connect(self.handle_create_user)
        self.create_user_dialog.show()

    @pyqtSlot(UserType)
    def handle_create_user(self, user_data: UserType):
        self._user_controller.create_user(user_data)

    @pyqtSlot(int, int)
    def handle_change_status(self, record_id: int, current_status: int):
        self._user_controller.update_status(
            record_id=record_id, current_status=current_status
        )

    @pyqtSlot(int)
    def on_update_product(self, record_id: int):
        user_data = self._user_controller.read_user(record_id)
        self.update_user_dialog = DialogUpdateUser(user_data)
        self.update_user_dialog.user_data_signal.connect(self.handle_update_user)
        self.update_user_dialog.new_mobile_ua_signal.connect(self.handle_new_mobile_ua)
        self.update_user_dialog.new_desktop_ua_signal.connect(
            self.handle_new_desktop_ua
        )
        self.update_user_dialog.show()

    @pyqtSlot(int)
    def handle_delete_product(self, record_id: int):
        udd_container = self._setting_udd_controller.get_selected_user_data_dir()
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this user?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._user_controller.delete_user(
                udd_container=udd_container, record_id=record_id
            )

    @pyqtSlot(UserType)
    def handle_update_user(self, user_data: UserType):
        self._user_controller.update_user(user_data.id, user_data=user_data)

    @pyqtSlot()
    def handle_new_mobile_ua(self):
        if hasattr(self, "update_user_dialog"):
            self.update_user_dialog.mobile_ua_input.setText(
                self._user_controller.handle_new_mobile_ua()
            )

    @pyqtSlot()
    def handle_new_desktop_ua(self):
        if hasattr(self, "update_user_dialog"):
            self.update_user_dialog.desktop_ua_input.setText(
                self._user_controller.handle_new_desktop_ua()
            )

    @pyqtSlot()
    def on_check_live(self):
        selected_ids = self.get_selected_ids()
        self._user_controller.handle_check_users(selected_ids=selected_ids)

    @pyqtSlot(bool)
    def handle_launch_browser(self, is_mobile):
        record_ids = self.get_selected_ids()
        udd_container = self._setting_udd_controller.get_selected_user_data_dir()
        proxies_data = self._setting_proxy_controller.read_all_proxies()
        raw_proxies = [proxy_data.value for proxy_data in proxies_data]
        self._user_controller.handle_launch_browser(
            record_ids=record_ids,
            udd_container=udd_container,
            raw_proxies=raw_proxies,
            is_mobile=is_mobile,
        )

    @pyqtSlot()
    def on_export_clicked(self):
        file_path = dialog_save_file(self)
        if not file_path:
            return
        is_exported = self._user_controller.export_to_file(file_path=file_path)
        if is_exported:
            QMessageBox.about(self, "Exported file", f"Export to {file_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to export data")

    @pyqtSlot()
    def on_import_clicked(self):
        file_path = dialog_open_file(self)
        if not file_path:
            return
        is_imported = self._user_controller.import_products(file_path)
        if is_imported:
            QMessageBox.about(self, "Imported file", f"Import to {file_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to import data")
