# main.py
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget
import sys
from loader_page import LoaderPage
from viewer_page import ViewerPage   # ← YENİ

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panoramik Etiket Görüntüleyici")
        self.setGeometry(200, 200, 1200, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.loader_page = LoaderPage()
        self.tabs.addTab(self.loader_page, "Dosya Yükle")

        self.viewer_page = ViewerPage()
        self.tabs.addTab(self .viewer_page, "Görüntüle")

        # Bağlantı: Yükleyici 'proceed' yaydığında viewer’a aktar ve sekmeye geç
        self.loader_page.proceed.connect(self.on_proceed)

    def on_proceed(self, image_path: str, json_path: str, json_type: str):
        self.viewer_page.load_case(image_path, json_path, json_type)
        self.tabs.setCurrentWidget(self.viewer_page)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
