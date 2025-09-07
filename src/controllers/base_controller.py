# src/controllers/base_controller.py
from PyQt6.QtCore import QObject, pyqtSignal

import json
from typing import Union, Optional, Dict, Type, List, TypeAlias, Any
from dataclasses import fields, asdict
from src.my_types import (
    UserType,
    RealEstateProductType,
    SettingProxyType,
    SettingUserDataDirType,
    RealEstateTemplateType,
    ControllerSignals,
)

DataType: TypeAlias = Union[
    UserType,
    RealEstateProductType,
    SettingProxyType,
    SettingUserDataDirType,
    RealEstateTemplateType,
]

DataTypeList: TypeAlias = List[DataType]


class BaseController(QObject):
    def __init__(self, service: Optional[Any], parent=None):
        super().__init__(parent)
        self.service = service
        self.controller_signals = ControllerSignals()

    def read_json_file(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Reads a JSON file and returns its content as a list of dictionaries.
        Returns None on error (FileNotFoundError, JSONDecodeError, or other errors).
        """
        try:
            with open(file_path, mode="r", encoding="utf8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    msg = f"Warning: JSON file '{file_path}' does not contain a top-level list."
                    self.controller_signals.warning_signal.emit(msg)
                    return None
                for item in data:
                    if not isinstance(item, dict):
                        msg = f"Warning: JSON file '{file_path}' contains non-dictionary items in the list."
                        self.controller_signals.warning_signal.emit(msg)
                        return None
                return data
        except FileNotFoundError:
            msg = f"Error: File not found at '{file_path}'."
            self.controller_signals.error_signal.emit(msg)
            return None
        except json.JSONDecodeError as e:
            msg = f"Error: Invalid JSON syntax in '{file_path}'. Details: {e}"
            self.controller_signals.error_signal.emit(msg)
            return None
        except Exception as e:
            msg = f"An unexpected error occurred while reading '{file_path}': {e}"
            self.controller_signals.error_signal.emit(msg)
            return None

    def parse_JSON_to_data_type(
        self,
        payload: Dict,
        data_type: DataType,
    ) -> Optional[DataTypeList]:
        """
        Reads a JSON file (expected to contain a list of dictionaries) and
        converts each dictionary into an instance of the specified dataclass type.

        Args:
            file_path (str): The path to the JSON file.
            data_type (Union[Type[UserType], Type[RealEstateProductType]]):
                The dataclass type to convert the JSON dictionaries into.

        Returns:
            Optional[DataTypeList]: A list of dataclass instances
            if successful, otherwise None.
        """
        raw_data_list = payload
        if raw_data_list is None:  # read_json_file now returns None on error
            return None

        parsed_instances: DataTypeList = []

        dataclass_field_types = {f.name: f.type for f in fields(data_type)}

        for item_dict in raw_data_list:
            instance_data: Dict[str, Any] = {}

            for field_name, field_type in dataclass_field_types.items():
                value = item_dict.get(field_name)

                actual_type = field_type
                if hasattr(field_type, "__origin__") and field_type.__origin__ is Union:
                    non_none_types = [
                        t for t in field_type.__args__ if t is not type(None)
                    ]
                    if len(non_none_types) == 1:
                        actual_type = non_none_types[0]

                if value is not None:
                    if actual_type is int:
                        try:
                            instance_data[field_name] = int(value)
                        except (ValueError, TypeError):
                            print(
                                f"Warning: Could not convert '{value}' to int for field '{field_name}'. Setting to None."
                            )
                            instance_data[field_name] = None
                    elif actual_type is float:
                        try:
                            instance_data[field_name] = float(value)
                        except (ValueError, TypeError):
                            print(
                                f"Warning: Could not convert '{value}' to float for field '{field_name}'. Setting to None."
                            )
                            instance_data[field_name] = None
                    elif actual_type is str:
                        instance_data[field_name] = str(value)
                    else:
                        instance_data[field_name] = value
                else:
                    instance_data[field_name] = None

            try:
                instance = data_type(**instance_data)
                parsed_instances.append(instance)
            except TypeError as e:
                print(
                    f"Error: Could not create instance of {data_type.__name__} from data: {item_dict}. Details: {e}"
                )
                return None
            except Exception as e:
                print(f"Unexpected error while creating instance: {e}")
                return None
        return parsed_instances

    def export_to_file(self, file_path: str):
        data_list: DataTypeList = self.service.read_all()
        if not data_list:
            print("Warning: Data list is empty. Nothing to export.")
            try:
                with open(file_path, mode="w", encoding="utf8") as f:
                    json.dump([], f, indent=4)  # Write an empty array
                return True
            except IOError as e:
                print(f"Error: Could not write JSON file '{file_path}'. Details: {e}")
                return False

        export_data = []
        for item in data_list:
            try:
                # asdict() converts a dataclass instance to a dictionary
                export_data.append(asdict(item))
            except TypeError as e:
                print(
                    f"Error: Could not convert instance of {type(item).__name__} to dictionary: {e}"
                )
                return False
            except Exception as e:
                print(f"Unexpected error converting instance to dict: {e}")
                return False

        try:
            with open(file_path, mode="w", encoding="utf8") as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            self.controller_signals.finished_signal.emit(
                f"Exported to file '{file_path}'."
            )
            self.controller_signals.data_changed_signal.emit()
            return True
        except IOError as e:
            self.controller_signals.error_signal(
                f"Error: Could not write JSON file '{file_path}'. Details: {e}"
            )
            return False
        except Exception as e:
            self.controller_signals.error_signal(
                f"An unexpected error occurred while exporting JSON file '{file_path}': {e}"
            )
            return False

    def import_products(self, file_path: str, data_type: DataType):
        try:
            raw_products = self.read_json_file(file_path)
            if raw_products:
                products = self.parse_JSON_to_data_type(raw_products, data_type)
                self.service.import_data(products)
                self.controller_signals.finished_signal.emit(
                    "Successfully imported real estate products."
                )
                self.controller_signals.data_changed_signal.emit()
                return True
            else:
                return False
        except Exception as e:
            print(f"[{self.__class__.__name__}.import_products] Error: {e}")
            self.controller_signals.error_signal.emit(
                "Error occurred while importing real estate products."
            )
            return False
