# src/my_constants.py
import os
from dotenv import load_dotenv

load_dotenv()

CONNECTION_DB_USER = "user_connection"
CONNECTION_DB_PRODUCT = "product_connection"
CONNECTION_DB_SETTING = "setting_connection"

PATH_DB_USER = os.getenv("PATH_DB_USER")
PATH_DB_PRODUCT = os.getenv("PATH_DB_PRODUCT")
PATH_DB_SETTING = os.getenv("PATH_DB_SETTING")

TABLE_USER = "user"
TABLE_USER_LISTED_PRODUCT = "listed_products"
TABLE_USER_ACTION = "user_actions"
TABLE_SETTING_USER_DATA_DIR = "user_data_dir"
TABLE_SETTING_PROXY = "proxy"
TABLE_REAL_ESTATE_PRODUCT = "real_estate_product"
TABLE_MISC_PRODUCT = "misc"
TABLE_REAL_ESTATE_TEMPLATE = "real_estate_template"

RE_CONTACT = {
    "phone_number": "0375155525",
    "phone_number_icon": "0️⃣3️⃣7️⃣5️⃣1️⃣5️⃣5️⃣5️⃣2️⃣5️⃣",
    "name": "Đ. Bình",
}

RE_TRANSACTION = {"sell": "bán", "rent": "cho thuê", "assignment": "sang nhượng"}
RE_STATUS = {"1": "khả dụng", "0": "không khả dụng"}
RE_CATEGORY = {
    "house": "nhà phố",
    "shop_house": "nhà mặt tiền",
    "apartment": "căn hộ/ chung cư",
    "villa": "biệt thự",
    "land": "đất nền",
    "workshop": "kho/bãi",
    "retail_space": "mbkd",
    "hotel": "khách sạn",
    "homestay": "homestay",
}
RE_PROVINCE = {
    "lam_dong": "lâm đồng",
}
RE_DISTRICT = {"da_lat": "đà lạt"}
RE_WARD = {
    "ward_1 ": "phường 1",
    "ward_2 ": "phường 2",
    "ward_3 ": "phường 3",
    "ward_4 ": "phường 4",
    "ward_5 ": "phường 5",
    "ward_6 ": "phường 6",
    "ward_7 ": "phường 7",
    "ward_8 ": "phường 8",
    "ward_9 ": "phường 9",
    "ward_10 ": "phường 10",
    "ward_11 ": "phường 11",
    "ward_12 ": "phường 12",
    "tram_hanh": "trạm hành",
    "ta_nung": "tà nung",
    "xuan_truong": "xuân trường",
    "xuan_tho": "xuân thọ",
}
RE_BUILDING_LINE = {
    "big_road": "đường xe hơi",
    "small_road": "đường xe máy",
}
RE_LEGAL = {
    "none": "mua bán vi bằng",
    "snnc": "sổ nông nghiệp chung",
    "snnpq": "sổ nông nghiệp phân quyền",
    "snnr": "sổ nông nghiệp riêng",
    "sxdc": "sổ xây dựng chung",
    "sxdpq": "sổ xây dựng phân quyền",
    "sxdr": "sổ xây dựng riêng",
}
RE_FURNITURE = {
    "none": "không nội thất",
    "basic": "nội thất cơ bản",
    "full": "đầy đủ nội thất",
}
RE_UNIT = {
    RE_TRANSACTION["sell"]: "tỷ",
    RE_TRANSACTION["rent"]: "triệu/tháng",
    RE_TRANSACTION["assignment"]: "triệu/tháng",
}


ICONS = [
    "🌼",
    "🌸",
    "🌺",
    "🏵️",
    "🌻",
    "🌷",
    "🌹",
    "🥀",
    "💐",
    "🌾",
    "🎋",
    "☘",
    "🍀",
    "🍃",
    "🍂",
    "🍁",
    "🌱",
    "🌿",
    "🎍",
    "🌵",
    "🌴",
    "🌳",
    "🎄",
    "🍄",
    "🌎",
    "🌍",
    "🌏",
    "🌜",
    "🌛",
    "🌕",
    "🌖",
    "🌗",
    "🌘",
    "🌑",
    "🌒",
    "🌓",
    "🌔",
    "🌚",
    "🌝",
    "🌙",
    "💫",
    "⭐",
    "🌟",
    "✨",
    "⚡",
    "🔥",
    "💥",
    "☄️",
    "🌞",
    "☀️",
    "🌤️",
    "⛅",
    "🌥️",
    "🌦️",
    "☁️",
    "🌧️",
    "⛈️",
    "🌩️",
    "🌨️",
    "🌈",
    "💧",
    "💦",
    "☂️",
    "☔",
    "🌊",
    "🌫",
    "🌪",
    "💨",
    "❄",
    "🌬",
    "⛄",
    "☃️",
    "♥️",
    "❤️",
    "💛",
    "💚",
    "💙",
    "💜",
    "🖤",
    "💖",
    "💝",
    "💔",
    "❣️",
    "💕",
    "💞",
    "💓",
    "💗",
    "💘",
    "💟",
    "💌",
    "💋",
    "👄",
    "💄",
    "💍",
    "📿",
    "🎁",
    "👙",
    "👗",
    "👚",
    "👕",
    "👘",
    "️🎽",
    "👘",
    "👖",
    "👠",
    "👡",
    "👢",
    "👟",
    "👞",
    "👒",
    "🎩",
    "🎓",
    "👑",
    "⛑️",
    "👓",
    "🕶️",
    "🌂",
    "👛",
    "👝",
    "👜",
    "💼",
    "🎒",
    "🛍️",
    "️🛒",
    "️🎭",
    "️🎦",
    "️🎨",
    "️🤹",
    "️🎊",
    "️🎉",
    "️🎈",
    "️🎧",
    "️🎷",
    "️🎺",
    "️🎸",
    "️🎻",
    "️🥁",
    "️🎹",
    "️🎤",
    "️🎵",
    "️🎶",
    "️🎼",
    "️⚽",
    "️🏀",
    "️🏈",
    "️⚾",
    "️🏐",
    "️🏉",
    "️🎱",
    "️🎾",
    "️🏸",
    "️🏓",
    "️🏏",
    "️🏑",
    "️🏒",
    "️🥅",
    "️⛸️",
    "️🎿",
    "️🥊",
    "️🥋",
    "️⛳",
    "️🎳",
    "️🏹",
    "️🎣",
    "️🎯",
    "🚵",
    "️🎖️",
    "️🏅",
    "️🥇",
    "️🥈",
    "️🥉",
    "️🏆",
]


ROBOT_ACTION_NAMES = {
    "list_on_group_and_share": "create on group & share",
    "marketplace": "marketplace & share",
    "discussion": "discussion",
    "list_on_marketplace": "marketplace",
    "share_latest_product": "share (mobile)",
    "join_groups": "join groups",
    # "fb_create_account": "create new account",
    # "interaction": "Tương tác",
}

ROBOT_ACTION_CONTENT_OPTIONS = {
    "pid": "PID",
    "random": "ngẫu nhiên pid",
    "content": "tuỳ chọn nội dung",
}

"""
action payload {
    marketplace: "title", "description", "images"
    discussion: "body", Optional["images"]
    action_playload chỉ hiển thị pid, random_pid, content
    content sẽ chứa là các trường tương ứng với action_name 
}
"""
