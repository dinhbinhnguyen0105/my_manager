# src/views/product/dialog_update_re_product.py
from typing import List
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import QDialog, QMessageBox, QLineEdit
from PyQt6.QtGui import QDoubleValidator, QPixmap

from src.my_types import RealEstateProductType
from src.ui.dialog_re_product_ui import Ui_Dialog_REProduct

from src.my_constants import (
    RE_TRANSACTION,
    RE_STATUS,
    RE_CATEGORY,
    RE_PROVINCE,
    RE_DISTRICT,
    RE_WARD,
    RE_BUILDING_LINE,
    RE_LEGAL,
    RE_FURNITURE,
)


class DialogUpdateREProduct(QDialog, Ui_Dialog_REProduct):
    product_data_signal = pyqtSignal(RealEstateProductType)

    def __init__(
        self, image_paths: List[str], product_data: RealEstateProductType, parent=None
    ):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f"Update {product_data.pid}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setModal(False)
        self.buttonBox.button(self.buttonBox.StandardButton.Save).disconnect()
        self.buttonBox.button(self.buttonBox.StandardButton.Save).clicked.connect(
            self.on_accepted
        )
        self.image_paths: List[str] = image_paths
        self.product_data = product_data
        self.init_options()
        self._display_image(image_paths)
        self.init_data()
        self.init_validate_input()

    def init_options(self):
        self.transaction_container_w.setHidden(True)
        self.pid_input.setDisabled(True)

        self.categories_combobox.clear()
        for _key in RE_CATEGORY.keys():
            self.categories_combobox.addItem(RE_CATEGORY[_key].capitalize(), _key)
        self.status_combobox.clear()
        for _key in RE_STATUS:
            self.status_combobox.addItem(RE_STATUS[_key].capitalize(), _key)
        self.wards_combobox.clear()
        for _key in RE_WARD:
            self.wards_combobox.addItem(RE_WARD[_key].capitalize(), _key)
        self.districts_combobox.clear()
        for _key in RE_DISTRICT:
            self.districts_combobox.addItem(RE_DISTRICT[_key].capitalize(), _key)
        self.provinces_combobox.clear()
        for _key in RE_PROVINCE:
            self.provinces_combobox.addItem(RE_PROVINCE[_key].capitalize(), _key)
        self.furniture_s_combobox.clear()
        for _key in RE_FURNITURE:
            self.furniture_s_combobox.addItem(RE_FURNITURE[_key].capitalize(), _key)
        self.building_line_s_combobox.clear()
        for _key in RE_BUILDING_LINE:
            self.building_line_s_combobox.addItem(
                RE_BUILDING_LINE[_key].capitalize(), _key
            )
        self.legal_s_combobox.clear()
        for _key in RE_LEGAL:
            self.legal_s_combobox.addItem(RE_LEGAL[_key].capitalize(), _key)

    def init_validate_input(self):
        validator = QDoubleValidator(self)
        validator.setDecimals(2)
        self.area_input.setValidator(validator)
        self.price_input.setValidator(validator)
        self.structure_input.setValidator(validator)
        self.area_input.textChanged.connect(
            lambda text: self._replace_dot_with_comma(self.area_input, text)
        )
        self.price_input.textChanged.connect(
            lambda text: self._replace_dot_with_comma(self.price_input, text)
        )
        self.structure_input.textChanged.connect(
            lambda text: self._replace_dot_with_comma(self.structure_input, text)
        )

    def init_data(self):
        # Set giá trị cho các input từ self.product_data
        if not self.product_data:
            return

        # PID
        self.pid_input.setText(str(self.product_data.pid))

        # status
        idx = self.status_combobox.findData(self.product_data.status)
        if idx != -1:
            self.status_combobox.setCurrentIndex(idx)

        # Transaction type (ẩn, nhưng nếu cần thì set)
        # self.transaction_value = self.product_data.transaction_type

        # Province
        idx = self.provinces_combobox.findData(self.product_data.province)
        if idx != -1:
            self.provinces_combobox.setCurrentIndex(idx)

        # District
        idx = self.districts_combobox.findData(self.product_data.district)
        if idx != -1:
            self.districts_combobox.setCurrentIndex(idx)

        # Ward
        idx = self.wards_combobox.findData(self.product_data.ward)
        if idx != -1:
            self.wards_combobox.setCurrentIndex(idx)

        # Street
        self.street_input.setText(str(self.product_data.street))

        # Category
        idx = self.categories_combobox.findData(self.product_data.category)
        if idx != -1:
            self.categories_combobox.setCurrentIndex(idx)

        # Area
        self.area_input.setText(str(self.product_data.area))

        # Price
        self.price_input.setText(str(self.product_data.price))

        # Legal
        idx = self.legal_s_combobox.findData(self.product_data.legal)
        if idx != -1:
            self.legal_s_combobox.setCurrentIndex(idx)

        # Structure
        self.structure_input.setText(str(self.product_data.structure))

        # Function
        self.function_input.setText(str(self.product_data.function))

        # Building line
        idx = self.building_line_s_combobox.findData(self.product_data.building_line)
        if idx != -1:
            self.building_line_s_combobox.setCurrentIndex(idx)

        # Furniture
        idx = self.furniture_s_combobox.findData(self.product_data.furniture)
        if idx != -1:
            self.furniture_s_combobox.setCurrentIndex(idx)

        # Description
        self.description_input.setPlainText(str(self.product_data.description))

    def _display_image(self, image_paths: List[str]):
        if not len(image_paths):
            self.image_input.setText("Failed to load image.")
        pixmap = QPixmap(image_paths[0])
        if not pixmap.isNull():
            self.image_input.setPixmap(
                pixmap.scaled(
                    self.image_input.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.image_input.setText("Failed to load image.")

    @pyqtSlot(QLineEdit, str)
    def _replace_dot_with_comma(self, line_edit: QLineEdit, text: str):
        if "." in text:
            cursor_pos = line_edit.cursorPosition()
            new_text = text.replace(".", ",")
            line_edit.blockSignals(True)
            line_edit.setText(new_text)
            line_edit.setCursorPosition(cursor_pos)
            line_edit.blockSignals(False)

    @pyqtSlot()
    def on_accepted(self):
        product_data = RealEstateProductType(
            id=self.product_data.id,
            pid=self.product_data.pid,
            status=self.status_combobox.currentData(),
            transaction_type=self.product_data.transaction_type,
            province=self.provinces_combobox.currentText().lower(),
            district=self.districts_combobox.currentText().lower(),
            ward=self.wards_combobox.currentText().lower(),
            street=self.street_input.text().lower(),
            category=self.categories_combobox.currentText().lower(),
            area=self.area_input.text(),
            price=self.price_input.text(),
            legal=self.legal_s_combobox.currentText().lower(),
            structure=self.structure_input.text().lower(),
            function=self.function_input.text(),
            building_line=self.building_line_s_combobox.currentText().lower(),
            furniture=self.furniture_s_combobox.currentText().lower(),
            description=self.description_input.toPlainText(),
            image_dir=self.product_data.image_dir,
            created_at=self.product_data.created_at,
            updated_at=None,
        )
        if not len(self.image_paths):
            QMessageBox.warning(self, "Missing Images", "Please add at least 1 image.")
            return
        elif not product_data.pid:
            QMessageBox.warning(self, "Missing Product ID", "Product ID is missing.")
            return
        elif not product_data.transaction_type:
            QMessageBox.warning(
                self, "Missing Transaction Type", "Please select a transaction type."
            )
            return
        elif not product_data.street:
            QMessageBox.warning(
                self, "Missing Street Name", "Please enter a street name."
            )
            return
        elif not product_data.price:
            QMessageBox.warning(self, "Missing Price", "Please enter a price.")
            return

        self.product_data_signal.emit(product_data)
        self.accept()
