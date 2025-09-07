# src/models/base_model.py
from typing import List, Any
from PyQt6.QtSql import QSqlTableModel
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtGui import QBrush, QColor


class BaseModel(QSqlTableModel):
    def __init__(self, table_name, db, parent=None):
        super().__init__(parent, db=db)
        self.setTable(table_name)
        self.setEditStrategy(QSqlTableModel.EditStrategy.OnManualSubmit)
        self.status_col = self.fieldIndex("status")
        self.select()
        # self.dataChanged.connect(lambda : print(f"rowCount: {self.rowCount()}"))

    def flags(self, index):
        return (
            Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsEditable
        )

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            return super().data(index, role)
        if role == Qt.ItemDataRole.BackgroundRole and self.status_col != -1:
            status_index = self.index(index.row(), self.status_col)
            status = super().data(status_index, Qt.ItemDataRole.DisplayRole)
            try:
                status_value = int(status)
            except Exception:
                status_value = None
            if status_value == 0:
                return QBrush(QColor("#e7625f"))
        return super().data(index, role)

    def get_record_ids(self, row: List[int]) -> List[Any]:
        ids = []
        id_col_index = self.fieldIndex("id")
        if id_col_index == -1:
            print("[BaseModel] 'id' field not found in table.")
            return []
        for row in rows:
            if 0 <= row < self.rowCount():
                index = self.index(row, id_col_index)
                ids.append(self.data(index))
            else:
                print(f"[BaseModel] Warning: Row index {row} is out of bounds.")
        return ids

    def get_row_by_id(self, db_id: Any) -> int:
        id_col_index = self.fieldIndex("id")
        if id_col_index == -1:
            print("[BaseModel] 'id' field not found for search.")
            return -1

        for row in range(self.rowCount()):
            index = self.index(row, id_col_index)
            if self.data(index) == db_id:
                return row
        return -1
