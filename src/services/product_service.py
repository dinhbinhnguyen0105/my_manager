# src/services/product_service.py
import uuid
import glob
import os
import shutil
from typing import Optional, List
from PyQt6.QtSql import QSqlQuery

from src.services.base_service import BaseService, transaction
from src.models.product_model import (
    RealEstateProductModel,
    RealEstateTemplateModel,
    MiscProductModel,
)
from src.my_types import RealEstateProductType, RealEstateTemplateType, MiscProductType
from src.my_constants import RE_TRANSACTION, TABLE_REAL_ESTATE_TEMPLATE
from src.utils.images_handler import overlay_logo_on_images


class RealEstateProductService(BaseService):
    DATA_TYPE = RealEstateProductType

    def __init__(self, model: RealEstateProductModel):
        if not isinstance(model, RealEstateProductModel):
            raise TypeError(
                "model must be an instance of RealEstateProductModel or its subclass."
            )
        super().__init__(model)

    def create(
        self,
        image_dir_container: str,
        image_paths: List[str],
        payload: RealEstateProductType,
    ) -> bool:
        product_dir = os.path.abspath(os.path.join(image_dir_container, payload.pid))
        if not os.path.exists(product_dir):
            os.makedirs(product_dir)

        for field in ["price", "area", "structure"]:
            if hasattr(payload, field):
                value = getattr(payload, field)
                if not value:
                    value = 0
                if isinstance(value, str):
                    new_value = float(value.replace(",", "."))
                    setattr(payload, field, new_value)
        logo_path = os.path.join(image_dir_container, "logo.png")
        dest_paths = []

        for idx, image_path in enumerate(image_paths):
            if os.path.isfile(image_path):
                ext = os.path.splitext(image_path)[1]
                base_name = getattr(payload, "uid", None) or getattr(
                    payload, "pid", "img"
                )
                new_name = f"{base_name}_{idx+1}{ext}"
                dest_path = os.path.join(product_dir, new_name)
                dest_paths.append(dest_path)
        if os.path.isfile(logo_path):
            overlay_logo_on_images(logo_path, image_paths, dest_paths)
        else:
            for idx, img in enumerate(image_paths):
                shutil.copy(img, dest_paths[idx])
        payload.image_dir = product_dir
        return super().create(payload)

    def read(self, record_id: int) -> Optional[RealEstateProductType]:
        return super().read(record_id)

    def read_all(self) -> List[RealEstateProductType]:
        return super().read_all()

    def update(self, record_id: int, payload: RealEstateProductType) -> bool:
        return super().update(record_id, payload)

    def delete(self, record_id: int) -> bool:
        product_data = self.read(record_id)
        if product_data and getattr(product_data, "image_dir", None):
            image_dir = product_data.image_dir
            if os.path.isdir(image_dir):
                try:
                    shutil.rmtree(image_dir)
                except Exception as e:
                    print(
                        f"[{self.__class__.__name__}.delete] Warning: Failed to remove image directory '{image_dir}': {e}"
                    )
        return super().delete(record_id)

    def delete_multiple(self, record_ids: List[int]):
        return super().delete_multiple(record_ids)

    def import_data(self, payload: List[RealEstateProductType]):
        return super().import_data(payload)

    def read_by_pid(self, pid: str) -> Optional[RealEstateProductType]:
        return self._find_by_model_index(find_method_name="find_row_by_pid", value=pid)

    def toggle_status(self, record_id: int) -> bool:
        product = self.read(record_id)
        if product is None:
            print(
                f"[{self.__class__.__name__}.toggle_status] Product with record_id '{record_id}' not found."
            )
            return False

        current_status = product.status
        if current_status == 0:
            new_status = 1
        elif current_status == 1:
            new_status = 0
        else:
            print(
                f"[{self.__class__.__name__}.toggle_status] Unexpected status value for record_id '{record_id}': {current_status}. Cannot toggle."
            )
            return False

        product.status = new_status
        update_success = self.update(record_id, product)
        if update_success:
            # print(
            #     f"[{self.__class__.__name__}.toggle_status] Successfully toggled status for record_id '{record_id}' to {new_status}."
            # )
            return True
        else:
            print(
                f"[{self.__class__.__name__}.toggle_status] Failed to update status for record_id '{record_id}'."
            )
            return False

    def initialize_new_pid(self, transaction_type: str) -> str:
        """
        Initializes and generates a new unique product identifier (PID).

        Returns:
            str: The newly generated unique product identifier.
        """
        try:
            if not transaction_type in RE_TRANSACTION.values():
                raise KeyError()
            else:
                while True:
                    uuid_str = str(uuid.uuid4())
                    pid = uuid_str.replace("-", "")[:8]
                    if transaction_type == "bán":
                        pid = "S." + pid
                    elif transaction_type == "cho thuê":
                        pid = "R." + pid
                    elif transaction_type == "sang nhượng":
                        pid = "A." + pid
                    pid = "RE." + pid
                    if not self.read_by_pid(pid):
                        return pid
        except KeyError:
            raise KeyError(
                f"[{__class__.__name__}.initialize_new_pid] Error: Invalid transaction type ({transaction_type})."
            )

    def get_images_by_id(self, record_id: int) -> List[str]:
        """
        Retrieves image file paths from a directory associated with a product ID.

        This method is designed to locate a specific directory linked to the given
        `record_id` (e.g., a product or item ID) and then collect all image
        file paths found within that directory.

        Args:
            record_id (int): The unique identifier of the product or item for which
                             images are to be retrieved.

        Returns:
            List[str]: A list of absolute file paths to the images found in the
                       corresponding directory. Returns an empty list if no images
                       are found or if the directory does not exist.
        """
        product = self.read(record_id)
        if not product or not getattr(product, "image_dir", None):
            return []
        return self.get_images_by_path(product.image_dir)

    def get_images_by_path(self, path: str) -> List[str]:
        """
        Retrieves image file paths from a specified directory.

        This method scans the directory provided by `path` and collects all
        image file paths found directly within it. It does not recurse into
        subdirectories.

        Args:
            path (str): The absolute or relative path to the directory from which
                        to retrieve image files.

        Returns:
            List[str]: A list of absolute file paths to the images found in the
                       specified directory. Returns an empty list if no images
                       are found or if the directory does not exist.
        """
        if not path or not os.path.isdir(path):
            return []
        image_extensions = (
            "*.png",
            "*.jpg",
            "*.jpeg",
            "*.bmp",
            "*.gif",
            "*.webp",
            "*.PNG",
            "*.JPG",
            "*.JPEG",
        )
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(path, ext)))
        return sorted(image_files)

    def get_all_pid(self):
        """
        Efficiently retrieves all product IDs (pid) directly from the database using SQL.
        Returns:
            List[str]: List of all product IDs.
        """
        if not self._db.isOpen():
            print(f"[{self.__class__.__name__}.get_all_pid] Database is not open.")
            return []
        query = QSqlQuery(self._db)
        # Assuming the table name is available as self.model.tableName()
        sql = f"SELECT pid FROM {self.model.tableName()}"
        if not query.exec(sql):
            print(
                f"[{self.__class__.__name__}.get_all_pid] Query failed: {query.lastError().text()}"
            )
            return []
        pids = []
        while query.next():
            pid = query.value(0)
            if pid is not None:
                pids.append(pid)
        return pids

    def get_random(self, transaction_type: str):
        if not self._db.isOpen():
            print(f"[{self.__class__.__name__}.get_random] Database is not open.")
            return None

        query = QSqlQuery(self._db)
        # Giả sử cột transaction_type lưu đúng kiểu dữ liệu, có thể cần chỉnh lại tên cột nếu khác
        sql = f"""
            SELECT id FROM {self.model.tableName()}
            WHERE transaction_type = ? AND status = 1
            ORDER BY RANDOM() LIMIT 1
        """
        query.prepare(sql)
        query.addBindValue(transaction_type)

        if not query.exec():
            print(
                f"[{self.__class__.__name__}.get_random] Query failed: {query.lastError().text()}"
            )
            return None

        if query.next():
            record_id = query.value(0)
            return self.read(record_id)
        return None


