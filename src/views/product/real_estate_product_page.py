# src/views/product/product.py
import os, sys
from typing import List, Optional
from PyQt6.QtGui import QAction, QPixmap, QMouseEvent, QShortcut, QKeySequence
from PyQt6.QtWidgets import QWidget, QMenu, QMessageBox
from PyQt6.QtCore import (
    Qt,
    pyqtSlot,
    QPoint,
    QItemSelection,
)
from src.controllers.product_controller import (
    RealEstateProductController,
    RealEstateTemplateController,
)
from src.models.product_model import (
    RealEstateProductModel,
    RealEstateTemplateModel,
)
from src.controllers.setting_controller import SettingUserDataDirController

from src.views.product.dialog_create_re_product import DialogCreateREProduct
from src.views.product.dialog_update_re_product import DialogUpdateREProduct
from src.views.utils.multi_field_model import MultiFieldFilterProxyModel
from src.ui.page_re_product_ui import Ui_PageREProduct

from src.my_types import RealEstateProductType
from src.utils.re_template import replace_template, init_footer_content
from src.views.utils.file_dialogs import dialog_open_file, dialog_save_file
from src.my_constants import (
    RE_WARD,
    RE_TRANSACTION,
    RE_CATEGORY,
    RE_BUILDING_LINE,
    RE_FURNITURE,
    RE_LEGAL,
    RE_STATUS,
)


