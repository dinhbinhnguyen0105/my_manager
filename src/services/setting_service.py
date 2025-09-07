# src/services/setting_service.py
from typing import List, Optional
from src.services.base_service import BaseService
from src.models.setting_model import SettingProxyModel, SettingUserDataDirModel
from src.my_types import SettingProxyType, SettingUserDataDirType


class SettingProxyService(BaseService):
    DATA_TYPE = SettingProxyType

    def __init__(self, model: SettingProxyModel):
        if not isinstance(model, SettingProxyModel):
            raise TypeError(
                "model must be an instance of SettingProxyType or its subclass."
            )
        super().__init__(model)
        self.model = model

    def create(self, payload: SettingProxyType):
        return super().create(payload)

    def read_all(self) -> List[SettingProxyType]:
        list_proxies: List[SettingProxyType] = super().read_all()
        return [proxy for proxy in list_proxies if proxy.value]

    def delete(self, record_id: int) -> bool:
        return super().delete(record_id)

    def delete_multiple(self, record_ids):
        return super().delete_multiple(record_ids)


class SettingUserDataDirService(BaseService):
    DATA_TYPE = SettingUserDataDirType

    def __init__(self, model: SettingUserDataDirModel):
        if not isinstance(model, SettingUserDataDirModel):
            raise TypeError(
                "model must be an instance of SettingUserDataDirType or its subclass."
            )
        super().__init__(model)

    def read(self, record_id: int) -> SettingUserDataDirType:
        return super().read(record_id)

    def create(self, payload: SettingUserDataDirType):
        return super().create(payload)

    def read_all(self) -> List[SettingUserDataDirType]:
        return super().read_all()

    def delete(self, record_id: int) -> bool:
        return super().delete(record_id)

    def delete_multiple(self, record_ids):
        return super().delete_multiple(record_ids)

    def set_selected(self, record_id: int) -> bool:
        udds = self.read_all()
        for udd in udds:
            udd.is_selected = 0
            self.update(udd.id, udd)

        current_udd = self.read(record_id)
        current_udd.is_selected = 1
        update_success = self.update(record_id, current_udd)
        if update_success:
            # print(
            #     f"[{self.__class__.__name__}.set_selected] Successfully toggled status for udd ID '{record_id}' to 1."
            # )
            return True
        else:
            # print(
            #     f"[{self.__class__.__name__}.set_selected] Failed to update status for udd ID '{record_id}'."
            # )
            return False

    def get_selected(self) -> Optional[str]:
        udds = self.read_all()
        for udd in udds:
            if udd.is_selected == 1:
                return udd.value
        return None
