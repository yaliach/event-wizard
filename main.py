# main.py
import sys
import base64
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QPixmap
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.gui.main_window import LogViewer
from app.resources.icon_base64 import ICON_DATA

def main():
    app = QApplication(sys.argv)
    
    # Load icon from embedded base64 data
    icon_data = base64.b64decode(ICON_DATA)
    pixmap = QPixmap()
    pixmap.loadFromData(icon_data)
    app.setWindowIcon(QIcon(pixmap))
    
    viewer = LogViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
