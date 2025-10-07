import os
from PIL import Image


def overlay_logo_on_images(logo_path, image_paths, dest_paths, opacity=0.3):
    """
    Chèn logo lên một loạt hình ảnh và lưu vào các đường dẫn file đích.

    Tham số:
    logo_path (str): Đường dẫn đến file logo (.png).
    image_paths (list): Danh sách các đường dẫn đến các file hình ảnh cần chèn logo.
    dest_paths (list): Danh sách các đường dẫn file đích để lưu các hình ảnh đã được chèn logo.
                       Phải có số lượng phần tử bằng với image_paths.
    opacity (float, optional): Độ mờ của logo (từ 0.0 đến 1.0). Mặc định là 0.7.
    """
    # Kiểm tra số lượng file đầu vào và đầu ra
    if len(image_paths) != len(dest_paths):
        print("Lỗi: Số lượng đường dẫn ảnh đầu vào và đầu ra không khớp nhau.")
        return

    try:
        logo = Image.open(logo_path).convert("RGBA")
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file logo tại '{logo_path}'.")
        return

    # Duyệt qua từng cặp đường dẫn ảnh đầu vào và đầu ra
    for i in range(len(image_paths)):
        image_path = image_paths[i]
        dest_path = dest_paths[i]

        try:
            main_image = Image.open(image_path).convert("RGBA")
            main_width, main_height = main_image.size

            new_logo_width = int(
                main_width * 0.3 if main_width < main_height else main_height * 0.3
            )
            logo_width, logo_height = logo.size
            new_logo_height = int(logo_height * (new_logo_width / logo_width))
            resized_logo = logo.resize((new_logo_width, new_logo_height), Image.LANCZOS)

            # Tạo logo mờ
            alpha = resized_logo.split()[-1]
            alpha = Image.eval(alpha, lambda x: x * opacity)
            resized_logo.putalpha(alpha)

            # Tính toán vị trí trung tâm
            position = (
                (main_width - resized_logo.width) // 2,
                (main_height - resized_logo.height) // 2,
            )

            main_image.paste(resized_logo, position, resized_logo)

            # Tạo thư mục cha nếu chưa tồn tại
            output_dir = os.path.dirname(dest_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Lưu hình ảnh vào đường dẫn đích được chỉ định
            main_image.save(dest_path, "PNG")
            # print(f"Đã chèn logo và lưu vào: '{dest_path}'")

        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file ảnh: '{image_path}'. Bỏ qua.")
        except Exception as e:
            print(f"Lỗi xử lý ảnh '{image_path}': {e}")


def get_subdirectories(path):
    """
    Lấy danh sách các thư mục con trong một thư mục.

    Args:
        path (str): Đường dẫn đến thư mục cha.

    Returns:
        list: Danh sách tên các thư mục con.
    """
    subdirectories = [
        d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))
    ]
    return subdirectories


def get_image_files_os(folder_path):
    """
    Lấy danh sách các tệp hình ảnh trong một thư mục bằng module os.

    Args:
        folder_path (str): Đường dẫn đến thư mục.

    Returns:
        list: Danh sách các đường dẫn đầy đủ đến các tệp hình ảnh.
    """
    image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")
    image_files = []

    if not os.path.isdir(folder_path):
        print(f"Lỗi: Thư mục không tồn tại tại '{folder_path}'")
        return []

    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(image_extensions):
            full_path = os.path.join(folder_path, file_name)
            image_files.append(full_path)

    return image_files


# --- Ví dụ sử dụng ---
if __name__ == "__main__":
    container_path = (
        "/Users/ndb/Dev/python/python.my-manager.v3/src/repositories/images"
    )
    logo_path = "/Users/ndb/Dev/python/python.my-manager.v3/logo.png"
    image_dirs = get_subdirectories(container_path)
    ignore_dirs = [
        "RE.S.b59c10dd",
        "RE.S.106759d6",
        "RE.S.27cfcf42",
        "RE.S.c6def33b",
        "RE.S.a532d9f5",
        "RE.S.aa1d916b",
    ]
    for image_dir in image_dirs:
        if image_dir in ignore_dirs:
            continue
        imgs = get_image_files_os(os.path.join(container_path, image_dir))
        overlay_logo_on_images(logo_path, imgs, imgs, 0.3)
    pass
