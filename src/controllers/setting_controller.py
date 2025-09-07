# src/controllers/setting_controller.py
from typing import List, Optional
from src.controllers.base_controller import BaseController
from src.services.setting_service import SettingProxyService, SettingUserDataDirService
from src.my_types import SettingProxyType, SettingUserDataDirType


class SettingProxyController(BaseController):
    def __init__(self, service: SettingProxyService, parent=None):
        super().__init__(service, parent)

    def create_proxy(self, proxy_data: SettingProxyType):
        try:
            if not isinstance(proxy_data, SettingProxyType):
                raise TypeError(f"Expected SettingProxyType, got {type(proxy_data)}")
            if not self.service.create(proxy_data):
                self.controller_signals.error_signal.emit(
                    "Failed to create proxy setting."
                )
                return False
            self.controller_signals.finished_signal.emit(
                "Successfully created proxy setting."
            )
            self.controller_signals.data_changed_signal.emit()
            return True
        except Exception as e:
            print(f"[{self.__class__.__name__}.create_proxy] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while creating proxy setting."
            )
            return False

    def read_proxy(self, record_id: int) -> Optional[SettingProxyType]:
        try:
            proxy = self.service.read(record_id)
            if not proxy:
                self.controller_signals.warning_signal.emit(
                    f"Failed to read proxy setting (id: {record_id})."
                )
                return None
            return proxy
        except Exception as e:
            print(f"[{self.__class__.__name__}.read_proxy] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while reading proxy setting."
            )
            return None

    def read_all_proxies(self) -> List[SettingProxyType]:
        try:
            return self.service.read_all()
        except Exception as e:
            print(f"[{self.__class__.__name__}.read_all_proxies] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while reading all proxy settings."
            )
            return []

    def update_proxy(self, record_id: int, proxy_data: SettingProxyType) -> bool:
        try:
            if not isinstance(proxy_data, SettingProxyType):
                raise TypeError(f"Expected SettingProxyType, got {type(proxy_data)}")
            if not self.service.update(record_id, proxy_data):
                self.controller_signals.error_signal.emit(
                    "Failed to update proxy setting."
                )
                return False
            self.controller_signals.finished_signal.emit(
                "Successfully updated proxy setting."
            )
            self.controller_signals.data_changed_signal.emit()
            return True
        except Exception as e:
            print(f"[{self.__class__.__name__}.update_proxy] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while updating proxy setting."
            )
            return False

    def delete_proxy(self, record_id: int) -> bool:
        try:
            if not self.service.delete(record_id):
                self.controller_signals.warning_signal.emit(
                    f"Failed to delete proxy setting (id: {record_id})."
                )
                return False
            self.controller_signals.finished_signal.emit(
                f"Successfully deleted proxy setting (id: {record_id})."
            )
            self.controller_signals.data_changed_signal.emit()
            return True
        except Exception as e:
            print(f"[{self.__class__.__name__}.delete_proxy] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while deleting proxy setting."
            )
            return False

    def delete_multiple_proxies(self, record_ids: List[int]) -> bool:
        try:
            self.service.delete_multiple(record_ids)
            self.controller_signals.finished_signal.emit(
                "Successfully deleted multiple proxy settings."
            )
            self.controller_signals.data_changed_signal.emit()
            return True
        except Exception as e:
            print(f"[{self.__class__.__name__}.delete_multiple_proxies] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while deleting multiple proxy settings."
            )
            return False

    def import_products(self, file_path):
        return super().import_products(file_path, SettingProxyType)


