import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainTabWidget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainTabWidget()
    main_window.show()
    sys.exit(app.exec_())