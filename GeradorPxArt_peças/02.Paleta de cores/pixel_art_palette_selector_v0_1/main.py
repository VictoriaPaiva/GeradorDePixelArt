
import sys
from app.main_window import MainWindow
from PySide6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pixel Art Palette Selector")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
