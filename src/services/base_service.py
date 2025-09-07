# src/services/base_service.py

import sys
from datetime import datetime
from typing import List, Any, Dict, Optional, Type
from contextlib import contextmanager
from PyQt6.QtCore import Qt, QVariant
from PyQt6.QtSql import QSqlDatabase, QSqlRecord, QSqlTableModel
from dataclasses import fields
from src.models.base_model import BaseModel


@contextmanager
def transaction(db: QSqlDatabase):
    """
    Context manager for managing database transactions.
    Ensures rollback on error or failed commit.
    """
    # Attempt to start the transaction
    if not db.transaction():
        error_msg = (
            f"[{transaction.__name__}] Failed to start transaction. Error: {db.lastError().text()}"
            if db.isOpen()
            else f"[{transaction.__name__}] Database is not open."
        )
        print(f"ERROR: {error_msg}")  # Keep print for critical error
        raise RuntimeError(error_msg)
    try:
        yield db  # Yield control to the 'with' block
        # Attempt to commit the transaction
        if not db.commit():
            error_msg = (
                f"[{transaction.__name__}] Failed to commit transaction. Error: { db.lastError().text()}"
                if db.isOpen()
                else f"[{transaction.__name__}] Database not open."
            )
            print(f"ERROR: {error_msg}")  # Keep print for critical error
            if (
                db.isOpen() and db.transaction()
            ):  # Check if transaction is still active before rollback
                db.rollback()  # Attempt to roll back if commit fails
                print(
                    f"WARNING: [{transaction.__name__}] Attempted rollback after commit failure."
                )  # Keep print
            raise RuntimeError(error_msg)
        # print(f"INFO: [{transaction.__name__}] Transaction committed successfully.") # Removed print for clean
    except Exception as e:
        print(
            f"ERROR: [{transaction.__name__}] Exception during transaction block: {e}"
        )  # Keep print
        if (
            db.isOpen() and db.transaction()
        ):  # Check if transaction is still active before rollback
            if db.rollback():
                print(
                    f"INFO: [{transaction.__name__}] Transaction rolled back due to exception."
                )  # Keep print
            else:
                print(
                    f"WARNING: [{transaction.__name__}] Failed to rollback transaction due to exception. Error: {db.lastError().text()}"
                )  # Keep print
        raise  # Re-raise the exception to be caught by the calling function (e.g., import_data)


