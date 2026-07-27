# -*- coding: utf-8 -*-
"""
Conversor Multi-Formato — Vídeos, Fotos e Documentos
Interface PyQt5 dark mode com gradiente roxo-azul.

Execução:
    python main.py

Build para .exe:
    ver README.md
"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QComboBox, QFileDialog, QProgressBar,
    QGroupBox, QCheckBox, QSlider, QSpinBox, QListWidget, QMessageBox,
    QStatusBar, QAbstractItemView,
)

from styles import DARK_STYLESHEET
from workers import (
    VideoConvertWorker, PhotoConvertWorker, DocConvertWorker,
    COMPRESSION_PRESETS,
)

VIDEO_FORMATS = ["mp4", "avi", "mkv", "webm", "mov", "flv", "wmv"]
PHOTO_FORMATS = ["jpg", "png", "webp", "bmp", "tiff"]
DOC_INPUT_EXT = ["pdf", "docx", "doc", "pptx", "ppt", "xlsx", "xls", "txt", "odt"]
DOC_OUTPUT_BY_INPUT = {
    "pdf": ["docx", "txt", "odt"],
    "docx": ["pdf", "odt", "txt"],
    "doc": ["pdf", "docx", "odt"],
    "pptx": ["pdf", "odp"],
    "ppt": ["pdf", "pptx"],
    "xlsx": ["pdf", "csv", "ods"],
    "xls": ["pdf", "xlsx", "csv"],
    "txt": ["pdf", "docx", "odt"],
    "odt": ["pdf", "docx", "txt"],
}


# --------------------------------------------------------------------------
# Aba Vídeos
# --------------------------------------------------------------------------

class VideoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = ""
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Seleção de arquivo
        file_group = QGroupBox("Arquivo de entrada")
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Nenhum arquivo selecionado")
        self.file_label.setObjectName("hint")
        btn_select = QPushButton("Selecionar vídeo…")
        btn_select.setObjectName("secondary")
        btn_select.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(btn_select)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Formato + compressão
        opts_group = QGroupBox("Opções de conversão")
        opts_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Formato de saída:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(VIDEO_FORMATS)
        row1.addWidget(self.format_combo)
        row1.addStretch()
        opts_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.compress_check = QCheckBox("Compressão inteligente")
        self.compress_check.setChecked(True)
        self.compress_check.stateChanged.connect(self._toggle_compression)
        row2.addWidget(self.compress_check)
        self.level_combo = QComboBox()
        self.level_combo.addItems(list(COMPRESSION_PRESETS.keys()))
        self.level_combo.setCurrentIndex(1)
        row2.addWidget(self.level_combo)
        row2.addStretch()
        opts_layout.addLayout(row2)

        hint = QLabel(
            "A compressão inteligente reduz o tamanho do arquivo mantendo "
            "a resolução original (ajusta apenas a taxa de qualidade)."
        )
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        opts_layout.addWidget(hint)

        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)

        # Progresso
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)

        # Botões
        btn_layout = QHBoxLayout()
        self.convert_btn = QPushButton("Converter")
        self.convert_btn.clicked.connect(self.start_conversion)
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setObjectName("secondary")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        btn_layout.addWidget(self.convert_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _toggle_compression(self):
        self.level_combo.setEnabled(self.compress_check.isChecked())

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar vídeo", "",
            "Vídeos (*.mp4 *.avi *.mkv *.webm *.mov *.flv *.wmv);;Todos os arquivos (*)"
        )
        if path:
            self.input_path = path
            self.file_label.setText(os.path.basename(path))

    def start_conversion(self):
        if not self.input_path:
            QMessageBox.warning(self, "Atenção", "Selecione um arquivo de vídeo primeiro.")
            return

        out_format = self.format_combo.currentText()
        default_name = os.path.splitext(os.path.basename(self.input_path))[0] + f".{out_format}"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar vídeo como", default_name, f"*.{out_format}"
        )
        if not save_path:
            return

        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)

        self.worker = VideoConvertWorker(
            input_path=self.input_path,
            output_path=save_path,
            output_format=out_format,
            compress_enabled=self.compress_check.isChecked(),
            compression_level=self.level_combo.currentText(),
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished_ok.connect(self.on_success)
        self.worker.finished_error.connect(self.on_error)
        self.worker.start()

    def cancel_conversion(self):
        if self.worker:
            self.worker.cancel()

    def on_success(self, out_path):
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        QMessageBox.information(self, "Concluído", f"Vídeo convertido com sucesso:\n{out_path}")

    def on_error(self, message):
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Erro na conversão", message)


# --------------------------------------------------------------------------
# Aba Fotos
# --------------------------------------------------------------------------

class PhotoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.input_paths = []
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        file_group = QGroupBox("Fotos selecionadas")
        file_layout = QVBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.file_list.setMaximumHeight(120)
        file_layout.addWidget(self.file_list)

        btn_row = QHBoxLayout()
        btn_select = QPushButton("Selecionar fotos…")
        btn_select.setObjectName("secondary")
        btn_select.clicked.connect(self.select_files)
        btn_clear = QPushButton("Limpar lista")
        btn_clear.setObjectName("secondary")
        btn_clear.clicked.connect(self.clear_files)
        btn_row.addWidget(btn_select)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        file_layout.addLayout(btn_row)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        opts_group = QGroupBox("Opções de conversão")
        opts_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Formato de saída:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(PHOTO_FORMATS)
        row1.addWidget(self.format_combo)
        row1.addStretch()
        opts_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Redimensionar (%):"))
        self.resize_spin = QSpinBox()
        self.resize_spin.setRange(10, 100)
        self.resize_spin.setValue(100)
        self.resize_spin.setSuffix("%")
        row2.addWidget(self.resize_spin)
        row2.addSpacing(20)
        row2.addWidget(QLabel("Qualidade:"))
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(10, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.setFixedWidth(150)
        self.quality_label = QLabel("85")
        self.quality_slider.valueChanged.connect(
            lambda v: self.quality_label.setText(str(v))
        )
        row2.addWidget(self.quality_slider)
        row2.addWidget(self.quality_label)
        row2.addStretch()
        opts_layout.addLayout(row2)

        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        self.convert_btn = QPushButton("Converter")
        self.convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_btn)

        layout.addStretch()

    def select_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar fotos", "",
            "Imagens (*.jpg *.jpeg *.png *.webp *.bmp *.tiff);;Todos os arquivos (*)"
        )
        if paths:
            self.input_paths = paths
            self.file_list.clear()
            self.file_list.addItems([os.path.basename(p) for p in paths])

    def clear_files(self):
        self.input_paths = []
        self.file_list.clear()

    def start_conversion(self):
        if not self.input_paths:
            QMessageBox.warning(self, "Atenção", "Selecione ao menos uma foto.")
            return

        out_dir = QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino")
        if not out_dir:
            return

        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        self.worker = PhotoConvertWorker(
            input_paths=self.input_paths,
            output_dir=out_dir,
            output_format=self.format_combo.currentText(),
            resize_percent=self.resize_spin.value(),
            quality=self.quality_slider.value(),
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished_ok.connect(self.on_success)
        self.worker.finished_error.connect(self.on_error)
        self.worker.start()

    def on_success(self, success, total):
        self.convert_btn.setEnabled(True)
        QMessageBox.information(
            self, "Concluído", f"{success} de {total} fotos convertidas com sucesso."
        )

    def on_error(self, message):
        self.convert_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Erro na conversão", message)


# --------------------------------------------------------------------------
# Aba Documentos
# --------------------------------------------------------------------------

class DocTab(QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = ""
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        file_group = QGroupBox("Arquivo de entrada")
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Nenhum arquivo selecionado")
        self.file_label.setObjectName("hint")
        btn_select = QPushButton("Selecionar documento…")
        btn_select.setObjectName("secondary")
        btn_select.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(btn_select)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        opts_group = QGroupBox("Opções de conversão")
        opts_layout = QHBoxLayout()
        opts_layout.addWidget(QLabel("Formato de saída:"))
        self.format_combo = QComboBox()
        opts_layout.addWidget(self.format_combo)
        opts_layout.addStretch()
        opts_group.setLayout(opts_layout)
        layout.addWidget(opts_group)

        note = QLabel(
            "Conversão de documentos requer o LibreOffice instalado no "
            "computador (gratuito). Formatos disponíveis dependem do "
            "arquivo de entrada."
        )
        note.setObjectName("hint")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        layout.addWidget(self.progress_bar)

        self.convert_btn = QPushButton("Converter")
        self.convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_btn)

        layout.addStretch()

    def select_file(self):
        filt = "Documentos (*.pdf *.docx *.doc *.pptx *.ppt *.xlsx *.xls *.txt *.odt);;Todos os arquivos (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar documento", "", filt)
        if path:
            self.input_path = path
            self.file_label.setText(os.path.basename(path))
            ext = os.path.splitext(path)[1].lower().lstrip(".")
            self.format_combo.clear()
            options = DOC_OUTPUT_BY_INPUT.get(ext, ["pdf"])
            self.format_combo.addItems(options)

    def start_conversion(self):
        if not self.input_path:
            QMessageBox.warning(self, "Atenção", "Selecione um documento primeiro.")
            return
        if self.format_combo.count() == 0:
            QMessageBox.warning(self, "Atenção", "Formato de saída indisponível para este arquivo.")
            return

        out_dir = QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino")
        if not out_dir:
            return

        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)

        self.worker = DocConvertWorker(
            input_path=self.input_path,
            output_dir=out_dir,
            output_format=self.format_combo.currentText(),
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished_ok.connect(self.on_success)
        self.worker.finished_error.connect(self.on_error)
        self.worker.start()

    def on_success(self, out_path):
        self.convert_btn.setEnabled(True)
        QMessageBox.information(self, "Concluído", f"Documento convertido com sucesso:\n{out_path}")

    def on_error(self, message):
        self.convert_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, "Erro na conversão", message)


# --------------------------------------------------------------------------
# Janela principal
# --------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conversor Multi-Formato")
        self.resize(620, 560)
        self.setMinimumSize(560, 500)

        tabs = QTabWidget()
        tabs.addTab(VideoTab(), "Vídeos")
        tabs.addTab(PhotoTab(), "Fotos")
        tabs.addTab(DocTab(), "Documentos")
        self.setCentralWidget(tabs)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Pronto.")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
