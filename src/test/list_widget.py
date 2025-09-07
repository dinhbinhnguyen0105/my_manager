import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QHBoxLayout,
    QMessageBox,
    QLabel,  # Import QLabel
)
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal  # Import pyqtSignal


# 1. Tạo một widget tùy chỉnh cho mỗi item
class ListItemWidget(QWidget):
    # Tín hiệu được phát ra khi nút xóa của item này được click
    # Nó sẽ truyền văn bản của item để biết item nào cần xóa
    delete_requested = pyqtSignal(str)

    def __init__(self, text: str, parent: QWidget = None):
        super().__init__(parent)
        self.item_text = text  # Lưu trữ văn bản của item

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # Xóa lề để nút x gần text hơn

        self.label = QLabel(text)
        self.label.setTextFormat(
            Qt.TextFormat.PlainText
        )  # Chỉ hiển thị văn bản thuần túy
        self.label.setWordWrap(True)  # Cho phép ngắt dòng nếu văn bản dài

        self.delete_button = QPushButton("x")
        self.delete_button.setFixedSize(20, 20)  # Kích thước nhỏ cho nút x
        self.delete_button.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336; /* Màu đỏ */
                color: white;
                border-radius: 10px; /* Bo tròn */
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #d32f2f; /* Đỏ sẫm hơn khi hover */
            }
            QPushButton:pressed {
                background-color: #b71c1c; /* Đỏ đậm hơn khi nhấn */
            }
            """
        )
        self.delete_button.clicked.connect(self._on_delete_button_clicked)

        main_layout.addWidget(self.label)
        main_layout.addStretch(1)  # Đẩy nút x sang phải
        main_layout.addWidget(self.delete_button)

        self.setLayout(main_layout)

    @pyqtSlot()
    def _on_delete_button_clicked(self):
        # Phát tín hiệu yêu cầu xóa, truyền văn bản của item này
        self.delete_requested.emit(self.item_text)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quản lý Item trong QListWidget với nút Xóa")
        self.setGeometry(100, 100, 400, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Tạo QListWidget
        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)

        # Thêm một số item mặc định (sử dụng hàm thêm item mới)
        self._add_item_to_list("Item 1 - Mặc định")
        self._add_item_to_list("Item 2 - Mặc định")
        self._add_item_to_list("Item 3 - Mặc định")

        # Khung nhập liệu và nút Thêm
        add_layout = QHBoxLayout()
        self.add_item_line_edit = QLineEdit()
        self.add_item_line_edit.setPlaceholderText("Nhập item mới...")
        add_button = QPushButton("Thêm Item")
        add_button.clicked.connect(self.add_item_from_input)

        add_layout.addWidget(self.add_item_line_edit)
        add_layout.addWidget(add_button)
        main_layout.addLayout(add_layout)

        # Giữ nút "Xóa Item đã chọn" cho việc xóa hàng loạt hoặc làm ví dụ thay thế
        # Tuy nhiên, chức năng chính sẽ là nút 'x' trên từng item
        self.remove_selected_button = QPushButton("Xóa Item đã chọn (Hàng loạt)")
        self.remove_selected_button.clicked.connect(
            self._remove_selected_items_from_list
        )
        main_layout.addWidget(self.remove_selected_button)

        main_layout.addStretch(1)  # Đẩy các widget lên trên

    @pyqtSlot()
    def add_item_from_input(self):
        """Thêm một item mới vào QListWidget từ văn bản nhập vào."""
        item_text = self.add_item_line_edit.text().strip()
        if item_text:
            self._add_item_to_list(item_text)  # Gọi hàm nội bộ để thêm item
            self.add_item_line_edit.clear()  # Xóa nội dung ô nhập liệu
            QMessageBox.information(self, "Thông báo", f"Đã thêm item: '{item_text}'.")
        else:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập văn bản cho item.")

    def _add_item_to_list(self, text: str):
        """
        Hàm nội bộ để thêm một item vào QListWidget bằng ListItemWidget tùy chỉnh.
        """
        # Tạo một QListWidgetItem trống
        list_item = QListWidgetItem(self.list_widget)

        # Tạo widget tùy chỉnh của chúng ta
        item_widget = ListItemWidget(text)

        # Kết nối tín hiệu delete_requested của widget tùy chỉnh
        # với slot xử lý xóa trong MainWindow
        item_widget.delete_requested.connect(self._remove_item_by_text)

        # Đặt kích thước của QListWidgetItem bằng kích thước của widget tùy chỉnh
        list_item.setSizeHint(item_widget.sizeHint())

        # Gán widget tùy chỉnh cho QListWidgetItem
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, item_widget)

    @pyqtSlot(str)
    def _remove_item_by_text(self, item_text_to_delete: str):
        """
        Slot được gọi khi nút 'x' trên ListItemWidget được click.
        Tìm và xóa item tương ứng từ QListWidget.
        """
        reply = QMessageBox.question(
            self,
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa item này: '{item_text_to_delete}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Lặp qua tất cả các item trong QListWidget
            for row in range(self.list_widget.count()):
                list_item = self.list_widget.item(row)
                # Lấy widget tùy chỉnh được gán cho item
                item_widget = self.list_widget.itemWidget(list_item)

                if (
                    item_widget
                    and isinstance(item_widget, ListItemWidget)
                    and item_widget.item_text == item_text_to_delete
                ):
                    # Xóa QListWidgetItem khỏi QListWidget
                    removed_list_item = self.list_widget.takeItem(row)

                    # Giải phóng bộ nhớ của QListWidgetItem đã xóa và widget tùy chỉnh của nó
                    if removed_list_item:
                        # itemWidget() trả về widget nhưng không xóa nó khỏi QListWidget
                        # takeItem() đã xóa item, chúng ta cần deleteLater() cho widget nội bộ
                        if item_widget:  # Kiểm tra lại xem item_widget có tồn tại không
                            item_widget.deleteLater()
                        removed_list_item.deleteLater()

                    QMessageBox.information(
                        self, "Thông báo", f"Đã xóa item: '{item_text_to_delete}'."
                    )
                    return  # Thoát sau khi xóa item đầu tiên tìm thấy

            QMessageBox.warning(
                self, "Lỗi", f"Không tìm thấy item '{item_text_to_delete}' để xóa."
            )

    @pyqtSlot()
    def _remove_selected_items_from_list(self):
        """Xóa tất cả các item hiện tại đang được chọn khỏi QListWidget."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self, "Thông báo", "Vui lòng chọn ít nhất một item để xóa."
            )
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận xóa hàng loạt",
            f"Bạn có chắc chắn muốn xóa {len(selected_items)} item đã chọn?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Lặp ngược để tránh lỗi chỉ mục khi xóa nhiều item
            for item in reversed(selected_items):
                row = self.list_widget.row(item)
                removed_list_item = self.list_widget.takeItem(row)

                if removed_list_item:
                    # Lấy widget tùy chỉnh và xóa nó
                    item_widget = self.list_widget.itemWidget(removed_list_item)
                    if item_widget:
                        item_widget.deleteLater()
                    removed_list_item.deleteLater()

            QMessageBox.information(
                self, "Thông báo", f"Đã xóa {len(selected_items)} item đã chọn."
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
