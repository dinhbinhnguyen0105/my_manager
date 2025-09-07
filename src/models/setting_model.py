# src/models/setting_model.py
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel
from src.my_constants import (
    TABLE_SETTING_PROXY,
    TABLE_SETTING_USER_DATA_DIR,
    CONNECTION_DB_SETTING,
)
from src.models.base_model import BaseModel


class SettingProxyModel(BaseModel):
    def __init__(self, parent=None):
        db = QSqlDatabase.database(CONNECTION_DB_SETTING)
        if not db.isValid() or not db.isOpen():
            warning_msg = f"Warning: Database connection '{CONNECTION_DB_SETTING}' is not valid or not open."
            print(warning_msg)
        super().__init__(TABLE_SETTING_PROXY, db, parent)
        # self.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)


class SettingUserDataDirModel(BaseModel):
    def __init__(self, parent=None):
        db = QSqlDatabase.database(CONNECTION_DB_SETTING)
        if not db.isValid() or not db.isOpen():
            warning_msg = f"Warning: Database connection '{CONNECTION_DB_SETTING}' is not valid or not open."
            print(warning_msg)
        super().__init__(TABLE_SETTING_USER_DATA_DIR, db, parent)
        # self.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
