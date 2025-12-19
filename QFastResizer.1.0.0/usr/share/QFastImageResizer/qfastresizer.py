#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QRadioButton, QPushButton, 
                             QGroupBox, QMessageBox, QCheckBox, QFrame, QGridLayout)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PIL import Image

# Debian/Linux GNOME-GUI uyumluluğu için
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class QFastResizer(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_files = [] # Çoklu dosya desteği için liste
        self.initUI()

    def initUI(self):
        self.setWindowTitle('QFast Image Resizer')
        
        # İkonu script'in bulunduğu dizinden çek
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'QFast.png')
        self.setWindowIcon(QIcon(icon_path)) 
        
        self.setFixedWidth(500)

        main_layout = QVBoxLayout()

        # Sürükle-Bırak Alanı (Sabit Boyutlu)
        self.drop_label = QLabel('\n\nDrag-Drop Image(s) Here\n\n')
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setMinimumHeight(120) 
        self.drop_label.setStyleSheet("""
            border: 2px dashed #1a639b; border-radius: 10px;
            color: #1a639b; font-weight: bold; background-color: #f9f9f9;
        """)
        self.setAcceptDrops(True)
        main_layout.addWidget(self.drop_label)

        # Seçenekler Çerçevesi (Grid Düzeni)
        options_frame = QFrame()
        options_frame.setFrameShape(QFrame.StyledPanel)
        grid_layout = QGridLayout(options_frame)

        # Resolution Mode Bölümü
        self.rb_resolution = QRadioButton("Resolution Mode")
        self.rb_resolution.setChecked(True)
        self.rb_resolution.toggled.connect(self.toggle_modes)
        grid_layout.addWidget(self.rb_resolution, 0, 0)

        grid_layout.addWidget(QLabel("Width (px):"), 1, 0)
        self.edit_width = QLineEdit()
        self.edit_width.setPlaceholderText("Width")
        grid_layout.addWidget(self.edit_width, 2, 0)

        grid_layout.addWidget(QLabel("Height (px):"), 3, 0)
        self.edit_height = QLineEdit()
        self.edit_height.setPlaceholderText("Height")
        grid_layout.addWidget(self.edit_height, 4, 0)

        self.cb_keep_ratio = QCheckBox("Keep Aspect Ratio")
        self.cb_keep_ratio.setChecked(True)
        grid_layout.addWidget(self.cb_keep_ratio, 5, 0)

        # Percent Mode Bölümü
        self.rb_percent = QRadioButton("Percent Mode")
        self.rb_percent.toggled.connect(self.toggle_modes)
        grid_layout.addWidget(self.rb_percent, 0, 1)

        grid_layout.addWidget(QLabel("Enter (%):"), 1, 1)
        self.edit_percent = QLineEdit()
        self.edit_percent.setPlaceholderText("Example: 50")
        grid_layout.addWidget(self.edit_percent, 2, 1)

        main_layout.addWidget(options_frame)

        # Resampling (Yumuşatma) Ayarı
        resampling_group = QGroupBox("Resampling Method")
        resampling_layout = QHBoxLayout()
        self.rb_smooth = QRadioButton("Smooth (LANCZOS)")
        self.rb_smooth.setChecked(True)
        self.rb_pixel = QRadioButton("Pixelated (NEAREST)")
        resampling_layout.addWidget(self.rb_smooth)
        resampling_layout.addWidget(self.rb_pixel)
        resampling_group.setLayout(resampling_layout)
        main_layout.addWidget(resampling_group)

        # Butonlar
        btn_layout = QHBoxLayout()
        self.btn_do = QPushButton('Do!')
        self.btn_do.setFixedHeight(40)
        self.btn_do.setStyleSheet("""
            QPushButton {
                background-color: #1a639b;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_do.clicked.connect(self.process_image)

        self.btn_about = QPushButton('About')
        self.btn_about.setFixedHeight(40)
        self.btn_about.clicked.connect(self.show_about)

        btn_layout.addWidget(self.btn_do)
        btn_layout.addWidget(self.btn_about)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.update_ui_states()

    def toggle_modes(self):
        self.update_ui_states()
        if self.rb_resolution.isChecked(): 
            self.edit_percent.clear()
        else:
            self.edit_width.clear()
            self.edit_height.clear()

    def update_ui_states(self):
        res_active = self.rb_resolution.isChecked()
        self.edit_width.setEnabled(res_active)
        self.edit_height.setEnabled(res_active)
        self.cb_keep_ratio.setEnabled(res_active)
        self.edit_percent.setEnabled(not res_active)

    def reset_ui(self):
        """Arayüzü başlangıç durumuna döndürür."""
        self.selected_files = []
        self.drop_label.setText('\n\nDrag-Drop Image(s) Here\n\n')
        self.drop_label.setStyleSheet("""
            border: 2px dashed #1a639b; border-radius: 10px;
            color: #1a639b; font-weight: bold; background-color: #f9f9f9;
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): 
            event.accept()
        else: 
            event.ignore()

    def dropEvent(self, event):
        self.selected_files = [u.toLocalFile() for u in event.mimeData().urls()]
        if self.selected_files:
            file_count = len(self.selected_files)
            if file_count == 1:
                display_text = f"Selected: {os.path.basename(self.selected_files[0])}"
            else:
                display_text = f"{file_count} images selected for batch processing"
            
            self.drop_label.setText(f"\n\n{display_text}\n\n")
            self.drop_label.setStyleSheet("border: 2px solid #27ae60; color: #27ae60; background-color: #f0fff0;")

    def get_unique_path(self, directory, base_name, extension):
        counter = 0
        suffix = "_resized"
        while True:
            candidate_name = f"{base_name}{suffix}{f'_{counter}' if counter > 0 else ''}{extension}"
            full_path = os.path.join(directory, candidate_name)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

    def process_image(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Error", "Please drag and drop image(s) first!")
            return

        success_count = 0
        try:
            method = Image.LANCZOS if self.rb_smooth.isChecked() else Image.NEAREST
            
            for file_path in self.selected_files:
                img = Image.open(file_path)
                orig_w, orig_h = img.size
                
                if self.rb_resolution.isChecked():
                    w_text = self.edit_width.text()
                    h_text = self.edit_height.text()
                    
                    if self.cb_keep_ratio.isChecked():
                        if w_text and not h_text:
                            new_w = int(w_text)
                            new_h = int(orig_h * (new_w / orig_w))
                        elif h_text and not w_text:
                            new_h = int(h_text)
                            new_w = int(orig_w * (new_h / orig_h))
                        else:
                            new_w = int(w_text) if w_text else orig_w
                            new_h = int(h_text) if h_text else orig_h
                    else:
                        new_w = int(w_text) if w_text else orig_w
                        new_h = int(h_text) if h_text else orig_h
                else:
                    p = int(self.edit_percent.text()) / 100
                    new_w = int(orig_w * p)
                    new_h = int(orig_h * p)

                dir_name = os.path.dirname(file_path)
                base_name, ext = os.path.splitext(os.path.basename(file_path))
                output_path = self.get_unique_path(dir_name, base_name, ext)

                resized_img = img.resize((new_w, new_h), method)
                resized_img.save(output_path)
                success_count += 1
            
            QMessageBox.information(self, "Success", f"Successfully processed {success_count} image(s).")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        
        finally:
            self.reset_ui() # Her durumda arayüzü sıfırla

    def show_about(self):
        about_msg = QMessageBox(self)
        about_msg.setWindowTitle("About QFast Image Resizer")
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'QFast.png')
        
        # Logo kontrolü dinamik yol ile yapılıyor
        logo_html = f"<center><img src='{icon_path}' width='64' height='64'></center>" if os.path.exists(icon_path) else ""
        
        content = f"""
        {logo_html}
        <center><h2 style='color:#1a639b;'>QFast Image Resizer</h2></center>
        <div style='text-align: left; margin-left: 20px;'>
            <p><b>License:</b> GNU GPLv3<br>
            <b>Programming Language:</b> Python3<br>
            <b>Interface:</b> Qt5<br>
            <b>Author:</b> A. Serhat KILIÇOĞLU (shampuan)<br>
            <b>Github:</b> <a href='https://www.github.com/shampuan'>www.github.com/shampuan</a></p>
        </div>
        <hr>
        <center>
            <p>This program was prepared to resize your images quickly.</p>
            <p><i>This program comes with no warranty.</i></p>
            <p>Copyright © 2025 - A. Serhat KILIÇOĞLU</p>
        </center>
        """
        about_msg.setTextFormat(Qt.RichText)
        about_msg.setText(content)
        about_msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = QFastResizer()
    ex.show()
    sys.exit(app.exec_())
