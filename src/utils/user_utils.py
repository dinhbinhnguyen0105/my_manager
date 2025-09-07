import json
import os
import uuid
from typing import List, Dict, Any


def add_uuid_to_json_file(input_file_path: str, output_file_path: str) -> None:
    """
    Đọc một file JSON chứa danh sách các đối tượng,
    thêm trường 'my_id' với giá trị UUID v4 cho mỗi đối tượng,
    sau đó ghi dữ liệu đã cập nhật vào một file JSON mới.

    Args:
        input_file_path (str): Đường dẫn đến file JSON đầu vào.
        output_file_path (str): Đường dẫn đến file JSON đầu ra (sẽ được tạo/ghi đè).
    """
    try:
        # 1. Đọc dữ liệu từ file JSON đầu vào
        with open(input_file_path, "r", encoding="utf-8") as f:
            data: List[Dict[str, Any]] = json.load(f)

        # 2. Thêm trường 'my_id' với UUID v4 cho mỗi đối tượng
        updated_data: List[Dict[str, Any]] = []
        for item in data:
            if "my_id" not in item:  # Kiểm tra để tránh ghi đè nếu đã tồn tại
                item["my_id"] = str(uuid.uuid4())  # Tạo UUID v4 và chuyển thành chuỗi
            updated_data.append(item)

        # 3. Ghi dữ liệu đã cập nhật vào file JSON đầu ra
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=4, ensure_ascii=False)

        print(
            f"Đã thêm trường 'my_id' với UUID v4 và ghi vào file '{output_file_path}' thành công."
        )

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file đầu vào tại đường dẫn '{input_file_path}'.")
    except json.JSONDecodeError:
        print(f"Lỗi: File '{input_file_path}' không phải là định dạng JSON hợp lệ.")
    except Exception as e:
        print(f"Đã xảy ra lỗi không mong muốn: {e}")


def rename_subdirectories_from_json(
    user_container_path: str, json_file_path: str
) -> None:
    """
    Đọc một file JSON chứa danh sách các đối tượng (mỗi đối tượng có 'id' và 'my_id').
    Sau đó, đổi tên các thư mục con trong 'user_container_path' từ giá trị 'id'
    thành giá trị 'my_id' tương ứng.

    Args:
        user_container_path (str): Đường dẫn đến thư mục chứa các thư mục con cần đổi tên.
        json_file_path (str): Đường dẫn đến file JSON chứa thông tin 'id' và 'my_id'.
    """
    if not os.path.isdir(user_container_path):
        print(f"Lỗi: Thư mục '{user_container_path}' không tồn tại.")
        return

    try:
        # 1. Đọc dữ liệu từ file JSON
        with open(json_file_path, "r", encoding="utf-8") as f:
            data: List[Dict[str, Any]] = json.load(f)

    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file JSON tại đường dẫn '{json_file_path}'.")
        return
    except json.JSONDecodeError:
        print(f"Lỗi: File '{json_file_path}' không phải là định dạng JSON hợp lệ.")
        return
    except Exception as e:
        print(f"Đã xảy ra lỗi khi đọc file JSON: {e}")
        return

    # 2. Xây dựng ánh xạ từ ID cũ sang MY_ID mới
    # Một dictionary để tra cứu nhanh chóng: {old_id_str: my_id_str}
    id_to_my_id_map: Dict[str, str] = {}
    for item in data:
        # Đảm bảo 'id' và 'my_id' tồn tại và có kiểu dữ liệu hợp lệ
        if "id" in item and "my_id" in item:
            # Chuyển đổi id sang chuỗi để khớp với tên thư mục (thường là chuỗi)
            old_id_str = str(item["id"])
            my_id_str = str(item["my_id"])
            id_to_my_id_map[old_id_str] = my_id_str
        elif "id" in item and "my_id" not in item:
            print(
                f"Cảnh báo: Mục có ID '{item['id']}' trong JSON không có trường 'my_id'. Bỏ qua."
            )

    if not id_to_my_id_map:
        print(
            "Không tìm thấy cặp ID/MY_ID hợp lệ nào trong file JSON để thực hiện đổi tên."
        )
        return

    # 3. Duyệt qua các thư mục con và thực hiện đổi tên
    print(f"Bắt đầu đổi tên thư mục trong '{user_container_path}'...")
    renamed_count = 0
    skipped_count = 0

    # Lấy danh sách tất cả các mục (file và thư mục) trong user_container_path
    for entry_name in os.listdir(user_container_path):
        old_dir_path = os.path.join(user_container_path, entry_name)

        # Chỉ xử lý các thư mục
        if os.path.isdir(old_dir_path):
            # Kiểm tra xem tên thư mục có khớp với một ID cũ trong map không
            if entry_name in id_to_my_id_map:
                new_id_name = id_to_my_id_map[entry_name]
                new_dir_path = os.path.join(user_container_path, new_id_name)

                if os.path.exists(new_dir_path):
                    print(
                        f"Cảnh báo: Thư mục đích '{new_dir_path}' đã tồn tại. Không đổi tên '{entry_name}'."
                    )
                    skipped_count += 1
                    continue

                try:
                    os.rename(old_dir_path, new_dir_path)
                    print(f"Đã đổi tên '{entry_name}' thành '{new_id_name}'")
                    renamed_count += 1
                except OSError as e:
                    print(f"Lỗi khi đổi tên '{entry_name}' thành '{new_id_name}': {e}")
                    skipped_count += 1
            else:
                print(
                    f"Bỏ qua thư mục '{entry_name}': Không tìm thấy ID tương ứng trong JSON."
                )
                skipped_count += 1
        else:
            print(f"Bỏ qua '{entry_name}': Không phải là thư mục.")
            skipped_count += 1

    print(f"\nQuá trình đổi tên hoàn tất.")
    print(f" - Số thư mục đã đổi tên: {renamed_count}")
    print(f" - Số mục đã bỏ qua: {skipped_count}")


# --- Cách sử dụng hàm ---
if __name__ == "__main__":
    # add_uuid_to_json_file(
    #     "/Volumes/KINGSTON/Dev/python/python.my-manager.v3/users_main.json",
    #     "/Volumes/KINGSTON/Dev/python/python.my-manager.v3/users_main_2.json",
    # )

    # rename_subdirectories_from_json(
    #     "/Volumes/KINGSTON/Dev/python/python.my-manager.v3/src/repositories/user_data_dirs",
    #     "/Volumes/KINGSTON/Dev/python/python.my-manager.v3/users_main_2.json",
    # )
    pass
