from dataclasses import fields
import random
from datetime import datetime
from src.my_constants import ICONS, RE_UNIT, RE_CONTACT
from src.my_types import RealEstateProductType


def replace_template(product_data: RealEstateProductType, template: str) -> str:
    result = template
    for field_info in fields(RealEstateProductType):
        field_name = field_info.name
        field_value = getattr(product_data, field_name, None)
        if field_value is None:
            field_value = ""
        placeholder = f"<{field_name}>"
        if field_name in [
            "street",
            "district",
            "ward",
            "province",
        ]:
            result = result.replace(placeholder, str(field_value).title())
        result = result.replace(placeholder, str(field_value).capitalize())

    for key in RE_CONTACT.keys():
        result = result.replace(f"<{key}>", RE_CONTACT.get(key, ""))

    if "<unit>" in result:
        result = result.replace("<unit>", RE_UNIT[product_data.transaction_type])

    while "<icon>" in result:
        random_icon = random.choice(ICONS)
        result = result.replace("<icon>", random_icon, 1)

    return result


def init_footer_content(product_data: RealEstateProductType) -> str:
    return f"""
------------------------------
🌺Ký gửi mua, bán - cho thuê, thuê bất động sản xin liên hệ 0375155525 - Đ. Bình🌺
------------------------------
[
    PID: <{product_data.pid}>
    updated_at: <{product_data.updated_at}>
    published_at: <{str(datetime.now())}>
]
"""
