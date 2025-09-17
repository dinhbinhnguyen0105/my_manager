import json
from datetime import datetime

if __name__ == "__main__":
    file_path = "/Volumes/KINGSTON/Dev/python/python.my-manager.v3/users_macmini.json"
    data = []
    with open(file=file_path, mode="r", encoding="utf8") as f:
        data = json.load(f)
        for index, item in enumerate(data):
            try:
                date_object = datetime.strptime(
                    item["created_at"], "%Y-%m-%d %H:%M:%S.%f"
                )
            except:
                date_object = datetime.strptime(item["created_at"], "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now()
            diffurent_date = current_time - date_object
            if item["user_group"] < 0:
                continue

            # if ".without_group_marketplace." in item["note"]:
            #     item["note"] = item["note"].replace("without_group_marketplace.", "")
            # if diffurent_date.days > 61:
            #     item["note"] = "every."
    if data:
        with open(file=file_path, mode="w", encoding="utf8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
