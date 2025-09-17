# src/views/utils/multi_field_model.py
from PyQt6.QtCore import (
    Qt,
    QSortFilterProxyModel,
)

from PyQt6.QtGui import QBrush, QColor


class MultiFieldFilterProxyModel(QSortFilterProxyModel):
    SERIAL_NUMBER_COLUMN_INDEX = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = {}

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.BackgroundRole:
            # lấy status từ source model
            source_index = self.mapToSource(index)
            status_col = self.sourceModel().fieldIndex("status")
            if status_col != -1:
                status_index = self.sourceModel().index(source_index.row(), status_col)
                status = self.sourceModel().data(
                    status_index, Qt.ItemDataRole.DisplayRole
                )
                try:
                    if int(status) == 0:
                        return QBrush(QColor("#e7625f"))
                except:
                    pass
            # fallback: tô màu theo row
            return QBrush(QColor("#d3eaf2" if index.row() % 2 == 0 else "#f8e3ec"))

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
