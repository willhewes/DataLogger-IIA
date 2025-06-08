light_theme = """
    QWidget {
        background-color: #f0f0f0;
        color: #000;
    }
    QGroupBox {
        border: 1px solid gray;
        margin-top: 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 7px;
        padding: 0 5px 0 5px;
    }
    QLineEdit {
        padding: 4px;
        border: 1px solid #888;
        background-color: #fff;
        color: #000;
    }
    QPushButton {
        padding: 4px;
        border: 1px solid #888;
        background-color: #007acc;
        color: #fff;
        font-weight: bold;
    }
"""

dark_theme = """
    QWidget {
        background-color: #2e2e2e;
        color: #ccc;
    }
    QGroupBox {
        border: 1px solid #666;
        margin-top: 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 7px;
        padding: 0 5px 0 5px;
    }
    QLineEdit {
        padding: 4px;
        border: 1px solid #444;
        background-color: #3a3a3a;
        color: #eee;
    }
    QPushButton {
        padding: 4px;
        border: 1px solid #444;
        background-color: #007acc;
        color: #fff;
        font-weight: bold;
    }
"""

def apply_theme(widget, theme_name):
    if theme_name == "dark":
        widget.setStyleSheet(dark_theme)
    else:
        widget.setStyleSheet(light_theme)
