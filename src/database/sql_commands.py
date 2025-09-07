# src/database/sql_commands.py
from src import my_constants as constants

CREATE_USER_TABLE = f"""
CREATE TABLE IF NOT EXISTS {constants.TABLE_USER} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status INTEGER,
    uid TEXT UNIQUE,
    my_id TEXT,
    username TEXT,
    password TEXT,
    two_fa TEXT,
    email TEXT,
    email_password TEXT,
    phone_number TEXT,
    note TEXT,
    type TEXT,
    user_group INTEGER,
    mobile_ua TEXT,
    desktop_ua TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""

CREATE_USER_LISTED_PRODUCT_TABLE = f"""
CREATE TABLE IF NOT EXISTS {constants.TABLE_USER_LISTED_PRODUCT} (
    id INTEGER PRIMARY KEY,
    id_user INTEGER REFERENCES {constants.TABLE_USER}(id),
    pid TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""
CREATE_USER_ACTION_TABLE = f"""
CREATE TABLE IF NOT EXISTS {constants.TABLE_USER_ACTION} (
    id INTEGER PRIMARY KEY,
    id_user INTEGER REFERENCES {constants.TABLE_USER}(id),
    action_name TEXT,
    action_payload TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""

CREATE_SETTING_UDD_TABLE = f"""
CREATE TABLE IF NOT EXISTS {constants.TABLE_SETTING_USER_DATA_DIR} (
id INTEGER PRIMARY KEY AUTOINCREMENT,
value TEXT UNIQUE NOT NULL,
is_selected INTEGER,
updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""
CREATE_SETTING_PROXY_TABLE = f"""
CREATE TABLE IF NOT EXISTS {constants.TABLE_SETTING_PROXY} (
id INTEGER PRIMARY KEY AUTOINCREMENT,
value TEXT UNIQUE NOT NULL,
updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""

CREATE_REAL_ESTATE_PRODUCT_TABLE = f"""
CREATE TABLE IF NOT EXISTS {constants.TABLE_REAL_ESTATE_PRODUCT} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid TEXT UNIQUE,
    status INT,
    transaction_type TEXT,
    province TEXT,
    district TEXT,
    ward TEXT,
    street TEXT,
    category TEXT,
    area REAL,
    price REAL,
    legal TEXT,
    structure REAL,
    function TEXT,
    building_line TEXT,
    furniture TEXT,
    description TEXT,
    image_dir TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""
CREATE_MISC_PRODUCT_TABLE = f"""
CREATE TABLE IF NOT EXISTS {constants.TABLE_MISC_PRODUCT} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid TEXT UNIQUE,
    category TEXT,
    title TEXT,
    description TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""
CREATE_REAL_ESTATE_TEMPLATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {constants.TABLE_REAL_ESTATE_TEMPLATE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type TEXT,
    category TEXT,
    is_default INT,
    part TEXT,
    value TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
)
"""


# giả sử tôi sử dụng 3 bản để hiển thị (constants.TABLE_USER,
# constants.TABLE_USER_LISTED_PRODUCT,
# constants.TABLE_USER_ACTION,) làm cách nào để thay đổi đồng bộ
