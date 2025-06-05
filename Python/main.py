import sys
from PySide6 import QtWidgets, QtCore
from serial.tools import list_ports
from gui import SerialPlotter

def main():
    app = QtWidgets.QApplication(sys.argv)

    # Get list of available COM ports
    ports = list_ports.comports()
    if not ports:
        QtWidgets.QMessageBox.critical(None, "No COM Ports", "No COM ports found.")
        return

    # Select port
    port_descriptions = [p.description for p in ports]
    port_lookup = {p.description: p.device for p in ports}

    # Show dropdown dialog
    item, ok = QtWidgets.QInputDialog.getItem(
        None,
        "Select COM Port",
        "Available COM ports:",
        port_descriptions,
        0,
        False
    )

    if ok and item:
        selected_port = port_lookup[item]
        window = SerialPlotter(port=selected_port)
        window.show()
        sys.exit(app.exec())
    else:
        QtCore.QCoreApplication.quit()

if __name__ == "__main__":
    main()