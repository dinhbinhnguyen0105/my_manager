# src/database/setting_database.py
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

from src.my_constants import (
    CONNECTION_DB_SETTING,
    PATH_DB_SETTING,
)
from src.database.sql_commands import (
    CREATE_SETTING_UDD_TABLE,
    CREATE_SETTING_PROXY_TABLE,
)


def initialize_setting_database():
    if QSqlDatabase.contains(CONNECTION_DB_SETTING):
        db = QSqlDatabase.database(CONNECTION_DB_SETTING)
    else:
        db = QSqlDatabase.addDatabase("QSQLITE", CONNECTION_DB_SETTING)

    db.setDatabaseName(PATH_DB_SETTING)
    if not db.open():
        raise Exception(
            f"An error occurred while opening the database: {db.lastError().text()}"
        )
    query = QSqlQuery(db)
    query.exec("PRAGMA foreign_keys = ON;")
    query.exec("PRAGMA journal_mode = WAL;")

    try:
        if db.transaction():
            for sql in [
                CREATE_SETTING_UDD_TABLE,
                CREATE_SETTING_PROXY_TABLE,
            ]:
                if not query.exec(sql):
                    db.rollback()
                    raise Exception(
                        f"[initialize_setting_database] An error occurred while creating table: {query.lastError().text()}"
                    )
            if not db.commit():
                db.rollback()
                raise Exception(
                    f"[initialize_setting_database] Cannot commit transaction: {db.lastError().text()}"
                )
            return True
        else:
            return False
    except Exception as e:
        raise e
