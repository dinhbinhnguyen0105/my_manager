# src/main.py
import sys
from PyQt6.QtWidgets import QApplication
from src.app import Application


def main():
    app = QApplication(sys.argv)
    application = Application()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
