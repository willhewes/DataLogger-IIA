import sys
from PyQt6 import QtWidgets
from gui import SerialPlotter

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = SerialPlotter(port='COM11')  # Adjust port if needed
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
