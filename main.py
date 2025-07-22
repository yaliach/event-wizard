# main.py
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.gui.main_window import LogViewer

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('app/resources/icon.ico'))
    viewer = LogViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
