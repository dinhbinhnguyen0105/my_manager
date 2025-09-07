# src/views/robot/dialog_run_bot.py
import os
from typing import Dict
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QFileDialog
from PyQt6.QtGui import QIntValidator

from src.my_types import RobotSettingsType
from src.ui.dialog_robot_run_ui import Ui_Dialog_RobotRun


class DialogRobotRun(QDialog, Ui_Dialog_RobotRun):
    setting_data_signal = pyqtSignal(RobotSettingsType)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle(f"Run settings")

        self.robot_settings = RobotSettingsType(
            is_mobile=False,
            headless=False,
            thread_num=0,
            group_num=0,
            delay_num=0,
            group_file_path="",
        )
        self.delay_time_input.setText("0")
        self.group_num_input.setText("3")
        self.thread_num_input.setValidator(QIntValidator())
        self.group_num_input.setValidator(QIntValidator())
        self.delay_time_input.setValidator(QIntValidator())

        self.buttonBox.accepted.disconnect()
        self.buttonBox.accepted.connect(self.handle_run)
        self.select_group_file_btn.clicked.connect(self.handle_open_directory)

    def handle_run(self):
        self.robot_settings.is_mobile = self.is_mobile_checkbox.isChecked()
        self.robot_settings.headless = self.is_headless_checkbox.isChecked()
        self.robot_settings.thread_num = int(self.thread_num_input.text())
        self.robot_settings.group_num = int(self.group_num_input.text())
        self.robot_settings.delay_num = float(self.delay_time_input.text())
        self.setting_data_signal.emit(self.robot_settings)
        self.accept()

    def handle_open_directory(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select group json file", "", "JSON Files (*.json);;All Files (*)"
        )
        label_text = self.select_group_file_label.text()
        if file_path:
            self.select_group_file_label.setText("File selected")
            self.robot_settings.group_file_path = file_path
        else:
            self.select_group_file_label.setText(label_text)
