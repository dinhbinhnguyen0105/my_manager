# src/views/user/dialog_create_user.py
from typing import Dict
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog
from PyQt6.QtGui import QIntValidator

from src.my_types import UserType

from src.ui.dialog_user_ui import Ui_Dialog_User


class DialogCreateUser(QDialog, Ui_Dialog_User):
    user_data_signal = pyqtSignal(UserType)

    def __init__(self, pre_payload: Dict, parent=None):
        super(DialogCreateUser, self).__init__(parent)
        self.pre_payload = pre_payload

        self.setupUi(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(f"Create new user")

        self.group_input.setValidator(QIntValidator())
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.handle_save)

        self.set_input_fields()

    def set_input_fields(self):
        self.status_checkbox.setChecked(True)
        self.password_input.setText(self.pre_payload.get("password", ""))
        self.group_input.setText(self.pre_payload.get("user_group", "-1"))
        self.created_at_input.setText(self.pre_payload.get("created_at", ""))
        self.updated_at_input.setText(self.pre_payload.get("updated_at", ""))
        self.mobile_ua_input.setText(self.pre_payload.get("mobile_ua", ""))
        self.desktop_ua_input.setText(self.pre_payload.get("desktop_ua", ""))
        self.note_input.setText(self.pre_payload.get("note"))

        self.mobile_ua_button.setHidden(True)
        self.desktop_ua_button.setHidden(True)

        if self.password_input.text().strip():
            self.password_input.setDisabled(True)
        if self.created_at_input.text().strip():
            self.created_at_input.setDisabled(True)
        if self.updated_at_input.text().strip():
            self.updated_at_input.setDisabled(True)

    def handle_save(self):
        self.user_data_signal.emit(
            UserType(
                id=None,
                uid=self.uid_input.text().strip(),
                my_id=None,
                username=self.username_input.text().strip(),
                password=self.password_input.text().strip(),
                two_fa=self.two_fa_input.text().strip(),
                email=self.email_input.text().strip(),
                email_password=self.email_password_input.text().strip(),
                phone_number=self.phone_number_input.text().strip(),
                note=self.note_input.text().strip(),
                type=self.type_input.text().strip(),
                user_group=self.group_input.text().strip(),
                mobile_ua=self.mobile_ua_input.text().strip(),
                desktop_ua=self.desktop_ua_input.text().strip(),
                status=self.status_checkbox.isChecked(),
                created_at=self.created_at_input.text().strip(),
                updated_at=self.updated_at_input.text().strip(),
            )
        )
        self.accept()
