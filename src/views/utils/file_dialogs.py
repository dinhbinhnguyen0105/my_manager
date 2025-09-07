from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QUrl


def dialog_open_file(parent):
    json_filter = "Json file (*.json)"
    json_path, _ = QFileDialog.getOpenFileUrl(
        parent,
        "Select json file",
        QUrl(),
        json_filter,
        "",
        # QFileDialog.Option.DontUseNativeDialog,
    )
    return json_path.toLocalFile()


def dialog_save_file(parent):
    json_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Lưu File Văn Bản",  # Save Text File
        "",  # Thư mục mặc định (rỗng để sử dụng thư mục hiện tại hoặc thư mục đã mở gần đây)
        "Json file (*.json)",  # Filters
    )
    return json_path
