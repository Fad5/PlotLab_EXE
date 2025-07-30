import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from views.main_window import YoungModulusApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)
    
    window = YoungModulusApp()
    window.show()
    sys.exit(app.exec_())