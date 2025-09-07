# src/views/product/dialog_create_re_product.py
from typing import List
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import QDialog, QRadioButton, QMessageBox, QLineEdit
from PyQt6.QtGui import QDoubleValidator, QDragEnterEvent, QDropEvent, QPixmap

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


class DialogCreateREProduct(QDialog, Ui_Dialog_REProduct):
    product_data_signal = pyqtSignal(list, RealEstateProductType)
    request_new_pid_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(DialogCreateREProduct, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Create new re product")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.setModal(False)
        self.buttonBox.button(self.buttonBox.StandardButton.Save).disconnect()
        self.buttonBox.button(self.buttonBox.StandardButton.Save).clicked.connect(
            self.on_accepted
        )

        self.transaction_option_widgets: List[QRadioButton] = []
        self.image_paths: List[str] = []
        self.transaction_value: str = ""

        self.init_options()
        self.init_validate_input()
        self.setup_events()
        self._setupImageDrop()

    def init_options(self):
        for transaction_type in RE_TRANSACTION.keys():
            transaction_option = QRadioButton(
                RE_TRANSACTION[transaction_type].capitalize()
            )

            transaction_option.setStyleSheet("padding: 0 24px;")
            transaction_option.setProperty("value", RE_TRANSACTION[transaction_type])
            transaction_option.clicked.connect(
                lambda _, opt=transaction_option: self.on_transaction_option_clicked(
                    opt.property("value")
                )
            )
            self.transaction_option_widgets.append(transaction_option)
            self.transaction_container_w.layout().addWidget(transaction_option)
        self.transaction_container_w.layout().setAlignment(
            Qt.AlignmentFlag.AlignJustify
        )

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

    def setup_events(self):
        pass

    def setup_ui(self):
        pass

    def _setupImageDrop(self):
        self.image_input.setAcceptDrops(True)
        self.image_input.dragEnterEvent = self._imagesDragEnterEvent
        self.image_input.dropEvent = self._imagesDropEvent

    def _imagesDragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def _imagesDropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            images = [url.toLocalFile() for url in event.mimeData().urls()]
            self._handleDroppedImages(images)
            self.image_paths = images

    def _handleDroppedImages(self, image_paths):
        if image_paths:
            self._display_image(image_paths[0])
        else:
            self.image_input.setText("No images dropped.")

    def _display_image(self, image_path):
        pixmap = QPixmap(image_path)
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

    @pyqtSlot(str)
    def on_transaction_option_clicked(self, transaction_type: str):
        self.transaction_value = transaction_type
        self.request_new_pid_signal.emit(transaction_type)

    @pyqtSlot()
    def on_accepted(self):
        product_data = RealEstateProductType(
            id=-1,
            pid=self.pid_input.text(),
            status=self.status_combobox.currentData(),
            transaction_type=self.transaction_value,
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
            image_dir=None,
            created_at=None,
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

        self.product_data_signal.emit(sorted(self.image_paths), product_data)
        self.accept()
