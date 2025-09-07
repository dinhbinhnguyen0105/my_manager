# src/views/robot/robot_page.py
from typing import List, Optional, Dict
from PyQt6.QtWidgets import QWidget, QLineEdit, QCompleter, QTreeWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, pyqtSlot, QStringListModel
from PyQt6.QtGui import QShortcut, QKeySequence

from src.controllers.robot_controller import RobotController

from src.views.utils.multi_field_model import MultiFieldFilterProxyModel
from src.views.robot.action_payload import ActionPayload
from src.views.robot.dialog_run_bot import DialogRobotRun
from src.ui.page_robot_ui import Ui_PageRobot

from src.my_types import UserType, RobotSettingsType


class RobotPage(QWidget, Ui_PageRobot):
    def __init__(
        self,
        robot_controller: RobotController,
        parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("User")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._robot_controller = robot_controller

        self.base_user_model = robot_controller._user_service.model
        self.proxy_model = MultiFieldFilterProxyModel()
        self.proxy_model.setSourceModel(self.base_user_model)

        self.browser_actions: Dict = {}

        self.setup_ui()
        self.setup_events()

    def setup_ui(self):
        self.set_user_table()
        self.set_action_tree()
        self.actions_container.setMaximumWidth(480)

    def setup_events(self):
        self.set_filters()
        self.action_add_btn.clicked.connect(self.on_add_action_clicked)
        self.action_save_btn.clicked.connect(self.on_save_action_clicked)
        self.action_run_btn.clicked.connect(self.on_run_action_clicked)
        shortcut_new_action = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut_new_action.activated.connect(self.on_add_action_clicked)
        shortcut_save_action = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save_action.activated.connect(self.on_save_action_clicked)
        shortcut_run_action = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut_run_action.activated.connect(self.on_run_action_clicked)

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
            if column_name not in [
                "uid",
                "username",
                "note",
                "type",
                "user_group",
                "created_at",
                # "my_id",
            ]:
                self.users_table.setColumnHidden(i, True)

    def get_selected_ids(self):
        selected_indexes = self.users_table.selectionModel().selectedRows()
        ids = []
        for proxy_index in selected_indexes:
            source_index = self.proxy_model.mapToSource(proxy_index)
            source_model = self.proxy_model.sourceModel()
            id_col = (
                source_model.fieldIndex("id")
                if hasattr(source_model, "fieldIndex")
                else 0
            )
            id_index = source_model.index(source_index.row(), id_col)
            id_value = source_model.data(id_index, Qt.ItemDataRole.DisplayRole)
            ids.append(id_value)
        return sorted(ids)

    def get_selected_users_data(self) -> List[UserType]:
        """
        Retrieves complete UserType data for all selected rows in the users_table.

        Returns:
            List[UserType]: A list of UserType objects representing the selected users.
                            Returns an empty list if no rows are selected or data is unavailable.
        """
        selected_users_data: List[UserType] = []
        selected_proxy_indexes = self.users_table.selectionModel().selectedRows()

        source_model = self.proxy_model.sourceModel()
        if not hasattr(source_model, "record"):
            print(
                "Error: Source model does not support fetching full records. Cannot retrieve UserType data."
            )
            return []

        for proxy_index in selected_proxy_indexes:
            source_index = self.proxy_model.mapToSource(proxy_index)
            row = source_index.row()
            record = source_model.record(row)

            user_data_dict = {}
            for field_info in UserType.__dataclass_fields__.values():
                field_name = field_info.name
                if record.contains(field_name):
                    value = record.value(field_name)
                    if field_info.type == Optional[int] and isinstance(value, str):
                        try:
                            user_data_dict[field_name] = int(value) if value else None
                        except ValueError:
                            user_data_dict[field_name] = None
                    elif field_info.type == Optional[float] and isinstance(value, str):
                        try:
                            user_data_dict[field_name] = float(value) if value else None
                        except ValueError:
                            user_data_dict[field_name] = None
                    else:
                        user_data_dict[field_name] = value
            try:
                user_type_instance = UserType(**user_data_dict)
                selected_users_data.append(user_type_instance)
            except TypeError as e:
                print(f"Error creating UserType instance for row {row}: {e}")
                print(f"Data tried to assign: {user_data_dict}")

        return selected_users_data

    def set_action_tree(self):
        self.actions_tree.setMaximumWidth(300)
        pass

    def set_pid_completer(self, line_edit: QLineEdit, parent: QWidget):
        suggestions = self._robot_controller._re_product_service.get_all_pid()

        completer_model = QStringListModel()
        completer_model.setStringList(suggestions)
        completer = QCompleter(parent)
        completer.setModel(completer_model)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.InlineCompletion)
        line_edit.setCompleter(completer)

    def fill_actions_tree(self):
        self.actions_tree.clear()
        for uid, actions in self.browser_actions.items():
            if not actions:
                continue
            user_info: UserType = actions[0].user_info
            user_item = QTreeWidgetItem([f"{user_info.username} | {user_info.uid}"])
            for action in actions:
                action_name = (
                    action.action_name
                    if hasattr(action, "action_name")
                    else str(action.get("action_name", ""))
                )
                action_item = QTreeWidgetItem([str(action_name)])
                user_item.addChild(action_item)
            self.actions_tree.addTopLevelItem(user_item)
        self.actions_tree.expandAll()

    def set_filters(self):
        filter_widgets = [
            (self.note_input, self.base_user_model.fieldIndex("note")),
            (self.type_input, self.base_user_model.fieldIndex("type")),
            (self.group_input, self.base_user_model.fieldIndex("user_group")),
            (self.username_input, self.base_user_model.fieldIndex("username")),
        ]

        for widget, column in filter_widgets:
            widget.textChanged.connect(
                lambda text, col=column: self.proxy_model.set_filter(col, text)
            )

    @pyqtSlot()
    def on_add_action_clicked(self):
        self.action_payload_layout.addWidget(ActionPayload(self.set_pid_completer))

    @pyqtSlot()
    def on_save_action_clicked(self):
        selected_users = self.get_selected_users_data()
        if not selected_users:
            return
        action_widgets = self.findChildren(ActionPayload)
        if not action_widgets:
            for selected_user in selected_users:
                if selected_user.uid in self.browser_actions.keys():
                    del self.browser_actions[selected_user.uid]
            self.fill_actions_tree()
            return
        action_payloads = [w.get_values() for w in action_widgets]

        new_browser_actions = self._robot_controller.init_actions(
            list_user_data=selected_users,
            action_payloads=action_payloads,
        )

        for uid, browser_action in new_browser_actions.items():
            self.browser_actions[uid] = browser_action

        self.fill_actions_tree()

    @pyqtSlot()
    def on_run_action_clicked(self):
        self.robot_run_dialog = DialogRobotRun(self)
        self.robot_run_dialog.setting_data_signal.connect(self.handle_run_robot)
        self.robot_run_dialog.show()

    @pyqtSlot(RobotSettingsType)
    def handle_run_robot(self, robot_settings: RobotSettingsType):
        browser_tasks = self._robot_controller.init_browser_tasks(self.browser_actions)
        for browser_task in browser_tasks:
            browser_task.is_mobile = robot_settings.is_mobile
            browser_task.headless = robot_settings.headless

        self._robot_controller.handle_run_bot(
            browser_tasks=browser_tasks,
            settings=robot_settings,
        )
