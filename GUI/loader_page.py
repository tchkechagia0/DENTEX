# loader_page.py
import json
from PySide6 import QtCore
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox

class LoaderPage(QWidget):
    proceed = QtCore.Signal(str, str, str)  # image_path, json_path, json_type

    def __init__(self):
        super().__init__()
        self.image_path = None
        self.json_path = None
        self.json_type = None

        self.layout = QVBoxLayout()
        self.layout.addWidget(QLabel("<h2>📁 Fotoğraf ve JSON Yükle</h2>"))

        self.btn_image = QPushButton("🖼 Fotoğraf Seç (PNG)")
        self.btn_image.clicked.connect(self.select_image)
        self.layout.addWidget(self.btn_image)

        self.lbl_image = QLabel("Seçilen Fotoğraf: Henüz seçilmedi")
        self.layout.addWidget(self.lbl_image)

        self.btn_json = QPushButton("🧾 JSON Seç (.json)")
        self.btn_json.clicked.connect(self.select_json)
        self.layout.addWidget(self.btn_json)

        self.lbl_json = QLabel("Seçilen JSON: Henüz seçilmedi")
        self.layout.addWidget(self.lbl_json)

        self.btn_next = QPushButton("➡ Devam Et")
        self.btn_next.clicked.connect(self.proceed_next)
        self.layout.addWidget(self.btn_next)

        self.setLayout(self.layout)

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Fotoğraf Seç", "", "PNG Files (*.png)")
        if path:
            self.image_path = path
            self.lbl_image.setText(f"Seçilen Fotoğraf: {path}")

    def select_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "JSON Dosyası Seç", "", "JSON Files (*.json)")
        if path:
            self.json_path = path
            self.lbl_json.setText(f"Seçilen JSON: {path}")

    def detect_json_type(self):
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
            if "categories" in data and "categories_1" not in data:
                return "Quadrant"
            if "categories_1" in data and "categories_2" in data and "categories_3" not in data:
                return "Enumeration"
            if "categories_1" in data and "categories_2" in data and "categories_3" in data:
                return "Disease"
        except Exception:
            return None

    def proceed_next(self):
        if not self.image_path or not self.json_path:
            QMessageBox.warning(self, "Eksik Dosya", "Lütfen fotoğraf ve JSON dosyasını seçin!")
            return
        self.json_type = self.detect_json_type()
        if not self.json_type:
            QMessageBox.warning(self, "Hatalı JSON", "JSON formatı tanınmadı!")
            return
        # Ana pencereye haber ver
        self.proceed.emit(self.image_path, self.json_path, self.json_type)
