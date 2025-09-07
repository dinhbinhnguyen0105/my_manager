# src/views/user/dialog_update_user.py
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog
from PyQt6.QtGui import QIntValidator

from src.my_types import UserType

from src.ui.dialog_user_ui import Ui_Dialog_User


class DialogUpdateUser(QDialog, Ui_Dialog_User):
    user_data_signal = pyqtSignal(UserType)
    new_mobile_ua_signal = pyqtSignal()
    new_desktop_ua_signal = pyqtSignal()

    def __init__(self, user_data: UserType, parent=None):
        super(DialogUpdateUser, self).__init__(parent)
        self._user_data = user_data

        self.setupUi(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(f"Create new user")

        self.group_input.setValidator(QIntValidator())
        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.handle_save)

        self.set_input_fields()
        self.setup_events()

    def setup_events(self):
        self.mobile_ua_button.clicked.connect(self.new_mobile_ua_signal)
        self.desktop_ua_button.clicked.connect(self.new_desktop_ua_signal)

    def handle_save(self):
        self.user_data_signal.emit(
            UserType(
                id=self._user_data.id,
                uid=self.uid_input.text(),
                my_id=self._user_data.my_id,
                username=self.username_input.text(),
                password=self.password_input.text(),
                two_fa=self.two_fa_input.text(),
                email=self.email_input.text(),
                email_password=self.email_password_input.text(),
                phone_number=self.phone_number_input.text(),
                note=self.note_input.text(),
                type=self.type_input.text(),
                user_group=self.group_input.text(),
                mobile_ua=self.mobile_ua_input.text(),
                desktop_ua=self.desktop_ua_input.text(),
                status=self.status_checkbox.isChecked(),
                created_at=self._user_data.created_at,
                updated_at=str(datetime.now()),
            )
        )
        self.accept()

    def set_input_fields(self):
        if not self._user_data:
            return
        self.uid_input.setText(self._user_data.uid or "")
        self.username_input.setText(self._user_data.username or "")
        self.password_input.setText(self._user_data.password or "")
        self.two_fa_input.setText(self._user_data.two_fa or "")
        self.email_input.setText(self._user_data.email or "")
        self.email_password_input.setText(self._user_data.email_password or "")
        self.phone_number_input.setText(self._user_data.phone_number or "")
        self.note_input.setText(self._user_data.note or "")
        self.type_input.setText(self._user_data.type or "")
        self.group_input.setText(
            str(self._user_data.user_group)
            if self._user_data.user_group is not None
            else ""
        )
        self.mobile_ua_input.setText(self._user_data.mobile_ua or "")
        self.desktop_ua_input.setText(self._user_data.desktop_ua or "")
        self.status_checkbox.setChecked(bool(self._user_data.status))
        self.created_at_container.setHidden(True)
        self.updated_at_container.setHidden(True)