class SettingUserDataDirController(BaseController):
    def __init__(self, service: SettingUserDataDirService, parent=None):
        super().__init__(service, parent)
        self.service = service

    def create_user_data_dir(self, data_dir: SettingUserDataDirType):
        try:
            if not isinstance(data_dir, SettingUserDataDirType):
                raise TypeError(
                    f"Expected SettingUserDataDirType, got {type(data_dir)}"
                )
            if not self.service.create(data_dir):
                self.controller_signals.error_signal.emit(
                    "Failed to create user data dir setting."
                )
                return False
            self.controller_signals.finished_signal.emit(
                "Successfully created user data dir setting."
            )
            self.controller_signals.data_changed_signal.emit()
            return True
        except Exception as e:
            print(f"[{self.__class__.__name__}.create_user_data_dir] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while creating user data dir setting."
            )
            return False

    def read_user_data_dir(self, record_id: int) -> Optional[SettingUserDataDirType]:
        try:
            data_dir = self.service.read(record_id)
            if not data_dir:
                self.controller_signals.warning_signal.emit(
                    f"Failed to read user data dir setting (id: {record_id})."
                )
                return None
            return data_dir
        except Exception as e:
            print(f"[{self.__class__.__name__}.read_user_data_dir] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while reading user data dir setting."
            )
            return None

    def read_all_user_data_dirs(self) -> List[SettingUserDataDirType]:
        try:
            return self.service.read_all()
        except Exception as e:
            print(f"[{self.__class__.__name__}.read_all_user_data_dirs] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while reading all user data dir settings."
            )
            return []

    def update_user_data_dir(
        self, record_id: int, data_dir: SettingUserDataDirType
    ) -> bool:
        try:
            if not isinstance(data_dir, SettingUserDataDirType):
                raise TypeError(
                    f"Expected SettingUserDataDirType, got {type(data_dir)}"
                )
            if not self.service.update(record_id, data_dir):
                self.controller_signals.error_signal.emit(
                    "Failed to update user data dir setting."
                )
                return False
            self.controller_signals.finished_signal.emit(
                "Successfully updated user data dir setting."
            )
            self.controller_signals.data_changed_signal.emit()
            return True
        except Exception as e:
            print(f"[{self.__class__.__name__}.update_user_data_dir] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while updating user data dir setting."
            )
            return False

    def delete_user_data_dir(self, record_id: int) -> bool:
        try:
            if not self.service.delete(record_id):
                self.controller_signals.warning_signal.emit(
                    f"Failed to delete user data dir setting (id: {record_id})."
                )
                return False
            self.controller_signals.finished_signal.emit(
                f"Successfully deleted user data dir setting (id: {record_id})."
            )
            self.controller_signals.data_changed_signal.emit()
            return True
        except Exception as e:
            print(f"[{self.__class__.__name__}.delete_user_data_dir] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while deleting user data dir setting."
            )
            return False

    def delete_multiple_user_data_dirs(self, record_ids: List[int]) -> bool:
        try:
            self.service.delete_multiple(record_ids)
            self.controller_signals.finished_signal.emit(
                "Successfully deleted multiple user data dir settings."
            )
            self.controller_signals.data_changed_signal.emit()
            return True
        except Exception as e:
            print(
                f"[{self.__class__.__name__}.delete_multiple_user_data_dirs] Error: {e}"
            )
            self.controller_signals.error_signal.emit(
                "Error occurred while deleting multiple user data dir settings."
            )
            return False

    def get_selected_user_data_dir(self):
        try:
            udd = None
            udd = self.service.get_selected()
            # self.controller_signals.finished_signal.emit(
            #     "Successfully get selected user data dir settings."
            # )
            self.controller_signals.data_changed_signal.emit()
            return udd
        except Exception as e:
            print(f"[{self.__class__.__name__}.get_selected_user_data_dir] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while get user data dir setting."
            )
            return False

    def set_selected_user_data_dir(self, record_id: int):
        """
        Sets the selected user data directory based on the provided record ID.

        Attempts to set the selected user data directory by invoking the service's `set_selected` method.
        Emits different signals based on the outcome:
        - Emits `info_signal` if the selection was not successful.
        - Emits `success_signal` and `data_changed_signal` if the selection was successful.
        - Emits `controller_signals.error_signal` if an exception occurs.

        Args:
            record_id (int): The ID of the record to be set as selected.

        Returns:
            bool: True if the selection was successful, False otherwise.
        """
        try:
            if not self.service.set_selected(record_id=record_id):
                self.controller_signals.info_signal.emit(
                    f"Failed to select user data directory for record ID {record_id}."
                )
            else:
                self.controller_signals.finished_signal.emit(
                    f"User data directory for record ID {record_id} successfully selected."
                )
                self.controller_signals.data_changed_signal.emit()
                return True
        except Exception as e:
            print(f"[{self.__class__.__name__}.set_selected_user_data_dir] Error: {e}")
            self.controller_signals.error_signal.emit(
                f"An error occurred while setting user data directory for record ID {record_id}. Error: {e}"
            )
            return False

    def import_products(self, file_path):
        return super().import_products(file_path, SettingUserDataDirType)
