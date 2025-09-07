# src/database/user_database.py
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

from src.my_constants import (
    CONNECTION_DB_USER,
    PATH_DB_USER,
)
from src.database.sql_commands import (
    CREATE_USER_TABLE,
    CREATE_USER_LISTED_PRODUCT_TABLE,
    # CREATE_USER_ACTION_TABLE,
)


def initialize_user_database():
    if QSqlDatabase.contains(CONNECTION_DB_USER):
        db = QSqlDatabase.database(CONNECTION_DB_USER)
    else:
        db = QSqlDatabase.addDatabase("QSQLITE", CONNECTION_DB_USER)
    db.setDatabaseName(PATH_DB_USER)
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
                CREATE_USER_TABLE,
                CREATE_USER_LISTED_PRODUCT_TABLE,
                # CREATE_USER_ACTION_TABLE,
            ]:
                if not query.exec(sql):
                    db.rollback()
                    raise Exception(
                        f"[initialize_db_user] An error occurred while creating table: {query.lastError().text()}"
                    )
            if not db.commit():
                db.rollback()
                raise Exception(
                    f"[initialize_db_user] Cannot commit transaction: {db.lastError().text()}"
                )
            return True
        else:
            return False
    except Exception as e:
        raise e