class RealEstateProductPage(QWidget, Ui_PageREProduct):
    def __init__(
        self,
        product_controller: RealEstateProductController,
        template_controller: RealEstateTemplateController,
        setting_controller: SettingUserDataDirController,
        parent=None,
    ):
        super(RealEstateProductPage, self).__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("Real estate product")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._product_controller = product_controller
        self._template_controller = template_controller
        self._setting_controller = setting_controller

        self.base_product_model: RealEstateProductModel = (
            self._product_controller.service.model
        )
        while self.base_product_model.canFetchMore():
            self.base_product_model.fetchMore()
        self.base_template_model: RealEstateTemplateModel = (
            self._template_controller.service.model
        )
        # print(f"base model: {self.base_product_model.rowCount()}")
        self.proxy_product_model = MultiFieldFilterProxyModel()
        self.proxy_product_model.setSourceModel(self.base_product_model)

        self.current_product: Optional[RealEstateProductType] = None
        self.current_image_paths: List[str] = []

        self.setup_ui()
        self.setup_events()
        self.set_filters()

    def setup_ui(self):
        self.set_product_table()
        self.set_comboboxes()
        # self.status_combobox.chan

    def setup_events(self):
        self.action_create_btn.clicked.connect(self.on_create_product)
        self.details_container_w.setHidden(True)
        self.action_default_btn.clicked.connect(
            lambda: self.set_product_details("default")
        )
        self.action_random_btn.clicked.connect(
            lambda: self.set_product_details("random")
        )
        shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut.activated.connect(self.on_create_product)
        self.action_export_btn.clicked.connect(self.on_export_clicked)
        self.action_import_btn.clicked.connect(self.on_import_clicked)

    def set_comboboxes(self):
        self.status_combobox.clear()
        self.status_combobox.addItem("Tất cả", -1)
        for key, value in RE_STATUS.items():
            self.status_combobox.addItem(value.capitalize(), key)

        self.wards_combobox.clear()
        self.wards_combobox.addItem("Tất cả", "")
        for key, value in RE_WARD.items():
            self.wards_combobox.addItem(value.capitalize(), key)
        self.transaction_combobox.clear()
        self.transaction_combobox.addItem("Tất cả", "")
        for key, value in RE_TRANSACTION.items():
            self.transaction_combobox.addItem(value.capitalize(), key)
        self.categories_combobox.clear()
        self.categories_combobox.addItem("Tất cả", "")
        for key, value in RE_CATEGORY.items():
            self.categories_combobox.addItem(value.capitalize(), key)
        self.building_line_s_combobox.clear()
        self.building_line_s_combobox.addItem("Tất cả", "")
        for key, value in RE_BUILDING_LINE.items():
            self.building_line_s_combobox.addItem(value.capitalize(), key)
        self.furniture_s_combobox.clear()
        self.furniture_s_combobox.addItem("Tất cả", "")
        for key, value in RE_FURNITURE.items():
            self.furniture_s_combobox.addItem(value.capitalize(), key)
        self.legal_s_combobox.clear()
        self.legal_s_combobox.addItem("Tất cả", "")
        for key, value in RE_LEGAL.items():
            self.legal_s_combobox.addItem(value.capitalize(), key)

    def set_filters(self):
        # return
        model = self.base_product_model
        filter_widgets = [
            (self.pid_input, model.fieldIndex("pid")),
            (self.street_input, model.fieldIndex("street")),
            (self.area_input, model.fieldIndex("area")),
            (self.price_input, model.fieldIndex("price")),
            (self.structure_input, model.fieldIndex("structure")),
            (self.function_input, model.fieldIndex("function")),
            (self.categories_combobox, model.fieldIndex("category")),
            (self.building_line_s_combobox, model.fieldIndex("building_line")),
            (self.furniture_s_combobox, model.fieldIndex("furniture")),
            (self.legal_s_combobox, model.fieldIndex("legal")),
            (self.transaction_combobox, model.fieldIndex("transaction_type")),
            (self.wards_combobox, model.fieldIndex("ward")),
            (self.status_combobox, model.fieldIndex("status")),
        ]

        for widget, column in filter_widgets:
            if hasattr(widget, "textChanged"):
                widget.textChanged.connect(
                    lambda text, col=column: self.proxy_product_model.set_filter(
                        col, text
                    )
                )
            elif hasattr(widget, "currentTextChanged"):
                if widget == self.status_combobox:
                    self.status_combobox.currentIndexChanged.connect(
                        lambda index, col=column: self.proxy_product_model.set_filter(
                            col,
                            (
                                self.status_combobox.currentData()
                                if self.status_combobox.currentData() != -1
                                else ""
                            ),
                        )
                    )
                else:
                    widget.currentTextChanged.connect(
                        lambda text, col=column: self.proxy_product_model.set_filter(
                            col, "" if text == "Tất cả" or text == "" else text
                        )
                    )

    def get_selected_ids(self):
        selected_indexes = self.products_table.selectionModel().selectedRows()
        ids = []
        for proxy_index in selected_indexes:
            # Chuyển sang index của source model
            source_index = self.proxy_product_model.mapToSource(proxy_index)
            source_model = self.proxy_product_model.sourceModel()
            # Tìm cột id
            id_col = (
                source_model.fieldIndex("id")
                if hasattr(source_model, "fieldIndex")
                else 0
            )
            id_index = source_model.index(source_index.row(), id_col)
            id_value = source_model.data(id_index, Qt.ItemDataRole.DisplayRole)
            ids.append(id_value)
        return sorted(ids)

    def set_product_table(self):
        self.products_table.setModel(self.proxy_product_model)
        self.products_table.setSortingEnabled(True)
        self.products_table.setSelectionBehavior(
            self.products_table.SelectionBehavior.SelectRows
        )
        self.products_table.setSelectionMode(
            self.products_table.SelectionMode.SingleSelection
        )
        self.products_table.setEditTriggers(
            self.products_table.EditTrigger.NoEditTriggers
        )

        self.products_table.selectionModel().selectionChanged.connect(
            self.on_selection_changed
        )

        for i in range(self.base_product_model.columnCount()):
            column_name = self.base_product_model.headerData(
                i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
            )
            if column_name in [
                "id",
                "status",
                "province",
                "district",
                "image_dir",
            ]:
                self.products_table.setColumnHidden(i, True)
        self.products_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.products_table.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos: QPoint):
        proxy_index = self.products_table.indexAt(pos)
        if not proxy_index.isValid():
            return

        # Chuyển sang index của source model
        source_index = self.proxy_product_model.mapToSource(proxy_index)
        source_model = self.proxy_product_model.sourceModel()

        # Tìm cột status
        status_col = (
            source_model.fieldIndex("status")
            if hasattr(source_model, "fieldIndex")
            else 0
        )
        status_index = source_model.index(source_index.row(), status_col)
        status_value: int = source_model.data(status_index, Qt.ItemDataRole.DisplayRole)

        id_col = (
            source_model.fieldIndex("id") if hasattr(source_model, "fieldIndex") else 0
        )
        id_index = source_model.index(source_index.row(), id_col)
        id_value = source_model.data(id_index, Qt.ItemDataRole.DisplayRole)

        global_pos = self.products_table.mapToGlobal(pos)
        menu = QMenu(self.products_table)

        if status_value == 1:
            set_unavailable = QAction("Change to unavailable", self)
            menu.addAction(set_unavailable)
            set_unavailable.triggered.connect(self.handle_change_status)
        else:
            set_available = QAction("Change to available", self)
            menu.addAction(set_available)
            set_available.triggered.connect(self.handle_change_status)

        update_action = QAction("Update", self)
        delete_action = QAction("Delete", self)
        update_action.triggered.connect(
            lambda _, record_id=id_value: self.on_update_product(record_id)
        )
        delete_action.triggered.connect(
            lambda _, record_id=id_value: self.handle_delete_product(record_id)
        )
        menu.addAction(update_action)
        menu.addAction(delete_action)

        menu.popup(global_pos)

    @pyqtSlot()
    def on_create_product(self):
        self.re_create_product_dialog = DialogCreateREProduct(self)
        self.re_create_product_dialog.request_new_pid_signal.connect(
            self.handle_new_pid
        )
        self.re_create_product_dialog.product_data_signal.connect(
            self.handle_create_new_product
        )
        self.re_create_product_dialog.show()

    @pyqtSlot(int)
    def on_update_product(self, record_id: int):
        product_info = self._product_controller.read_product(record_id)
        product_images = self._product_controller.get_images_by_path(
            product_info.image_dir
        )
        self.re_update_re_dialog = DialogUpdateREProduct(
            image_paths=product_images,
            product_data=product_info,
            parent=self,
        )
        self.re_update_re_dialog.product_data_signal.connect(self.handle_update_product)
        self.re_update_re_dialog.show()

    @pyqtSlot(str)
    def handle_new_pid(self, transaction_type: str):
        new_pid = self._product_controller.initialize_new_pid(transaction_type)
        if hasattr(self, "re_create_product_dialog"):
            self.re_create_product_dialog.pid_input.setText(new_pid)

    @pyqtSlot(list, RealEstateProductType)
    def handle_create_new_product(
        self, image_paths: List[str], product_data: RealEstateProductType
    ):
        self.udd_container_dir = self._setting_controller.get_selected_user_data_dir()
        if not self.udd_container_dir:
            QMessageBox.critical(
                self,
                "ERROR",
                "The 'user_data_dir' path is not accessible. Please check your settings.",
            )
            return False
        self._product_controller.create_product(
            os.path.join(self.udd_container_dir, "..", "images"),
            image_paths,
            product_data,
        )

    @pyqtSlot(int)
    def handle_delete_product(self, record_id: int):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this product?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._product_controller.delete_product(record_id)

    @pyqtSlot()
    def handle_change_status(self):
        selected_ids = self.get_selected_ids()
        if len(selected_ids):
            self._product_controller.toggle_status(selected_ids[0])

    @pyqtSlot(RealEstateProductType)
    def handle_update_product(self, product_data: RealEstateProductType):
        self._product_controller.update_product(
            record_id=product_data.id, product_data=product_data
        )

    @pyqtSlot(QItemSelection, QItemSelection)
    def on_selection_changed(
        self,
        selected: QItemSelection,
        deselected: QItemSelection,
    ):
        if not selected.indexes():
            self.details_container_w.setHidden(True)
            return
        selected_index = selected.indexes()[0]
        row = selected_index.row()
        item_id = self.proxy_product_model.data(
            self.proxy_product_model.index(row, 0), Qt.ItemDataRole.DisplayRole
        )
        self.current_product = self._product_controller.read_product(item_id)
        self.current_image_paths = self._product_controller.get_images_by_path(
            self.current_product.image_dir
        )
        self.details_container_w.setHidden(False)
        self.image_label.mousePressEvent = self.on_image_clicked
        self.set_product_details("default")

    @pyqtSlot(str)
    def set_product_details(self, _type: str):
        self.display_image(self.current_image_paths)
        if _type == "default":
            title_template: str = self._template_controller.get_default(
                "title",
                self.current_product.transaction_type,
                self.current_product.category,
            )
            description_template: str = self._template_controller.get_default(
                "description",
                self.current_product.transaction_type,
                self.current_product.category,
            )
        elif _type == "random":
            title_template: str = self._template_controller.get_random(
                "title",
                self.current_product.transaction_type,
                self.current_product.category,
            )
            description_template: str = self._template_controller.get_random(
                "description",
                self.current_product.transaction_type,
                self.current_product.category,
            )
        title = replace_template(self.current_product, title_template)
        # title = title[:100]
        description = replace_template(self.current_product, description_template)
        footer = init_footer_content(self.current_product)
        self.detail_text.setPlainText(f"{title.upper()} \n\n {description} \n{footer}")

    def display_image(self, image_paths: List[str]):
        if not len(image_paths):
            self.image_label.setText("Failed to load image.")
            return
        pixmap = QPixmap(image_paths[0])
        if not pixmap.isNull():
            self.image_label.setPixmap(
                pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.image_label.setText("Failed to load image.")

    @pyqtSlot(QMouseEvent)
    def on_image_clicked(self, ev: QMouseEvent):
        if not self.current_image_paths:
            return
        image_path = self.current_image_paths[0]
        folder_path = os.path.dirname(image_path)
        if os.path.exists(folder_path):
            if sys.platform == "darwin":
                os.system(f'open "{folder_path}"')
            elif sys.platform.startswith("win"):
                os.startfile(folder_path)
            else:
                os.system(f'xdg-open "{folder_path}"')

    @pyqtSlot()
    def on_export_clicked(self):
        file_path = dialog_save_file(self)
        if not file_path:
            return
        is_exported = self._product_controller.export_to_file(file_path=file_path)
        if is_exported:
            QMessageBox.about(self, "Exported file", f"Export to {file_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to export data")

    @pyqtSlot()
    def on_import_clicked(self):
        file_path = dialog_open_file(self)
        if not file_path:
            return
        is_imported = self._product_controller.import_products(file_path)
        if is_imported:
            QMessageBox.about(self, "Imported file", f"Import to {file_path}")
        else:
            QMessageBox.critical(self, "Error", "Failed to import data")
