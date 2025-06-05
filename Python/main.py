import sys
from PySide6 import QtWidgets
from gui import SerialPlotter

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = SerialPlotter(port='COM5')  # Adjust port if needed
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()