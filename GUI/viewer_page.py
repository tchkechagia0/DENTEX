# viewer_page.py
import os
from PySide6 import QtCore, QtGui, QtWidgets
import json
from collections import defaultdict
class ImageView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.setRenderHints(QtGui.QPainter.Antialiasing |
                            QtGui.QPainter.SmoothPixmapTransform |
                            QtGui.QPainter.TextAntialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self._pix_item = None
        self._zoom = 0

    def load_image(self, path: str):
        pix = QtGui.QPixmap(path)
        if pix.isNull():
            return False
        self.scene().clear()
        self._pix_item = self.scene().addPixmap(pix)
        self.scene().setSceneRect(pix.rect())
        self._zoom = 0
        self.fitInView(self.sceneRect(), QtCore.Qt.KeepAspectRatio)
        return True

    def wheelEvent(self, event: QtGui.QWheelEvent):
        if self._pix_item is None:
            return super().wheelEvent(event)
        delta = event.angleDelta().y()
        factor = 1.25 if delta > 0 else 0.8
        if delta > 0 and self._zoom > 40:
            return
        if delta < 0 and self._zoom < -10:
            return
        self._zoom += (1 if delta > 0 else -1)
        self.scale(factor, factor)


class ViewerPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.image_path = None
        self.json_type = None

        root = QtWidgets.QHBoxLayout(self)

        # SOL – Görsel
        self.view = ImageView()
        root.addWidget(self.view, 3)

        # SAĞ – Bilgi + Kontroller
        right = QtWidgets.QVBoxLayout()

        # --- Dosya Bilgisi ---
        self.grp_info = QtWidgets.QGroupBox("Bilgiler")
        info_lay = QtWidgets.QFormLayout(self.grp_info)
        self.lbl_img = QtWidgets.QLabel("—")
        self.lbl_type = QtWidgets.QLabel("—")
        info_lay.addRow("Fotoğraf:", self.lbl_img)
        info_lay.addRow("JSON Türü:", self.lbl_type)
        right.addWidget(self.grp_info)

        # --- Checkbox Paneli ---
        self.grp_controls = QtWidgets.QGroupBox("Görüntü Seçenekleri")
        self.controls_layout = QtWidgets.QVBoxLayout(self.grp_controls)
        right.addWidget(self.grp_controls)

        right.addStretch(1)

        right_wrap = QtWidgets.QWidget()
        right_wrap.setLayout(right)
        right_wrap.setFixedWidth(300)
        root.addWidget(right_wrap)

        
        self._json_data = None
        self._items = []  # sahneye eklenen overlay öğeleri (bbox, polygon, label)

        # Checkbox’ları oluştur
        self.create_checkboxes()
        # Çizim tetikleyici
        for cb in [self.cb_quad_bbox, self.cb_quad_mask, self.cb_teeth_bbox,
                   self.cb_teeth_mask, self.cb_disease_mask, self.cb_disease_bbox, self.cb_text]:
            cb.stateChanged.connect(self.on_checkbox_changed)

    def create_checkboxes(self):
        """Tüm checkbox butonları oluşturulur."""
        self.cb_quad_bbox = QtWidgets.QCheckBox("Quadrant BBox")
        self.cb_quad_mask = QtWidgets.QCheckBox("Quadrant Mask")
        self.cb_teeth_bbox = QtWidgets.QCheckBox("Teeth BBox")
        self.cb_teeth_mask = QtWidgets.QCheckBox("Teeth Mask")
        self.cb_disease_mask = QtWidgets.QCheckBox("Disease Mask")
        self.cb_disease_bbox = QtWidgets.QCheckBox("Disease BBox")
        self.cb_text = QtWidgets.QCheckBox("Text Labels")

        # Checkbox’ları panele ekle
        self.controls_layout.addWidget(self.cb_quad_bbox)
        self.controls_layout.addWidget(self.cb_quad_mask)
        self.controls_layout.addWidget(self.cb_teeth_bbox)
        self.controls_layout.addWidget(self.cb_teeth_mask)
        self.controls_layout.addWidget(self.cb_disease_mask)
        self.controls_layout.addWidget(self.cb_disease_bbox)
        self.controls_layout.addWidget(self.cb_text)
        self.controls_layout.addStretch(1)

        # Checkbox değişiminde yeniden çizim olacak (şimdilik pasif)
        for cb in [self.cb_quad_bbox, self.cb_quad_mask, self.cb_teeth_bbox,
                   self.cb_teeth_mask, self.cb_disease_mask, self.cb_disease_bbox, self.cb_text]:
            cb.stateChanged.connect(self.on_checkbox_changed)

    def set_checkbox_states(self):
        """JSON tipine göre checkbox aktif/pasif yapılır."""
        if self.json_type == "Quadrant":
            self.cb_quad_bbox.setEnabled(True)
            self.cb_quad_mask.setEnabled(True)
            self.cb_teeth_bbox.setEnabled(False)
            self.cb_teeth_mask.setEnabled(False)
            self.cb_disease_mask.setEnabled(False)
            self.cb_disease_bbox.setEnabled(False)
            self.cb_text.setEnabled(True)

        elif self.json_type == "Enumeration":
            self.cb_quad_bbox.setEnabled(False)
            self.cb_quad_mask.setEnabled(False)
            self.cb_teeth_bbox.setEnabled(True)
            self.cb_teeth_mask.setEnabled(True)
            self.cb_disease_mask.setEnabled(False)
            self.cb_disease_bbox.setEnabled(False)
            self.cb_text.setEnabled(True)

        elif self.json_type == "Disease":
            self.cb_quad_bbox.setEnabled(False)
            self.cb_quad_mask.setEnabled(False)
            self.cb_teeth_bbox.setEnabled(False)
            self.cb_teeth_mask.setEnabled(False)
            self.cb_disease_mask.setEnabled(True)
            self.cb_disease_bbox.setEnabled(True)
            self.cb_text.setEnabled(True)

    def load_case(self, image_path: str, json_path: str, json_type: str):
        """LoaderPage'den gelen veriyi alır."""
        self.image_path = image_path
        self.json_type = json_type

        ok = self.view.load_image(self.image_path)
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Hata", "Görsel yüklenemedi.")
            return

        self.lbl_img.setText(os.path.basename(self.image_path))
        self.lbl_type.setText(self.json_type)
        self.set_checkbox_states()
        
        self._current_image_id = self._find_image_id_from_filename(self.image_path)
        if self._current_image_id is None:
            QtWidgets.QMessageBox.warning(self, "Uyarı", "image_id bulunamadı, tüm anotasyonlar çizilebilir!")


    def on_checkbox_changed(self):
        """Checkbox değişikliklerinde çalışacak (çizim motoru bağlanacak)."""
        pass  # Daha sonra buraya Drow fonksiyonlarını ekleyeceğiz
    def load_case(self, image_path: str, json_path: str, json_type: str):
        """LoaderPage'den gelen veriyi alır, resmi açar, JSON'u yükler ve çizer."""
        self.image_path = image_path
        self.json_type = json_type

        ok = self.view.load_image(self.image_path)
        if not ok:
            QtWidgets.QMessageBox.warning(self, "Hata", "Görsel yüklenemedi.")
            return

        # Sadece dosya adı göster
        self.lbl_img.setText(os.path.basename(self.image_path))
        self.lbl_type.setText(self.json_type)

        # JSON'u belleğe al (UI'da yolu göstermiyoruz)
        self._json_data = self._load_json(json_path)

        # Checkbox durumlarını ayarla ve çiz
        self.set_checkbox_states()
        self.draw_all()

    def _load_json(self, path: str):
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return data
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "JSON Hatası", f"JSON okunamadı:\n{e}")
            return None

    def on_checkbox_changed(self):
        self.draw_all()

    def clear_overlays(self):
        """Önceki çizimleri sahneden temizle."""
        if not self.view.scene():
            return
        for it in self._items:
            self.view.scene().removeItem(it)
        self._items.clear()
    
    def _find_image_id_from_filename(self, filename):
        #JSON içindeki images bölümünden, eşleşen file_name'e göre image_id bulur.
        if self._json_data is None:
            return None

        images = self._json_data.get("images", [])
        base_name = os.path.basename(filename)

        for img in images:
            if img.get("file_name") == base_name:
                return img.get("id")

        return None

    # ----------------------
    # ANA ÇİZİM YÜRÜTÜCÜSÜ
    # ----------------------
    def draw_all(self):
        current_id = self._find_image_id_from_filename(self.image_path)
        
        """Seçili checkbox'lara ve JSON tipine göre her şeyi yeniden çizer."""
        if self._json_data is None or self.view._pix_item is None:
            return

        self.clear_overlays()

        anns = self._json_data.get("annotations", [])
        # Kategori ad sözlükleri (id->isim)
        cat = self._index_categories(self._json_data)

        # Hızlı erişim için: hastalık id->renk
        disease_colors = self._disease_color_map(cat.get("categories_3", {}))

        # Hangi katmanda ne çizileceğine karar verelim
        draw_quad_bbox   = self.cb_quad_bbox.isChecked()   and self.json_type == "Quadrant"
        draw_quad_mask   = self.cb_quad_mask.isChecked()   and self.json_type == "Quadrant"
        draw_teeth_bbox  = self.cb_teeth_bbox.isChecked()  and self.json_type == "Enumeration"
        draw_teeth_mask  = self.cb_teeth_mask.isChecked()  and self.json_type == "Enumeration"
        draw_dis_mask    = self.cb_disease_mask.isChecked() and self.json_type == "Disease"
        draw_dis_bbox    = self.cb_disease_bbox.isChecked() and self.json_type == "Disease"
        draw_text        = self.cb_text.isChecked()

        for a in anns:
            if a.get("image_id") != current_id:
                continue
            # Ortak alanlar güvenli şekilde alınır
            bbox = a.get("bbox")  # [x, y, w, h]
            segs = a.get("segmentation") or []

            # Etiket parçaları
            q_id = a.get("category_id") if self.json_type == "Quadrant" else a.get("category_id_1")
            t_id = a.get("category_id_2")
            d_id = a.get("category_id_3")

            q_name = cat["categories"].get(q_id) if self.json_type == "Quadrant" else cat["categories_1"].get(q_id)
            t_name = cat["categories_2"].get(t_id) if t_id is not None else None
            d_name = cat["categories_3"].get(d_id) if d_id is not None else None

            # 1) QUADRANT: bbox/mask
            if self.json_type == "Quadrant":
                if draw_quad_bbox and bbox:
                    self._items.append(self.draw_bbox(bbox, pen=QtGui.QPen(QtGui.QColor(220, 0, 0), 2.0)))
                if draw_quad_mask and segs:
                    self._items.extend(self.draw_polygons(segs, fill=QtGui.QColor(220, 0, 0, 70),
                                                          outline=QtGui.QColor(220, 0, 0), outline_w=1.5))

            # 2) ENUMERATION: diş bbox/mask
            elif self.json_type == "Enumeration":
                if draw_teeth_bbox and bbox:
                    self._items.append(self.draw_bbox(bbox, pen=QtGui.QPen(QtGui.QColor(220, 0, 0), 2.0)))
                if draw_teeth_mask and segs:
                    self._items.extend(self.draw_polygons(segs, fill=QtGui.QColor(0, 140, 255, 70),
                                                          outline=QtGui.QColor(0, 140, 255), outline_w=1.5))

            # 3) DISEASE: sadece hastalıklı dişler var → disease bbox/mask
            elif self.json_type == "Disease":
                color = disease_colors.get(d_id, QtGui.QColor(240, 180, 0))  # fallback
                if draw_dis_bbox and bbox:
                    pen = QtGui.QPen(color, 2.0)
                    self._items.append(self.draw_bbox(bbox, pen=pen))
                if draw_dis_mask and segs:
                    fill = QtGui.QColor(color.red(), color.green(), color.blue(), 70)
                    self._items.extend(self.draw_polygons(segs, fill=fill, outline=color, outline_w=1.5))

            # 4) TEXT LABELS (kısa format A)
            if draw_text:
                label = self._build_short_label(self.json_type, q_name, t_name, d_name)
                if label:
                    # Yazıyı bbox üstüne, yoksa polygon centroid'ine koy
                    pos = None
                    if bbox:
                        x, y, w, h = bbox
                        pos = QtCore.QPointF(x, y - 4)  # kutunun üstüne koy
                    elif segs:
                        pos = self._polygon_centroid(segs[0])  # ilk halkadan centroid
                    if pos:
                        self._items.append(self.draw_label(label, pos))

        # Görseli kadraja iyi sığdırmak için (isteğe bağlı)
        # self.view.fitInView(self.view.sceneRect(), QtCore.Qt.KeepAspectRatio)

    # ----------------------
    # YARDIMCI: KATEGORİ İNDEKSLERİ
    # ----------------------
    def _index_categories(self, data):
        """categories / categories_1 / categories_2 / categories_3 -> {id: name} sözlükleri döner."""
        out = {
            "categories": {},
            "categories_1": {},
            "categories_2": {},
            "categories_3": {},
        }
        if "categories" in data:
            for c in data["categories"]:
                out["categories"][c.get("id")] = c.get("name")
        if "categories_1" in data:
            for c in data["categories_1"]:
                out["categories_1"][c.get("id")] = c.get("name")
        if "categories_2" in data:
            for c in data["categories_2"]:
                out["categories_2"][c.get("id")] = c.get("name")
        if "categories_3" in data:
            for c in data["categories_3"]:
                out["categories_3"][c.get("id")] = c.get("name")
        return out

    def _disease_color_map(self, id2name: dict):
        """Hastalık adlarına göre tutarlı renk seç (4 hastalık varsayımıyla)."""
        palette = [
            QtGui.QColor(220, 20, 60),   # crimson
            QtGui.QColor(65, 105, 225),  # royal blue
            QtGui.QColor(50, 205, 50),   # lime green
            QtGui.QColor(255, 140, 0),   # dark orange
        ]
        mapping = {}
        for i, k in enumerate(sorted(id2name.keys(), key=lambda x: int(x) if isinstance(x, int) else 0)):
            mapping[k] = palette[i % len(palette)]
        return mapping

    # ----------------------
    # ÇİZİM PRİMİTİFLERİ
    # ----------------------
    def draw_bbox(self, bbox, pen=None):
        """[x,y,w,h] dikdörtgeni çizer."""
        x, y, w, h = bbox
        rect = QtCore.QRectF(x, y, w, h)
        item = self.view.scene().addRect(rect, pen or QtGui.QPen(QtGui.QColor(220, 0, 0), 2.0))
        item.setZValue(10)
        return item

    def draw_polygons(self, segmentation, fill: QtGui.QColor, outline: QtGui.QColor, outline_w=1.5):
        """COCO-style segmentation: [[x1,y1,x2,y2,...], ...]"""
        items = []
        for ring in segmentation:
            pts = self._flat_to_qpolygonf(ring)
            path = QtGui.QPainterPath()
            if len(pts) > 0:
                path.addPolygon(pts)
                path.closeSubpath()
            item = self.view.scene().addPath(
                path,
                QtGui.QPen(outline, outline_w),
                QtGui.QBrush(fill)
            )
            item.setZValue(8)
            items.append(item)
        return items

    def draw_label(self, text: str, pos: QtCore.QPointF):
        """Kısa metin etiketi (kutu üstü)."""
        # Arka planlı metin için basit bir TextItem
        item = QtWidgets.QGraphicsSimpleTextItem(text)
        font = item.font()
        font.setPointSizeF(10.0)
        item.setFont(font)
        item.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0)))  # siyah yazı
        item.setPos(pos)

        # Beyaz yarı saydam arkaplan
        pad = 3
        br = item.boundingRect()
        bg = self.view.scene().addRect(
            QtCore.QRectF(pos.x() - pad, pos.y() - pad, br.width() + 2*pad, br.height() + 2*pad),
            QtGui.QPen(QtCore.Qt.NoPen),
            QtGui.QBrush(QtGui.QColor(255, 255, 255, 190))
        )
        bg.setZValue(11)
        item.setZValue(12)
        self.view.scene().addItem(item)

        # Z-order ve gruplama benzeri kontrol için listede ikisini de tut
        return_group = QtWidgets.QGraphicsItemGroup()
        self.view.scene().addItem(return_group)
        return_group.addToGroup(bg)
        return_group.addToGroup(item)
        return_group.setZValue(12)
        return return_group

    # ----------------------
    # ETİKET, GEOMETRİ YARDIMCILARI
    # ----------------------
    def _flat_to_qpolygonf(self, flat):
        """[x1,y1,x2,y2,...] -> QPolygonF"""
        it = iter(flat)
        pts = [QtCore.QPointF(float(x), float(y)) for x, y in zip(it, it)]
        poly = QtGui.QPolygonF(pts)
        return poly

    def _polygon_centroid(self, flat):
        """Düz liste (x1,y1,...) için centroid hesapla."""
        it = iter(flat)
        pts = [(float(x), float(y)) for x, y in zip(it, it)]
        if not pts:
            return QtCore.QPointF(0, 0)
        # basit centroid
        xs = sum(p[0] for p in pts) / len(pts)
        ys = sum(p[1] for p in pts) / len(pts)
        return QtCore.QPointF(xs, ys)

    def _build_short_label(self, json_type, q_name, t_name, d_name):
        """Kısa format A: Quadrant -> 'Q:1', Enumeration -> 'Q:1 T:3', Disease -> 'Q:1 T:3 D:xyz'."""
        if json_type == "Quadrant":
            if q_name: return f"Q:{q_name}"
        elif json_type == "Enumeration":
            parts = []
            if q_name: parts.append(f"Q:{q_name}")
            if t_name: parts.append(f"T:{t_name}")
            return " ".join(parts) if parts else ""
        elif json_type == "Disease":
            parts = []
            if q_name: parts.append(f"Q:{q_name}")
            if t_name: parts.append(f"T:{t_name}")
            if d_name: parts.append(f"D:{d_name}")
            return " ".join(parts) if parts else ""
        return ""    