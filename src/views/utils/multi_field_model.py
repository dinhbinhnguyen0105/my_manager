# src/views/utils/multi_field_model.py
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QModelIndex

from PyQt6.QtGui import QBrush, QColor


class MultiFieldFilterProxyModel(QSortFilterProxyModel):
    SERIAL_NUMBER_COLUMN_INDEX = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = {}

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        # Lấy dữ liệu từ source model trước
        source_index = self.mapToSource(index)

        # Lấy status_value từ source model để xử lý màu
        status_col = self.sourceModel().fieldIndex("status")
        status_value = -1  # Giá trị mặc định
        if status_col != -1:
            status_index = self.sourceModel().index(source_index.row(), status_col)
            status_text = self.sourceModel().data(
                status_index, Qt.ItemDataRole.DisplayRole
            )
            try:
                status_value = int(status_text)
            except (ValueError, TypeError):
                pass

        # Xử lý màu nền (BackgroundRole)
        if role == Qt.ItemDataRole.BackgroundRole:
            if status_value == 0:
                return QBrush(QColor("#e7625f"))  # Màu nền ưu tiên cho status == 0

            # Tô màu xen kẽ nếu không có điều kiện đặc biệt
            return QBrush(QColor("#d3eaf2" if index.row() % 2 == 0 else "#f8e3ec"))

        # Xử lý màu chữ (ForegroundRole)
        if role == Qt.ItemDataRole.ForegroundRole:
            # Nếu status là 0, tô màu chữ trắng để dễ đọc trên nền đỏ
            # if status_value == 0:
            return QBrush(QColor("#000000"))

        # Trả về giá trị mặc định cho các role khác
        return super().data(index, role)

    def set_filter(self, column, text):
        self.filters[column] = text.lower().strip() if type(text) == str else str(text)
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        for column, text in self.filters.items():
            if text:
                index = model.index(source_row, column, source_parent)
                data = str(model.data(index, Qt.ItemDataRole.DisplayRole)).lower()
                if text not in data:
                    return False
        return True
