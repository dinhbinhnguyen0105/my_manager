# src/views/settings/dialog_settings.py
from typing import Union
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal, QPoint
from PyQt6.QtWidgets import QDialog, QMenu
from PyQt6.QtGui import QAction

from src.models.setting_model import SettingProxyModel, SettingUserDataDirModel
from src.models.product_model import RealEstateTemplateModel

from src.ui.dialog_settings_ui import Ui_Dialog_Settings
from src.my_types import (
    SettingProxyType,
    SettingUserDataDirType,
    RealEstateTemplateType,
)
from src.my_constants import RE_CATEGORY, RE_TRANSACTION


class DialogSettings(QDialog, Ui_Dialog_Settings):
    new_proxy_data_signal = pyqtSignal(SettingProxyType)
    new_udd_data_signal = pyqtSignal(SettingUserDataDirType)
    new_re_template_signal = pyqtSignal(RealEstateTemplateType)
    delete_proxy_signal = pyqtSignal(int)
    delete_udd_signal = pyqtSignal(int)
    delete_re_template_signal = pyqtSignal(int)
    set_udd_selected_signal = pyqtSignal(int)
    re_template_set_default_signal = pyqtSignal(int)
    import_signal = pyqtSignal(str)
    export_signal = pyqtSignal(str)

    def __init__(
        self,
        proxy_setting_model: SettingProxyModel,
        udd_setting_model: SettingUserDataDirModel,
        re_template_model: RealEstateTemplateModel,
        parent=None,
    ):
        super(DialogSettings, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Real estate product")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setModal(False)
        self._proxy_setting_model = proxy_setting_model
        self._udd_setting_model = udd_setting_model
        self._re_template_model = re_template_model

        self.current_setting_option = None

        self.udd_container.setHidden(True)
        self.proxy_container.setHidden(True)
        self.re_template_container.setHidden(True)
        self.setup_events()
        self.setup_ui()

    def setup_ui(self):
        self.set_table_ui()
        self.set_re_template_comboboxes()

    def setup_events(self):
        self.udd_radio.clicked.connect(lambda: self.on_setting_option_clicked("udd"))
        self.proxy_radio.clicked.connect(
            lambda: self.on_setting_option_clicked("proxy")
        )
        self.re_template_radio.clicked.connect(
            lambda: self.on_setting_option_clicked("re_template")
        )
        self.create_new_btn.clicked.connect(self.on_save_clicked)
        self.action_import_btn.clicked.connect(
            lambda: self.import_signal.emit(self.current_setting_option)
        )
        self.action_export_btn.clicked.connect(
            lambda: self.export_signal.emit(self.current_setting_option)
        )

    def set_table_ui(self):
        self.tableView.setSortingEnabled(True)
        self.tableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableView.setSelectionBehavior(self.tableView.SelectionBehavior.SelectRows)
        self.tableView.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos: QPoint):
        global_pos = self.tableView.mapToGlobal(pos)

        menu = QMenu(self.tableView)
        if type(self.tableView.model()).__name__ == "SettingUserDataDirModel":
            selected_action = QAction("Select", self)
            selected_action.triggered.connect(self.on_set_selected)
            menu.addAction(selected_action)
        elif type(self.tableView.model()).__name__ == "RealEstateTemplateModel":
            set_default_action = QAction("Set to default", self)
            set_default_action.triggered.connect(self._on_set_to_default)
            menu.addAction(set_default_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.on_deleted_clicked)
        menu.addAction(delete_action)

        menu.popup(global_pos)

    def set_re_template_comboboxes(self):
        for _key in RE_TRANSACTION:
            self.transaction_type_combobox.addItem(
                RE_TRANSACTION[_key].capitalize(), _key
            )
        for _key in RE_CATEGORY:
            self.categories_combobox.addItem(RE_CATEGORY[_key].capitalize(), _key)

    def get_selected_ids(self):
        selected_indexes = self.tableView.selectionModel().selectedRows()
        model = self.tableView.model()
        id_col = model.fieldIndex("id") if hasattr(model, "fieldIndex") else 0
        ids = []
        for index in selected_indexes:
            id_index = model.index(index.row(), id_col)
            ids.append(model.data(id_index))
        return ids

    @pyqtSlot(str)
    def on_setting_option_clicked(self, setting_option_name: str):
        self.current_setting_option = setting_option_name
        self.udd_container.setVisible("udd" == setting_option_name)
        self.proxy_container.setVisible("proxy" == setting_option_name)
        self.re_template_container.setVisible("re_template" == setting_option_name)

        if "udd" == setting_option_name:
            self.tableView.setModel(self._udd_setting_model)
        if "proxy" == setting_option_name:
            self.tableView.setModel(self._proxy_setting_model)
        if "re_template" == setting_option_name:
            self.tableView.setModel(self._re_template_model)
        self.tableView.hideColumn(0)

    @pyqtSlot()
    def on_save_clicked(self):
        if "udd" == self.current_setting_option:
            self.new_udd_data_signal.emit(
                SettingUserDataDirType(
                    id=None,
                    value=self.udd_input.text(),
                    is_selected=int(self.udd_is_selected_checkbox.isChecked()),
                    created_at=None,
                    updated_at=None,
                )
            )
            self.udd_input.clear()
        elif "proxy" == self.current_setting_option:
            self.new_proxy_data_signal.emit(
                SettingProxyType(
                    id=None,
                    value=self.proxy_input.text(),
                    created_at=None,
                    updated_at=None,
                )
            )
            self.proxy_input.clear()
        elif "re_template" == self.current_setting_option:
            part = None
            if self.title_radio.isChecked():
                part = "title"
            elif self.description_radio.isChecked():
                part = "description"
            else:
                return
            self.new_re_template_signal.emit(
                RealEstateTemplateType(
                    id=None,
                    transaction_type=self.transaction_type_combobox.currentText().lower(),
                    category=self.categories_combobox.currentText().lower(),
                    part=part,
                    is_default=0,
                    value=self.value_plain_text.toPlainText(),
                    created_at=None,
                    updated_at=None,
                )
            )
            self.value_plain_text.clear()
        else:
            return

    @pyqtSlot()
    def on_deleted_clicked(self):
        record_id = self.get_selected_ids()[0]

        if "udd" == self.current_setting_option:
            self.delete_udd_signal.emit(record_id)
        elif "proxy" == self.current_setting_option:
            self.delete_proxy_signal.emit(record_id)
        elif "re_template" == self.current_setting_option:
            self.delete_re_template_signal.emit(record_id)
        else:
            return

    @pyqtSlot()
    def on_set_selected(self):
        record_id = self.get_selected_ids()[0]
        self.set_udd_selected_signal.emit(record_id)
        pass

    @pyqtSlot()
    def _on_set_to_default(self):
        record_id = self.get_selected_ids()[0]
        self.re_template_set_default_signal.emit(record_id)
        pass


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication([])
    dialog = DialogSettings(
        SettingProxyModel(),
        SettingUserDataDirModel(),
    )
    dialog.show()
    sys.exit(app.exec())
