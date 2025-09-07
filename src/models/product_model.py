# src/models/product_model.py
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel

from src.my_constants import (
    CONNECTION_DB_PRODUCT,
    TABLE_REAL_ESTATE_PRODUCT,
    TABLE_MISC_PRODUCT,
    TABLE_REAL_ESTATE_TEMPLATE,
)
from src.models.base_model import BaseModel


class RealEstateProductModel(BaseModel):

    def __init__(self, parent=None):
        db = QSqlDatabase.database(CONNECTION_DB_PRODUCT)
        if not db.isValid() or not db.isOpen():
            print(
                f"Warning: Database connection '{CONNECTION_DB_PRODUCT}' is not valid or not open."
            )
        super().__init__(TABLE_REAL_ESTATE_PRODUCT, db, parent)

    def find_row_by_pid(self, pid: str) -> int:
        pid_col_index = self.fieldIndex("pid")
        if pid_col_index == -1:
            print("[BaseModel] 'pid' field not found for search.")

            return -1
        for row in range(self.rowCount()):
            index = self.index(row, pid_col_index)
            if self.data(index) == pid:
                return row
        return -1


class MiscProductModel(BaseModel):

    def __init__(self, parent=None):
        db = QSqlDatabase.database(CONNECTION_DB_PRODUCT)
        if not db.isValid() or not db.isOpen():
            print(
                f"Warning: Database connection '{CONNECTION_DB_PRODUCT}' is not valid or not open."
            )
        super().__init__(TABLE_MISC_PRODUCT, db, parent)

    def find_row_by_pid(self, pid: str) -> int:
        pid_col_index = self.fieldIndex("pid")
        if pid_col_index == -1:
            print("[BaseModel] 'pid' field not found for search.")

            return -1
        for row in range(self.rowCount()):
            index = self.index(row, pid_col_index)
            if self.data(index) == pid:
                return row
        return -1


class RealEstateTemplateModel(BaseModel):
    def __init__(self, parent=None):
        db = QSqlDatabase.database(CONNECTION_DB_PRODUCT)
        if not db.isValid() or not db.isOpen():
            print(
                f"Warning: Database connection '{CONNECTION_DB_PRODUCT}' is not valid or not open."
            )
        super().__init__(TABLE_REAL_ESTATE_TEMPLATE, db, parent)
        # self.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)

    def find_row_by_tid(self, tid: str) -> int:
        tid_col_index = self.fieldIndex("tid")
        if tid_col_index == -1:
            print("[BaseModel] 'tid' field not found for search.")

            return -1
        for row in range(self.rowCount()):
            index = self.index(row, tid_col_index)
            if self.data(index) == tid:
                return row
        return -1
