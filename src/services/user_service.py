# src/services/user_service.py
import os
import shutil
from fake_useragent import UserAgent
from typing import Optional, List
from src.services.base_service import BaseService
from src.models.user_model import UserModel, UserListedProductModel
from src.my_types import UserType, UserListedProductType
import uuid


class UserService(BaseService):
    DATA_TYPE = UserType

    def __init__(self, model: UserModel):
        if not isinstance(model, UserModel):
            raise TypeError("model must be an instance of UserModel or its subclass.")
        super().__init__(model)
        self.listed_product_service = None

    def create(self, payload: UserType) -> bool:
        ua_desktop = UserAgent(os="Mac OS X")
        ua_mobile = UserAgent(os="iOS")
        payload.mobile_ua = ua_mobile.random
        payload.desktop_ua = ua_desktop.random
        payload.my_id = str(uuid.uuid4())
        return super().create(payload)

    def read(self, record_id: int) -> Optional[UserType]:
        return super().read(record_id)

    def read_all(self) -> List[UserType]:
        return super().read_all()

    def update(self, record_id: int, payload: UserType) -> bool:
        return super().update(record_id, payload)

    def delete(self, udd_container, record_id: int) -> bool:
        if not os.path.exists(os.path.abspath(udd_container)):
            info_msg = f"[{self.__class__.__name__}.delete] Failed get udd container."
            print(info_msg)
            return False
        user_data = self.read(record_id=record_id)
        udd_path = os.path.join(os.path.abspath(udd_container), user_data.my_id)
        if os.path.exists(udd_path):
            shutil.rmtree(udd_path)
            print(f"Deleted {udd_path}")
        return super().delete(record_id)

    def delete_multiple(self, record_ids):
        # self.listed_product_service.delete_multiple(record_ids)
        raise Exception("Undefined")
        return super().delete_multiple(record_ids)

    def import_data(self, payload: List[UserType]):
        return super().import_data(payload)

    def find_by_uid(self, uid: str) -> Optional[UserType]:
        return self._find_by_model_index(find_method_name="find_row_by_uid", value=uid)

    def update_status(self, record_id: int, new_status: int) -> bool:
        if new_status not in [0, 1]:
            raise ValueError(
                f"Invalid status value: {new_status}. Status must be 0 or 1."
            )
        user = self.read(record_id)
        user.status = new_status
        update_success = self.update(record_id, user)
        if update_success:
            # print(
            #     f"[{self.__class__.__name__}.update_status] Successfully toggled status for user ID '{record_id}' to {new_status}."
            # )
            return True
        else:
            # print(
            #     f"[{self.__class__.__name__}.update_status] Failed to update status for user ID '{record_id}'."
            # )
            return False

    def get_uids_by_record_ids(self, record_ids: List[int]) -> List[str]:
        return self.model.get_uids_by_record_ids(record_ids)

    def handle_new_desktop_ua(self) -> str:
        ua_desktop = UserAgent(os="Mac OS X")
        return ua_desktop.random

    def handle_new_mobile_ua(self) -> str:
        ua_mobile = UserAgent(os="iOS")
        return ua_mobile.random


class UserListedProductService(BaseService):
    DATA_TYPE = UserListedProductType

    def __init__(self, model: UserListedProductModel):
        if not isinstance(model, UserListedProductModel):
            raise TypeError(
                "model must be an instance of UserListedProductType or its subclass."
            )
        super().__init__(model)

    def create(self, payload: UserListedProductType):
        return super().create(payload)

    def read(self, record_id: int) -> UserListedProductType:
        return super().read(record_id)

    def read_all(self) -> List[UserListedProductType]:
        return super().read_all()

    def delete(self, record_id: int) -> bool:
        return super().delete(record_id)

    def delete_multiple(self, record_ids):
        return super().delete_multiple(record_ids)

    def read_by_user_id(self, user_id: int) -> List[UserListedProductType]:
        if self.DATA_TYPE is None:
            info_msg = f"[{self.__class__.__name__}.read_by_user_id] DATA_TYPE is not set. Cannot read. => return None"
            print(info_msg)
            return None
        if not self._db.isOpen():
            info_msg = f"[{self.__class__.__name__}.read_by_user_id] Database is not open. => return None"
            print(info_msg)
            return None
        rows = self.model.get_rows_by_user_id(user_id)
        results = []
        for row in rows:
            record = self.model.record(row)
            results.append(self._map_record_to_datatype(record))
        return results

    def shift_record_by_user_id(self, user_id: int) -> Optional[UserListedProductType]:
        if self.DATA_TYPE is None:
            info_msg = f"[{self.__class__.__name__}.shift_record_by_user_id] DATA_TYPE is not set. Cannot read. => return None"
            print(info_msg)
            return None
        if not self._db.isOpen():
            info_msg = f"[{self.__class__.__name__}.shift_record_by_user_id] Database is not open. => return None"
            print(info_msg)
            return None
        rows_to_remove = self.model.get_rows_by_user_id(user_id)
        if not rows_to_remove:
            info_msg = f"[{self.__class__.__name__}.shift_record_by_user_id] No record found for user ID {user_id}."
            print(info_msg)
            return None
        row_index_to_remove = rows_to_remove[0]
        try:
            record_to_return = self.model.record(row_index_to_remove)
            removed_data_instance = self._map_record_to_datatype(record_to_return)
            if removed_data_instance is None:
                error_msg = f"[{self.__class__.__name__}.shift_record_by_user_id] Failed to map record to DATA_TYPE for row {row_index_to_remove}."
                print(error_msg)
                return None

        except IndexError:
            error_msg = f"[{self.__class__.__name__}.shift_record_by_user_id] Invalid row index {row_index_to_remove} after finding rows."
            print(error_msg)
            return None
        if not self.model.removeRow(row_index_to_remove):
            error_msg = f"[{self.__class__.__name__}.shift_record_by_user_id] Failed to remove row {row_index_to_remove} from model buffer. Error: {self.model.lastError().text()}"
            print(error_msg)
            self.model.revertAll()
            return None

        if self.model.submitAll():
            return removed_data_instance
        else:
            error_msg = f"[{self.__class__.__name__}.shift_record_by_user_id] Failed to submit deletion for row {row_index_to_remove}. Error: {self.model.lastError().text()}"
            print(error_msg)
            self.model.revertAll()
            self.model.select()
            return None
