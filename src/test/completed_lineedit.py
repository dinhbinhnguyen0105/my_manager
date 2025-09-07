import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QLabel,
    QCompleter,
)
from PyQt6.QtCore import Qt, QStringListModel, pyqtSlot


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gợi ý nhập liệu cho QLineEdit với QCompleter")
        self.setGeometry(100, 100, 450, 250)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.info_label = QLabel("Thử gõ 'a', 'berry', hoặc 'e' vào ô bên dưới:")
        main_layout.addWidget(self.info_label)

        self.input_line_edit = QLineEdit()
        self.input_line_edit.setPlaceholderText("Nhập tên trái cây...")
        main_layout.addWidget(self.input_line_edit)

        # --- 1. Chuẩn bị danh sách gợi ý ---
        self.suggestions = [
            "Apple",
            "Banana",
            "Cherry",
            "Date",
            "Elderberry",
            "Fig",
            "Grape",
            "Honeydew",
            "Kiwi",
            "Lemon",
            "Mango",
            "Nectarine",
            "Orange",
            "Peach",
            "Plum",
            "Raspberry",
            "Strawberry",
            "Watermelon",
            "Blueberry",
            "Avocado",
        ]

        # --- 2. Tạo một QStringListModel từ danh sách gợi ý ---
        self.completer_model = QStringListModel()
        self.completer_model.setStringList(self.suggestions)

        # --- 3. Tạo một QCompleter và gán model cho nó ---
        self.completer = QCompleter(self)  # 'self' (MainWindow) là parent của completer
        self.completer.setModel(self.completer_model)

        # --- 4. Cấu hình QCompleter (Tùy chọn nhưng hữu ích) ---
        # MatchContains: Gợi ý sẽ hiển thị nếu chuỗi nhập vào là chuỗi con bất kỳ
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        # CaseInsensitive: Bỏ qua chữ hoa/thường khi tìm kiếm
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # PopupCompletion: Hiển thị danh sách gợi ý trong một cửa sổ popup
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        # --- 5. Gán QCompleter cho QLineEdit ---
        self.input_line_edit.setCompleter(self.completer)

        # Nút để thêm một gợi ý mới và cập nhật completer
        add_suggestion_button = QPushButton("Thêm 'Dragonfruit' vào gợi ý")
        add_suggestion_button.clicked.connect(self.add_new_suggestion)
        main_layout.addWidget(add_suggestion_button)

        main_layout.addStretch(1)  # Đẩy các widget lên trên cùng

    @pyqtSlot()
    def add_new_suggestion(self):
        """Thêm một gợi ý mới vào danh sách và cập nhật QCompleter."""
        new_item = "Dragonfruit"
        if new_item not in self.suggestions:
            self.suggestions.append(new_item)
            # Cập nhật model của completer với danh sách mới
            self.completer_model.setStringList(self.suggestions)
            QMessageBox.information(
                self, "Thông báo", f"Đã thêm '{new_item}' vào danh sách gợi ý."
            )
        else:
            QMessageBox.information(
                self, "Thông báo", f"'{new_item}' đã có trong danh sách gợi ý rồi."
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
