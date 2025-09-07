# src/views/robot/action_payload.py

from typing import Callable
from PyQt6.QtWidgets import QWidget, QFileDialog
from PyQt6.QtCore import Qt, pyqtSlot, QUrl
from src.ui.action_payload_ui import Ui_ActionPayloadContainer

from src.my_constants import ROBOT_ACTION_NAMES, ROBOT_ACTION_CONTENT_OPTIONS


class ActionPayload(QWidget, Ui_ActionPayloadContainer):
    def __init__(self, set_completer_callback: Callable, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("Action payload")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        set_completer_callback(self.pid_input, self)
        self.image_paths = []
        self.setup_ui()
        self.setup_events()
        self.open_images_btn.setAcceptDrops(True)  # Cho phép kéo-thả lên nút

    def setup_ui(self):
        for key, value in ROBOT_ACTION_NAMES.items():
            self.names_combobox.addItem(value.capitalize(), key)
        for key, value in ROBOT_ACTION_CONTENT_OPTIONS.items():
            self.options_combobox.addItem(value.capitalize(), key)
        self.list_images.setHidden(True)
        self.content_container.setHidden(True)

    def setup_events(self):
        self.on_options_changed(0)
        self.options_combobox.currentIndexChanged.connect(self.on_options_changed)
        self.open_images_btn.clicked.connect(self.on_open_images_clicked)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        # Gán lại các event handler cho drag & drop
        self.open_images_btn.dragEnterEvent = self.open_images_btn_dragEnterEvent
        self.open_images_btn.dropEvent = self.open_images_btn_dropEvent

    def get_values(self):
        results = {
            "action_name": self.names_combobox.currentData(),
            "action_option": self.options_combobox.currentData(),
        }
        if self.pid_input.isVisible():
            _ = self.pid_input.text().strip()
            results["pid"] = _ if _ else None
        elif not self.pid_input.isVisible() and not self.content_container.isVisible():
            results["pid"] = None
        elif self.content_container.isVisible():
            results["content"] = {
                "title": self.title_line_edit.text(),
                "description": self.description_text_edit.toPlainText(),
                "image_paths": self.image_paths,
            }
        return results

    @pyqtSlot(int)
    def on_options_changed(self, index: int):
        current_data = self.options_combobox.itemData(index)
        self.content_container.setVisible(current_data == "content")
        self.pid_input.setVisible(current_data == "pid")
        if current_data == "random" or current_data == "content":
            self.pid_input.clear()

    @pyqtSlot()
    def on_open_images_clicked(self):
        self.image_paths = []
        image_filter = "Image file (*.png *.jpg *.jpeg *.gif);;All file (*.*)"
        images_paths, _ = QFileDialog.getOpenFileUrls(
            self,
            "Select images",
            QUrl(),
            image_filter,
            "",
            # QFileDialog.Option.DontUseNativeDialog,
        )
        self.image_paths = [url.toLocalFile() for url in images_paths]
        if len(self.image_paths):
            self.list_images.clear()
            self.list_images.setVisible(True)
            self.list_images.addItems(self.image_paths)

    @pyqtSlot()
    def on_delete_clicked(self):
        self.deleteLater()

    # --- Drag & Drop event handlers for open_images_btn ---
    def open_images_btn_dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Chỉ chấp nhận nếu có file ảnh
            for url in event.mimeData().urls():
                if (
                    url.toLocalFile()
                    .lower()
                    .endswith((".png", ".jpg", ".jpeg", ".gif"))
                ):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def open_images_btn_dropEvent(self, event):
        urls = event.mimeData().urls()
        image_paths = []
        for url in urls:
            path = url.toLocalFile()
            if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                image_paths.append(path)
        if image_paths:
            self.image_paths = image_paths
            self.list_images.clear()
            self.list_images.setVisible(True)
            self.list_images.addItems(self.image_paths)
        event.acceptProposedAction()