class BaseService:
    DATA_TYPE: Optional[Type[Any]] = None

    def __init__(self, model: BaseModel):
        if not isinstance(model, BaseModel):
            raise TypeError("model mus be an instance of BaseModel or its subclass.")
        self.model = model
        self._db = model.database()
        # print(self._db.isOpen())
        # print()

        if not self._db.isValid() or not self._db.isOpen():
            warning_msg = f"[{self.__class__.__name__}.__init__] Warning: db connection '{self._db.connectionName()}' is not valid or not open."
            print(warning_msg)

        self._column_names: List[str] = []
        for i in range(self.model.columnCount()):
            col_name = self.model.headerData(
                i,
                Qt.Orientation.Horizontal,
                Qt.ItemDataRole.DisplayRole,
            )
            if isinstance(col_name, str):
                self._column_names.append(col_name)
            else:
                warning_msg = f"[{self.__class__.__name__}.__init__] Warning: Column header at index {i} is not a string: {col_name}."
                print(warning_msg)
        if self.model.fieldIndex("id") == -1:
            warning_msg = f"[{self.__class__.__name__}.__init__] Warning: Table '{self.model.tableName()}' must have an 'id' column for some operations."
            print(warning_msg)
        if self.DATA_TYPE is not None:
            dataclass_fields = [f.name for f in fields(self.DATA_TYPE)]
            for field_name in dataclass_fields:
                if self.model.fieldIndex(field_name) == -1:
                    warning_msg = f"[{self.__class__.__name__}.__init__] Warning: Field '{field_name}' from DATA_TYPE '{self.DATA_TYPE.__name__}' not found as a column in table '{self.model.tableName()}'."
                    print(warning_msg)

    # ========================================================================
    # Helper method
    # ========================================================================
    def _map_record_to_datatype(self, record: QSqlRecord) -> Optional[Any]:
        """Helper to map a QSqlRecord to an instance of the specific DATA_TYPE dataclass."""
        if self.DATA_TYPE is None:
            info_msg = f"[{self.__class__.__name__}._map_record_to_datatype] DATA_TYPE is not set. Cannot map record. => return None"
            print(info_msg)
            return None
        data: Dict[str, Any] = {}
        for i in range(record.count()):
            field_name = record.fieldName(i)
            data[field_name] = record.value(i)
        try:
            dataclass_field_names = {f.name for f in fields(self.DATA_TYPE)}
            valid_data = {field: data.get(field) for field in dataclass_field_names}
            return self.DATA_TYPE(**valid_data)
        except Exception as e:
            error_msg = f"[{self.__class__.__name__}._map_record_to_datatype] Error: converting dict to {self.DATA_TYPE.__name__}: {e} -- Data: {data}"
            print(error_msg)
            return None

    def _fill_row_from_payload(self, row: int, payload: Any):
        """Helper to set data in a model row from a DATA_TYPE payload."""
        if self.DATA_TYPE is None:
            info_msg = f"[{self.__class__.__name__}._fill_row_from_payload] DATA_TYPE is not set. Cannot fill row. => return False"
            print(info_msg)
            return False
        if not isinstance(payload, self.DATA_TYPE):
            info_msg = f"[{self.__class__.__name__}._fill_row_from_payload] Invalid payload type. Expected {self.DATA_TYPE.__name__}, got {type(payload).__name__}. => return False"
            print(info_msg)
            return False
        fields_set_count = 0
        for col_index in range(self.model.columnCount()):
            field_name = self.model.headerData(
                col_index,
                Qt.Orientation.Horizontal,
                Qt.ItemDataRole.DisplayRole,
            )
            if not isinstance(field_name, str):
                continue
            if hasattr(payload, field_name):
                value = getattr(payload, field_name)
                if (
                    field_name == "created_at" or field_name == "updated_at"
                ) and value is None:
                    value = str(datetime.now())
            if field_name != "id":
                index = self.model.index(row, col_index)
                if index.isValid():
                    set_success = self.model.setData(
                        index,
                        value,
                        Qt.ItemDataRole.EditRole,
                    )
                    if set_success:
                        fields_set_count += 1
                    else:
                        warning_msg = f"[{self.__class__.__name__}._fill_row_from_payload] Warning: setData returned False for col '{field_name}' (index {col_index}) at row {row}."
                        print(warning_msg)
                else:
                    warning_msg = f"[{self.__class__.__name__}._fill_row_from_payload] Warning: Invalid index for field '{field_name}' (col index {col_index}) at row {row}. Data not set."
                    print(warning_msg)
        return fields_set_count > 0

    # ========================================================================
    # CRUD method
    # ========================================================================
    def create(self, payload: Any) -> bool:
        """
        Creates a new record from a DATA_TYPE payload using the model.
        Returns True on success, False on failure.
        Automatically sets created_at and updated_at if they are None in payload
        and exist as columns.
        """
        if self.DATA_TYPE is None:
            info_msg = f"[{self.__class__.__name__}.create] DATA_TYPE is not set. Cannot create. => return False"
            print(info_msg)
            return False
        if not isinstance(payload, self.DATA_TYPE):
            info_msg = f"[{self.__class__.__name__}.create] Invalid payload type. Expected {self.DATA_TYPE.__name__}, got {type(payload).__name__}. => return False"
            print(info_msg)
            return False
        if not self._db.isOpen():
            info_msg = f"[{self.__class__.__name__}.create] Database is not open. => return False"
            print(info_msg)
            return False

        row = self.model.rowCount()
        if not self.model.insertRow(row):
            error_msg = f"[{self.__class__.__name__}.create] Failed to insert row into model buffer. Error: {self.model.lastError().text()}. => return False"
            print(error_msg)
            return False
        # --- Handle created_at and updated_at if None in payload ---
        self._fill_row_from_payload(row, payload=payload)

        if self.model.submitAll():
            self.model.select()
            return True
        else:
            error_msg = f"[{self.__class__.__name__}.create] Failed to submit changes to database. Error: {self.model.lastError().text()}. => return False"
            print(error_msg)
            self.model.revertAll()
            return False

    def read(self, record_id: int) -> Optional[Any]:
        """Reads a record by ID using the model's find method.
        Returns an instance of DATA_TYPE or None if not found."""
        if self.DATA_TYPE is None:
            info_msg = f"[{self.__class__.__name__}.read] DATA_TYPE is not set. Cannot read. => return None"
            print(info_msg)
            return None
        if not self._db.isOpen():
            info_msg = (
                f"[{self.__class__.__name__}.read] Database is not open. => return None"
            )
            print(info_msg)
            return None
        row = self.model.get_row_by_id(record_id)
        if row != -1:
            record = self.model.record(row)
            return self._map_record_to_datatype(record)
        return None

    def read_all(self) -> List[Any]:
        """Reads all records currently loaded in the model.
        Returns a list of DATA_TYPE instances."""
        if self.DATA_TYPE is None:
            info_msg = f"[{self.__class__.__name__}.read] DATA_TYPE is not set. Cannot read. => return []"
            print(info_msg)
            return []
        if not self._db.isOpen():
            info_msg = (
                f"[{self.__class__.__name__}.read] Database is not open. => return []"
            )
            print(info_msg)
            return []
        while self.model.canFetchMore():
            self.model.fetchMore()
        results: List[Any] = []
        for row in range(self.model.rowCount()):
            record = self.model.record(row)
            data_instance = self._map_record_to_datatype(record)
            if data_instance is not None:
                results.append(data_instance)
        return results

    def update(self, record_id: Any, payload: Any) -> bool:
        """Updates an existing record by ID from a DATA_TYPE payload using the model.
        Updates only the fields present (not None) in the payload.
        Automatically sets updated_at if it's None in payload and exists as a column.
        Returns True on success, False on failure."""
        if self.DATA_TYPE is None:
            info_msg = f"[{self.__class__.__name__}.update] DATA_TYPE is not set. Cannot update. => return False"
            print(info_msg)
            return False
        if not isinstance(payload, self.DATA_TYPE):
            info_msg = f"[{self.__class__.__name__}.update] Invalid payload type. Expected {self.DATA_TYPE.__name__}, got {type(payload).__name__}. => return False"
            print(info_msg)
            return False
        if not self._db.isOpen():
            info_msg = f"[{self.__class__.__name__}.update] Database is not open. => return False"
            print(info_msg)
            return False
        row = self.model.get_row_by_id(record_id)
        if row == -1:
            info_msg = f"[{self.__class__.__name__}.update] Record with id {record_id} not found in model. => return False"
            print(info_msg)
            return False

        payload.updated_at = str(datetime.now())
        fields_updated_count = 0
        for col_index in range(self.model.columnCount()):
            field_name = self.model.headerData(
                col_index,
                Qt.Orientation.Horizontal,
                Qt.ItemDataRole.DisplayRole,
            )
            if not isinstance(field_name, str):
                continue
            if hasattr(payload, field_name):
                value = getattr(payload, field_name)
                if value is not None:
                    index = self.model.index(row, col_index)
                    if index.isValid():
                        set_success = self.model.setData(
                            index,
                            value,
                            Qt.ItemDataRole.EditRole,
                        )
                        if set_success:
                            fields_updated_count += 1
                        else:
                            warning_msg = f"[{self.__class__.__name__}.update] WARNING: setData returned False for col '{field_name}' (index {col_index}) at row {row}."
                            print(warning_msg)
                    else:
                        warning_msg = f"[{self.__class__.__name__}.update] WARNING: Invalid index for field '{field_name}' (col index {col_index}) at row {row}. Data not set."
                        print(warning_msg)

        if fields_updated_count > 0 and self.model.submitAll():
            self.model.select()
            # print("select")
            return True
        elif fields_updated_count == 0:
            info_msg = f"[{self.__class__.__name__}.update] No fields provided in payload to update for id: {record_id}."
            print(info_msg)
            return True
        else:
            info_msg = f"[{self.__class__.__name__}.update] Failed to submit update. Error: {self.model.lastError().text()}"
            self.model.revertAll()
            return False

    def delete(self, record_id: Any) -> bool:
        """Deletes a single record by ID using the model.
        Returns True on success, False on failure."""
        if not self._db.isOpen():
            info_msg = f"[{self.__class__.__name__}.delete] Database is not open. => return False"
            print(info_msg)
            return False
        row = self.model.get_row_by_id(record_id)
        if row == -1:
            info_msg = f"[{self.__class__.__name__}.delete] Record with id {record_id} not found in model for deletion."
            print(info_msg)
            return False
        if not self.model.removeRow(row):
            info_msg = f"[{self.__class__.__name__}.delete] Failed to remove row {row} from model buffer. Error: {self.model.lastError().text()}"
            print(info_msg)
            return False
        if self.model.submitAll():
            self.model.select()
            info_msg = f"[{self.__class__.__name__}.delete] Deleted row {row} from model buffer"
            print(info_msg)
            return True
        else:
            info_msg = f"[{self.__class__.__name__}.delete] Failed to submit deletion. Error: {self.model.lastError().text()}"
            print(info_msg)
            self.model.revertAll()
            return False

    def delete_multiple(self, record_ids: List[Any]) -> bool:
        """Deletes multiple records by IDs using the model within a transaction.
        Returns True on success, False on failure (any failure causes rollback)."""
        if not self._db.isOpen():
            info_msg = f"[{self.__class__.__name__}.update] Database is not open. => return False"
            print(info_msg)
            return False
        if not record_ids:
            info_msg = (
                f"[{self.__class__.__name__}.delete_multiple] No record IDs provided."
            )
            print(info_msg)
            return False
        rows_to_delete = sorted(
            [
                self.model.get_row_by_id(db_id)
                for db_id in record_ids
                if self.model.get_row_by_id(db_id) != -1
            ],
            reverse=True,
        )
        if not rows_to_delete:
            info_msg = f"[{self.__class__.__name__}.delete_multiple] None of the provided IDs were found in the model."
            print(info_msg)
            return False
        try:
            with transaction(self._db):
                for row in rows_to_delete:
                    if not self.model.removeRow(row):
                        error_msg = f"[{self.__class__.__name__}.delete_multiple] Failed to remove row {row} from model buffer. Error: {self.model.lastError().text()}"
                        print(error_msg)
                        raise RuntimeError(error_msg)
                if not self.model.submitAll():
                    error_msg = f"[{self.__class__.__name__}.delete_multiple] Failed to submit deletions. Error: {self.model.lastError().text()}"
                    print(error_msg)
                    raise RuntimeError(error_msg)
            self.model.select()
            return True
        except Exception as e:
            exception_msg = (
                f"[{self.__class__.__name__}.delete_multiple] Transaction failed: {e}"
            )
            print(exception_msg)
            self.model.revertAll()
            self.model.select()
            return False

    def import_data(self, payload: List[Any]) -> bool:
        """
        Imports multiple records from a list of DATA_TYPE payloads using the model
        within a transaction.
        Returns True on success (all imported), False on failure (rollback).
        Automatically sets created_at and updated_at if they exist as columns.
        """
        if self.DATA_TYPE is None:
            print(
                f"WARNING: [{self.__class__.__name__}.import_data] DATA_TYPE chưa được đặt. Không thể nhập."
            )
            return False
        if not isinstance(payload, list) or not all(
            isinstance(item, self.DATA_TYPE) for item in payload
        ):
            print(
                f"ERROR: [{self.__class__.__name__}.import_data] Kiểu danh sách payload không hợp lệ. Mong đợi danh sách của {self.DATA_TYPE.__name__}."
            )
            return False
        if not payload:
            print(
                f"INFO: [{self.__class__.__name__}.import_data] Danh sách payload trống được cung cấp, không có dữ liệu để nhập."
            )
            return True  # Đã hoàn thành thành công (không làm gì) cho payload trống
        if not self._db.isOpen():
            print(
                f"ERROR: [{self.__class__.__name__}.import_data] Kết nối cơ sở dữ liệu không mở."
            )
            return False
        try:
            # --- SỬA LỖI QUAN TRỌNG: Đồng bộ hóa QSqlTableModel trước khi chèn hàng loạt ---
            # Gọi select() ở đây đảm bảo bộ nhớ đệm nội bộ của model được đồng bộ
            # với trạng thái thực tế của cơ sở dữ liệu, có thể ngăn insertRow bị lỗi
            # một cách khó hiểu sau vài lần chèn, hoặc nếu có các thay đổi/lỗi chưa được commit.
            self.model.select()

            # --- Gỡ lỗi bổ sung / Xác thực ---
            # if not self.model.insertRow():
            #     error_msg = f"[{self.__class__.__name__}.import_data] QSqlTableModel không thể chèn hàng. Kiểm tra quyền của bảng hoặc trạng thái model. Lỗi cuối cùng: {self.model.lastError().text()}"
            #     print(f"ERROR: {error_msg}")
            #     return False

            with transaction(self._db):
                for i, record_instance in enumerate(payload):
                    # Chuẩn bị dữ liệu để chèn (xử lý ID và dấu thời gian)
                    # Đối với bản ghi mới, ID nên là None cho các cột tự động tăng
                    if hasattr(record_instance, "id"):
                        record_instance.id = None

                    # Xử lý dấu thời gian (created_at và updated_at) nếu chúng tồn tại trong dataclass
                    current_time_str = str(
                        datetime.now()
                    )  # Lấy dấu thời gian hiện tại dưới dạng chuỗi

                    if (
                        hasattr(record_instance, "created_at")
                        and self.model.record().indexOf("created_at") != -1
                    ):
                        # Chỉ đặt created_at nếu nó hiện là None (đối với bản ghi mới)
                        if record_instance.created_at is None:
                            record_instance.created_at = current_time_str
                    if (
                        hasattr(record_instance, "updated_at")
                        and self.model.record().indexOf("updated_at") != -1
                    ):
                        # Luôn cập nhật updated_at khi nhập
                        record_instance.updated_at = current_time_str

                    # Chèn một hàng trống mới vào bộ nhớ đệm của model
                    # rowCount() cung cấp chỉ mục nơi một hàng mới sẽ được thêm vào.
                    row_index_for_new_item = self.model.rowCount()

                    print(
                        f"DEBUG: [{self.__class__.__name__}.import_data] Item {i+1}: Đang cố gắng chèn hàng tại chỉ mục {row_index_for_new_item}..."
                    )  # Thêm debug

                    if not self.model.insertRow(row_index_for_new_item):
                        error_text = self.model.lastError().text()
                        error_msg = (
                            f"[{self.__class__.__name__}.import_data] Thất bại khi chèn hàng {row_index_for_new_item} "
                            f"vào bộ nhớ đệm của model cho item {i+1} (PID: {getattr(record_instance, 'pid', 'N/A')}). "
                            f"Lỗi Model: {error_text if error_text else 'Không có thông báo lỗi cụ thể từ model.'}"
                        )
                        print(f"ERROR: {error_msg}")
                        raise RuntimeError(error_msg)

                    # Điền hàng vừa chèn vào bộ nhớ đệm của model bằng dữ liệu từ payload
                    self._fill_row_from_payload(row_index_for_new_item, record_instance)
                    print(
                        f"DEBUG: [{self.__class__.__name__}.import_data] Item {i+1}: Hàng {row_index_for_new_item} đã được điền thành công trong bộ nhớ đệm."
                    )  # Thêm debug

                # --- Gửi tất cả các thay đổi đã đệm vào cơ sở dữ liệu sau khi tất cả các hàng được chèn ---
                print(
                    f"DEBUG: [{self.__class__.__name__}.import_data] Đang cố gắng submit tất cả {len(payload)} hàng đã đệm..."
                )  # Thêm debug
                if not self.model.submitAll():
                    error_text = self.model.lastError().text()
                    error_msg = (
                        f"[{self.__class__.__name__}.import_data] Thất bại khi submit tất cả {len(payload)} "
                        f"các lần chèn vào cơ sở dữ liệu. Lỗi Cơ sở dữ liệu: {error_text if error_text else 'Không có thông báo lỗi cụ thể từ model.'}"
                    )
                    print(f"ERROR: {error_msg}")
                    raise RuntimeError(error_msg)

            # Nếu giao dịch thành công, làm mới model để hiển thị dữ liệu mới được thêm từ DB
            self.model.select()
            print(
                f"INFO: [{self.__class__.__name__}.import_data] Đã nhập thành công {len(payload)} bản ghi."
            )
            return True

        except (
            RuntimeError
        ) as e:  # Bắt RuntimeError cụ thể từ các lần raise rõ ràng của chúng ta
            print(
                f"ERROR: [{self.__class__.__name__}.import_data] Giao dịch nhập thất bại: {e}"
            )
            self.model.revertAll()  # Hoàn tác mọi thay đổi đang chờ xử lý trong bộ nhớ đệm của model
            self.model.select()  # Làm mới model từ DB để xóa mọi trạng thái lỗi
            return False
        except (
            Exception
        ) as e:  # Bắt bất kỳ ngoại lệ không mong đợi nào khác trong quá trình nhập
            print(
                f"CRITICAL ERROR: [{self.__class__.__name__}.import_data] Đã xảy ra lỗi không mong đợi: {e}",
                file=sys.stderr,
            )  # In ra stderr
            self.model.revertAll()  # Hoàn tác mọi thay đổi đang chờ xử lý
            self.model.select()  # Làm mới model
            return False

    def _find_by_model_index(self, find_method_name: str, value: Any) -> Optional[Any]:
        """Helper to find a single record based on a custom find method in the model.
        Intended for use by subclasses to implement methods like find_by_uid, find_by_email.
        find_method_name: The name of the method in the model (e.g., 'find_row_by_uid').
        value: The value to pass to the model's find method."""

        if self.DATA_TYPE is None:
            info_msg = f"[{self.__class__.__name__}._find_one_by_model_index] DATA_TYPE is not set. Cannot find record."
            print(info_msg)
            return None

        find_method = getattr(self.model, find_method_name, None)
        if find_method is None or not callable(find_method):
            info_msg = f"[{self.__class__.__name__}._find_one_by_model_index] Error: Model does not have a callable method named '{find_method_name}'."
            return None
        row = find_method(value)
        if row != -1:
            record = self.model.record(row)
            return self._map_record_to_datatype(record)
        return None
