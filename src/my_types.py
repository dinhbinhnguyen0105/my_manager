# src/my_types.py
from dataclasses import dataclass
from typing import Optional, List, Union

from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class UserType:
    id: Optional[int]
    uid: Optional[str]
    my_id: Optional[str]
    username: Optional[str]
    password: Optional[str]
    two_fa: Optional[str]
    email: Optional[str]
    email_password: Optional[str]
    phone_number: Optional[str]
    note: Optional[str]
    type: Optional[str]
    user_group: Optional[int]
    mobile_ua: Optional[str]
    desktop_ua: Optional[str]
    status: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class UserListedProductType:
    id: Optional[int]
    id_user: int
    pid: str
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class SettingProxyType:
    id: Optional[int]
    value: str
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class SettingUserDataDirType:
    id: Optional[int]
    value: str
    is_selected: int
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class RealEstateProductType:
    id: Optional[int]
    pid: Optional[str]
    status: Optional[int]
    transaction_type: Optional[str]
    province: Optional[str]
    district: Optional[str]
    ward: Optional[str]
    street: Optional[str]
    category: Optional[str]
    area: Optional[float]
    price: Optional[float]
    legal: Optional[str]
    structure: Optional[float]
    function: Optional[str]
    building_line: Optional[str]
    furniture: Optional[str]
    description: Optional[str]
    image_dir: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class RealEstateTemplateType:
    id: Optional[int]
    transaction_type: Optional[str]
    category: Optional[str]
    is_default: Optional[int]
    part: Optional[str]
    value: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


@dataclass
class MiscProductType:
    id: Optional[int]
    pid: Optional[str]
    category: Optional[int]
    title: Optional[str]
    description: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[int]


@dataclass
class SellPayloadType:
    title: str
    description: str
    image_paths: List[str]


@dataclass
class CreateAccountPayloadType:
    first_name: str
    surname: str
    birth_day: str
    gender: int
    passwords: str
    phone_number: str


@dataclass
class LaunchPayloadType:
    url: str


@dataclass
class RobotTaskType:
    user_info: UserType
    action_name: Optional[str]
    action_payload: Union[SellPayloadType, CreateAccountPayloadType, LaunchPayloadType]


@dataclass
class BrowserTaskType(RobotTaskType):
    is_mobile: bool
    headless: bool
    udd: str
    browser_id: str


@dataclass
class RobotSettingsType:
    is_mobile: bool
    headless: bool
    thread_num: int
    group_num: int
    delay_num: float
    group_file_path: str


class BrowserWorkerSignals(QObject):
    info_signal = pyqtSignal(BrowserTaskType, str)
    warning_signal = pyqtSignal(BrowserTaskType, str)
    failed_signal = pyqtSignal(BrowserTaskType, str, str)
    error_signal = pyqtSignal(BrowserTaskType, str)
    progress_signal = pyqtSignal(BrowserTaskType, str, list)
    finished_signal = pyqtSignal(BrowserTaskType, str, str)
    proxy_unavailable_signal = pyqtSignal(BrowserTaskType, str)
    proxy_not_ready_signal = pyqtSignal(BrowserTaskType, str)
    require_phone_number_signal = pyqtSignal(BrowserTaskType)
    require_otp_code_signal = pyqtSignal(BrowserTaskType)


class BrowserManagerSignals(QObject):
    info_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    warning_signal = pyqtSignal(str)
    failed_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    task_succeed_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str, list)


class ControllerSignals(BrowserManagerSignals):
    data_changed_signal = pyqtSignal()
    pass
