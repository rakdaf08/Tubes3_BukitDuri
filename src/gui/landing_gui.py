import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QButtonGroup, QSizePolicy, QSpacerItem, QGraphicsOpacityEffect
)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QFont,QFontDatabase

class BukitDuriApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BUKIT DURI - Your CV Analyzer App")
        self.setFixedSize(1280, 720)
        self.setStyleSheet("background-color: #051010; color: #00E4AA;")
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #051010; color: #00E4AA;")
        wrapper = QVBoxLayout()
        wrapper.setAlignment(Qt.AlignCenter)

        # === LOGO ===
        logo_layout = QHBoxLayout()
        logo = QSvgWidget("src/gui/logo_bukdur.svg")
        logo.setFixedSize(344, 179)
        logo_layout.addWidget(logo, alignment=Qt.AlignCenter)

        # === Keywords ===
        keyword_label = QLabel("Keywords")
        keyword_label.setFont(QFont("Inter 24pt", 20))
        keyword_label.setAlignment(Qt.AlignLeft)

        keyword_input = QLineEdit()
        keyword_input.setPlaceholderText("React, Express, HTML")
        keyword_input.setFixedSize(900, 50)
        keyword_input.setStyleSheet("""
            background-color: #6D797A;
            color: white;
                
            border-radius: 8px;
            font-size: 20px;
        """)

        # === Methods ===
        method_label = QLabel("Methods")
        method_label.setFont(QFont("Inter 24pt", 20))
        method_label.setAlignment(Qt.AlignLeft)

        self.kmp_btn = QPushButton("KMP")
        self.bm_btn = QPushButton("BM")
        self.ac_btn = QPushButton("AC")

        self.method_group = QButtonGroup()
        self.method_group.setExclusive(True)
        for btn in [self.kmp_btn, self.bm_btn, self.ac_btn]:
            self.method_group.addButton(btn)
            btn.setCheckable(True)
            btn.setFixedSize(160, 50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #45786F;
                    color: #B1B1B1;
                    border-radius: 12px;
                    font-size: 20px;
                }
                QPushButton:checked {
                    background-color: #2BBA91;
                    color: #E8EDED;
                }
            """)
            self.add_fade_hover_effect(btn)

        method_buttons_layout = QHBoxLayout()
        method_buttons_layout.setSpacing(20)
        method_buttons_layout.addWidget(self.kmp_btn)
        method_buttons_layout.addWidget(self.bm_btn)
        method_buttons_layout.addWidget(self.ac_btn)

        method_box = QVBoxLayout()
        method_box.addWidget(method_label)
        method_box.addLayout(method_buttons_layout)

        # === Top Matches ===
        top_label = QLabel("Top Matches")
        top_label.setFont(QFont("Inter 24pt", 20))
        top_label.setAlignment(Qt.AlignLeft)

        top_input = QLineEdit()
        top_input.setPlaceholderText("3")
        top_input.setAlignment(Qt.AlignCenter)
        top_input.setFixedSize(100, 50)
        top_input.setStyleSheet("""
            background-color: #6D797A;
            color: #E8EDED;
            padding: 8px;
            border-radius: 8px;
            font-size: 20px;
        """)

        top_box = QVBoxLayout()
        top_box.addWidget(top_label)
        top_box.addWidget(top_input)

        # === Combine Method + Top Match ===
        row = QHBoxLayout()
        row.addLayout(method_box)
        row.addStretch()
        row.addLayout(top_box)
        row.setAlignment(Qt.AlignCenter)

        # === Search Button ===
        search_btn = QPushButton("Search")
        search_btn.setFixedSize(900, 50)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #0AD87E;
                color: #06312D;
                font-weight: bold;
                border-radius: 10px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #11f59b;
            }
        """)

        # === Final Input Layout ===
        main_form = QVBoxLayout()
        main_form.setSpacing(20)
        main_form.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        main_form.addWidget(keyword_label)
        main_form.addWidget(keyword_input)
        main_form.addLayout(row)
        main_form.addWidget(search_btn, alignment=Qt.AlignHCenter)

        form_container = QWidget()
        form_container.setLayout(main_form)
        form_container.setFixedWidth(900)

        # === Final Combine Layout ===
        wrapper.addLayout(logo_layout)
        wrapper.addSpacing(40)
        wrapper.addWidget(form_container, alignment=Qt.AlignHCenter)
        self.setLayout(wrapper)


    def add_fade_hover_effect(self, button):
        # Tambahkan animasi opacity ringan saat hover tombol
        effect = QGraphicsOpacityEffect(button)
        button.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(150)
        anim.setStartValue(0.6)
        anim.setEndValue(1.0)
        anim.setLoopCount(1)

        def on_enter():
            anim.setDirection(QPropertyAnimation.Forward)
            anim.start()

        def on_leave():
            anim.setDirection(QPropertyAnimation.Backward)
            anim.start()

        button.enterEvent = lambda e: on_enter()
        button.leaveEvent = lambda e: on_leave()

# === RUN APP ===
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font_path = os.path.join(os.path.dirname(__file__), "../gui/font/Inter_24pt-Regular.ttf")
    font_path = os.path.abspath(font_path)
    
    print(f"Trying to load font from: {font_path}")
    print(f"Font file exists: {os.path.exists(font_path)}")
    
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id != -1:
        families = QFontDatabase.applicationFontFamilies(font_id)
        print(f"Loaded font families: {families}")
        app.setFont(QFont("Inter 24pt", 10))
    else:
        print("Failed to load Inter font, using default Arial")
        app.setFont(QFont("Arial", 10))
    
    window = BukitDuriApp()
    window.show()
    sys.exit(app.exec_())
