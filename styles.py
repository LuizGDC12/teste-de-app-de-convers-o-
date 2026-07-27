# -*- coding: utf-8 -*-
"""
Tema visual da aplicação: dark mode com gradiente roxo-azul.
"""

DARK_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #14141c;
    color: #e6e6f0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10.5pt;
}

QTabWidget::pane {
    border: 1px solid #2a2a3a;
    background-color: #1a1a24;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background: #1a1a24;
    color: #9a9ab0;
    padding: 10px 22px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
}

QTabBar::tab:selected {
    color: #ffffff;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6a3ee0, stop:1 #3e6ee0);
}

QTabBar::tab:hover:!selected {
    color: #cfcfe8;
}

QGroupBox {
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: 600;
    color: #b9b9d6;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QLabel {
    color: #d6d6e8;
}

QLabel#hint {
    color: #8888a0;
    font-size: 9pt;
}

QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b3ff2, stop:1 #3f7ff2);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 700;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #8a53f5, stop:1 #5390f5);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6531c9, stop:1 #3164c9);
}

QPushButton:disabled {
    background: #33334a;
    color: #77778c;
}

QPushButton#secondary {
    background: #23233299;
    border: 1px solid #3a3a52;
    color: #cfcfe8;
}

QPushButton#secondary:hover {
    background: #2c2c40;
}

QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #20202e;
    border: 1px solid #33334a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e6e6f0;
}

QComboBox:hover, QSpinBox:hover, QLineEdit:hover {
    border: 1px solid #5a5a8a;
}

QComboBox QAbstractItemView {
    background-color: #20202e;
    color: #e6e6f0;
    selection-background-color: #5a3ff2;
    border: 1px solid #33334a;
    outline: none;
}

QListWidget {
    background-color: #1a1a24;
    border: 1px solid #2a2a3a;
    border-radius: 6px;
    color: #d6d6e8;
}

QListWidget::item {
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #3f3f66;
    border-radius: 4px;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #2a2a3a;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b3ff2, stop:1 #3f7ff2);
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    width: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

QProgressBar {
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    background-color: #1a1a24;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
    height: 22px;
}

QProgressBar::chunk {
    border-radius: 7px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b3ff2, stop:0.5 #5c6bf5, stop:1 #3f9ff2);
}

QStatusBar {
    background-color: #14141c;
    color: #8888a0;
}

QScrollBar:vertical {
    background: #1a1a24;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #3a3a52;
    border-radius: 5px;
    min-height: 20px;
}
"""