class RealEstateTemplateService(BaseService):
    DATA_TYPE = RealEstateTemplateType

    def __init__(self, model: RealEstateTemplateModel):
        if not isinstance(model, RealEstateTemplateModel):
            raise TypeError(
                "model must be an instance of RealEstateTemplateModel or its subclass."
            )
        super().__init__(model)

    def create(self, payload: RealEstateTemplateType) -> bool:
        return super().create(payload)

    def read(self, record_id: int) -> Optional[RealEstateTemplateType]:
        return super().read(record_id)

    def read_all(self) -> List[RealEstateTemplateType]:
        return super().read_all()

    def update(self, record_id: int, payload: RealEstateTemplateType) -> bool:
        return super().update(record_id, payload)

    def delete(self, record_id: int) -> bool:
        return super().delete(record_id)

    def delete_multiple(self, record_ids: List[int]):
        return super().delete_multiple(record_ids)

    def import_data(self, payload: List[RealEstateTemplateType]):
        return super().import_data(payload)

    def get_random(self, part: str, transaction_type: str, category: str) -> str:
        """
        Retrieves a random template value based on part, transaction_type, and category.
        """
        if not self._db.isOpen():
            print(f"[{self.__class__.__name__}.get_random] Database is not open.")
            return ""

        query_obj = QSqlQuery(self._db)  # Khởi tạo QSqlQuery với đối tượng QSqlDatabase
        query = f"""
            SELECT value FROM {TABLE_REAL_ESTATE_TEMPLATE}
            WHERE (? = '' OR part = ?)
            AND (? = '' OR transaction_type = ?)
            AND (? = '' OR category = ?)
            AND is_default = 0
            ORDER BY RANDOM() LIMIT 1
        """
        query_obj.prepare(query)  # Chuẩn bị truy vấn

        # Binding các tham số
        query_obj.addBindValue(part)
        query_obj.addBindValue(part)
        query_obj.addBindValue(transaction_type)
        query_obj.addBindValue(transaction_type)
        query_obj.addBindValue(category)
        query_obj.addBindValue(category)

        if not query_obj.exec():  # Thực thi truy vấn
            print(
                f"[{self.__class__.__name__}.get_random] Query failed: {query_obj.lastError().text()}"
            )
            return ""

        if query_obj.next():  # Di chuyển con trỏ đến hàng đầu tiên (nếu có)
            return query_obj.value(0)  # Lấy giá trị của cột đầu tiên (value)
        return ""  # Trả về chuỗi rỗng nếu không tìm thấy

    def get_default(self, part: str, transaction_type: str, category: str) -> str:
        """
        Retrieves the default template value (is_default = 1) for a given
        part, transaction_type, and category.
        """
        if not self._db.isOpen():
            print(f"[{self.__class__.__name__}.get_default] Database is not open.")
            return ""

        query_obj = QSqlQuery(self._db)  # Khởi tạo QSqlQuery với đối tượng QSqlDatabase
        query = f"""
            SELECT value from {TABLE_REAL_ESTATE_TEMPLATE}
            WHERE (? = '' OR part = ?)
            AND (? = '' OR transaction_type = ?)
            AND (? = '' OR category = ?)
            AND is_default = 1
        """
        query_obj.prepare(query)  # Chuẩn bị truy vấn

        # Binding các tham số
        query_obj.addBindValue(part)
        query_obj.addBindValue(part)
        query_obj.addBindValue(transaction_type)
        query_obj.addBindValue(transaction_type)
        query_obj.addBindValue(category)
        query_obj.addBindValue(category)

        if not query_obj.exec():  # Thực thi truy vấn
            print(
                f"[{self.__class__.__name__}.get_default] Query failed: {query_obj.lastError().text()}"
            )
            return ""

        if query_obj.next():  # Di chuyển con trỏ đến hàng đầu tiên (nếu có)
            return query_obj.value(0)  # Lấy giá trị của cột đầu tiên (value)
        return ""  # Trả về chuỗi rỗng nếu không tìm thấy

    def set_default_template(self, record_id: int) -> bool:
        """
        Sets a specific RealEstateTemplate record as the default template and
        unsets others matching its part, transaction_type, and category.

        Args:
            record_id (int): The ID of the record to be set as the new default.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        if not self._db.isOpen():
            print(
                f"[{self.__class__.__name__}.set_default_template] Database is not open."
            )
            return False

        try:
            with transaction(
                self._db
            ) as db_conn:  # Use the QSqlDatabase object directly
                query = QSqlQuery(db_conn)  # Create QSqlQuery with the connection

                # 1. Get information (part, transaction_type, category) of the target record
                select_target_query = f"""
                    SELECT part, transaction_type, category
                    FROM {TABLE_REAL_ESTATE_TEMPLATE}
                    WHERE id = ?
                """
                query.prepare(select_target_query)
                query.addBindValue(record_id)

                if not query.exec():
                    print(
                        f"[{self.__class__.__name__}.set_default_template] Failed to fetch target record: {query.lastError().text()}"
                    )
                    raise RuntimeError("Failed to fetch target record.")

                if not query.next():  # Move to the first (and only) result
                    print(
                        f"[{self.__class__.__name__}.set_default_template] Record with ID {record_id} not found."
                    )
                    return False

                part = query.value("part")
                transaction_type = query.value("transaction_type")
                category = query.value("category")

                # 2. Unset (is_default = 0) all other records with matching part, transaction_type, category
                update_others_query = f"""
                    UPDATE {TABLE_REAL_ESTATE_TEMPLATE}
                    SET is_default = 0, updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now')
                    WHERE part = ?
                    AND transaction_type = ?
                    AND category = ?
                    AND id != ?
                """
                query.prepare(update_others_query)
                query.addBindValue(part)
                query.addBindValue(transaction_type)
                query.addBindValue(category)
                query.addBindValue(record_id)

                if not query.exec():
                    print(
                        f"[{self.__class__.__name__}.set_default_template] Failed to unset other defaults: {query.lastError().text()}"
                    )
                    raise RuntimeError("Failed to unset other defaults.")

                # 3. Set the target record (record_id) to is_default = 1
                update_target_query = f"""
                    UPDATE {TABLE_REAL_ESTATE_TEMPLATE}
                    SET is_default = 1, updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now')
                    WHERE id = ?
                """
                query.prepare(update_target_query)
                query.addBindValue(record_id)

                if not query.exec():
                    print(
                        f"[{self.__class__.__name__}.set_default_template] Failed to set target as default: {query.lastError().text()}"
                    )
                    raise RuntimeError("Failed to set target as default.")

                # Re-select the model to refresh the view (optional, but good practice if model is connected to a view)
                self.model.select()
            return True  # Transaction committed successfully

        except Exception as e:
            # The 'transaction' context manager already handles rollback and prints
            # so we just need to catch, print a specific message, and return False.
            print(
                f"[{self.__class__.__name__}.set_default_template] Operation failed: {e}"
            )
            self.model.select()  # Refresh model to show original state if transaction failed
            return False


class MiscProductService(BaseService):
    DATA_TYPE = MiscProductType

    def __init__(self, model: MiscProductModel):
        if not isinstance(model, MiscProductModel):
            raise TypeError(
                "model must be an instance of MiscProductModel or its subclass."
            )
        super().__init__(model)

    def create(self, payload: MiscProductModel) -> bool:
        return super().create(payload)

    def read(self, record_id: int) -> Optional[MiscProductModel]:
        return super().read(record_id)

    def read_all(self) -> List[MiscProductModel]:
        return super().read_all()

    def update(self, record_id: int, payload: MiscProductModel) -> bool:
        return super().update(record_id, payload)

    def delete(self, record_id: int) -> bool:
        return super().delete(record_id)

    def delete_multiple(self, record_ids: List[int]):
        return super().delete_multiple(record_ids)

    def import_data(self, payload: List[MiscProductModel]):
        return super().import_data(payload)

    def toggle_status(self, record_id: int) -> bool:
        product = self.read(record_id)
        if product is None:
            print(
                f"[{self.__class__.__name__}.toggle_status] Product with record_id '{record_id}' not found."
            )
            return False

        current_status = product.status
        if current_status == 0:
            new_status = 1
        elif current_status == 1:
            new_status = 0
        else:
            print(
                f"[{self.__class__.__name__}.toggle_status] Unexpected status value for product ID '{record_id}': {current_status}. Cannot toggle."
            )
            return False

        product.status = new_status
        update_success = self.update(product.id, product)
        if update_success:
            # print(
            #     f"[{self.__class__.__name__}.toggle_status] Successfully toggled status for product ID '{record_id}' to {new_status}."
            # )
            return True
        else:
            print(
                f"[{self.__class__.__name__}.toggle_status] Failed to update status for product ID '{record_id}'."
            )
            return False

    def read_by_pid(self, pid: str) -> Optional[MiscProductType]:
        return self._find_by_model_index(find_method_name="find_row_by_pid", value=pid)
