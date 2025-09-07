# src/app.py
from src.database.user_database import initialize_user_database
from src.database.product_database import initialize_product_database
from src.database.setting_database import initialize_setting_database
from src.models.user_model import UserModel, UserListedProductModel
from src.models.product_model import (
    MiscProductModel,
    RealEstateProductModel,
    RealEstateTemplateModel,
)
from src.models.setting_model import SettingProxyModel, SettingUserDataDirModel
from src.services.user_service import UserService, UserListedProductService
from src.services.product_service import (
    RealEstateProductService,
    RealEstateTemplateService,
    MiscProductService,
)
from src.services.setting_service import SettingProxyService, SettingUserDataDirService
from src.controllers.user_controller import UserController, UserListedProductController
from src.controllers.product_controller import (
    RealEstateProductController,
    RealEstateTemplateController,
    MiscProductController,
)
from src.controllers.setting_controller import (
    SettingProxyController,
    SettingUserDataDirController,
)
from src.controllers.robot_controller import RobotController

from src.views.mainwindow import MainWindow


class Application:
    def __init__(self):
        self.initial_database()
        user_model = UserModel()
        user_listed_product_model = UserListedProductModel()
        real_estate_product_model = RealEstateProductModel()
        real_estate_template_model = RealEstateTemplateModel()
        misc_product_model = MiscProductModel()
        setting_proxy_model = SettingProxyModel()
        setting_user_data_dir_model = SettingUserDataDirModel()

        user_service = UserService(user_model)
        user_listed_product_service = UserListedProductService(
            user_listed_product_model
        )
        real_estate_product_service = RealEstateProductService(
            real_estate_product_model
        )
        real_estate_template_service = RealEstateTemplateService(
            real_estate_template_model
        )
        misc_product_service = MiscProductService(misc_product_model)
        setting_proxy_service = SettingProxyService(setting_proxy_model)
        setting_user_data_dir_service = SettingUserDataDirService(
            setting_user_data_dir_model
        )

        user_controller = UserController(user_service)
        user_listed_product_controller = UserListedProductController(
            user_listed_product_service
        )
        real_estate_product_controller = RealEstateProductController(
            real_estate_product_service
        )
        real_estate_template_controller = RealEstateTemplateController(
            real_estate_template_service
        )
        misc_product_controller = MiscProductController(misc_product_service)
        setting_proxy_controller = SettingProxyController(setting_proxy_service)
        setting_user_data_dir_controller = SettingUserDataDirController(
            setting_user_data_dir_service
        )
        robot_controller = RobotController(
            user_service=user_service,
            misc_product_service=misc_product_service,
            re_product_service=real_estate_product_service,
            re_template_service=real_estate_template_service,
            setting_proxy_service=setting_proxy_service,
            setting_udd_service=setting_user_data_dir_service,
        )
        self.mainWindow = MainWindow(
            user_controller=user_controller,
            robot_controller=robot_controller,
            user_listed_product_controller=user_listed_product_controller,
            real_estate_product_controller=real_estate_product_controller,
            real_estate_template_controller=real_estate_template_controller,
            misc_product_controller=misc_product_controller,
            setting_proxy_controller=setting_proxy_controller,
            setting_user_data_dir_controller=setting_user_data_dir_controller,
        )
        self.mainWindow.show()

    def initial_database(self):
        if not initialize_product_database():
            raise Exception("Initialize product database failed!")
        if not initialize_user_database():
            raise Exception("Initialize user database failed!")
        if not initialize_setting_database():
            raise Exception("Initialize setting database failed!")
