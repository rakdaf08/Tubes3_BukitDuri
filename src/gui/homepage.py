import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QCursor, QIcon
from PyQt5.QtCore import Qt, QSize

class CVCard(QWidget):
    def __init__(self, name, matches, skills, resume_id=None):
        super().__init__()
        self.resume_id = resume_id
        self.setFixedSize(350, 300)
        self.setStyleSheet("background-color: #1a1a1a;") 

        # === Outer Frame as a single card container ===
        card_frame = QFrame()
        card_frame.setStyleSheet("background-color: #006C54; border-radius: 20px;")
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 20, 20, 20)

        # === Name Label ===
        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", 28, QFont.Bold)) 
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: white;")
        card_layout.addWidget(name_label)

        # === Matches Label ===
        matches_label = QLabel(f"{matches} matches")
        matches_label.setFont(QFont("Arial", 14))
        matches_label.setAlignment(Qt.AlignCenter)
        matches_label.setStyleSheet("color: white;")
        card_layout.addWidget(matches_label)

        # === Skills Box ===
        skill_frame = QFrame()
        skill_frame.setFixedHeight(140) 
        skill_frame.setStyleSheet("background-color: #003B31; border-radius: 20px;")
        skill_layout = QVBoxLayout()
        skill_layout.setContentsMargins(15, 15, 15, 15) 

        for idx, (skill, count) in enumerate(skills.items(), 1):
            lbl = QLabel(f"{idx}. {skill} - {count} occurrence{'s' if count > 1 else ''}")
            lbl.setFont(QFont("Arial", 12))
            lbl.setStyleSheet("color: white;")
            skill_layout.addWidget(lbl)

        skill_frame.setLayout(skill_layout)
        card_layout.addWidget(skill_frame)

        # === Buttons Layout ===
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(10, 10, 10, 0)
        btn_layout.setSpacing(20) 

        view_more = QPushButton("View More")
        view_cv = QPushButton("View CV")
        view_more.clicked.connect(self.view_more_clicked)
        view_cv.clicked.connect(self.view_cv_clicked)

        for btn in (view_more, view_cv):
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: #CFFFEF;
                    font-weight: bold;
                    text-decoration: underline;
                    font-size: 13px;
                }
                QPushButton:hover {
                    color: #A5FFF0;
                }
            """)

        btn_layout.addWidget(view_more, alignment=Qt.AlignLeft)
        btn_layout.addWidget(view_cv, alignment=Qt.AlignRight)

        card_layout.addLayout(btn_layout)
        card_frame.setLayout(card_layout)

        # Set layout
        outer_layout = QVBoxLayout()
        outer_layout.addWidget(card_frame)
        self.setLayout(outer_layout)
    
    def view_more_clicked(self):
        # Show summary page with resume data
        from summary import IntegratedSummaryPage
        self.summary_page = IntegratedSummaryPage(self.get_resume_data())
        self.summary_page.show()

    def view_cv_clicked(self):
        # Open PDF viewer or show CV content
        QMessageBox.information(self, "CV Viewer", f"Opening CV for {self.name}")

    def get_resume_data(self):
        # Fetch full resume data from database using self.resume_id
        return {'name': self.name, 'skills': self.skills}



class SearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Homepage")
        self.setStyleSheet("background-color: #1A1A1A; color: white;")
        self.setMinimumSize(1280, 720)

        # === Data untuk cards ===
        self.cv_data = [
            ("Rakdaf", 4, {"React": 1, "Express": 2, "HTML": 1})
        ] * 20  # Misal ada 20 data dummy
        self.items_per_page = 6
        self.current_page = 0

        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        self.setupTopBar()
        self.setupCardArea()
        self.setupPagination()

        self.setLayout(self.main_layout)
        self.updateCards()

    def setupTopBar(self):
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignHCenter)
        top_layout.setSpacing(10)

        self.method_dropdown = QComboBox()
        self.method_dropdown.addItems(["KMP", "BM", "AC"])
        self.method_dropdown.setFixedSize(100, 36)
        self.method_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #00FFC6;
                border-radius: 10px;
                color: black;
                font-weight: bold;
                padding-left: 10px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
            }
        """)

        self.top_input = QLineEdit("3")
        self.top_input.setFixedSize(40, 36)
        self.top_input.setStyleSheet("""
            QLineEdit {
                background-color: #5A6563;
                border-radius: 10px;
                padding: 0 10px;
                color: white;
            }
        """)

        self.keyword_input = QLineEdit("React, Express, HTML")
        self.keyword_input.setFixedHeight(36)
        self.keyword_input.setFixedWidth(400)
        self.keyword_input.setStyleSheet("""
            QLineEdit {
                background-color: #5A6563;
                border-radius: 10px;
                padding: 0 10px;
                color: white;
            }
        """)

        self.search_btn = QPushButton()
        self.search_btn.setFixedSize(36, 36)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #00FF88;
                border-radius: 18px;
            }
        """)
        self.search_btn.setIcon(QIcon("assets/search_icon.png")) 
        self.search_btn.setIconSize(QSize(20, 20))

        top_layout.addWidget(self.method_dropdown)
        top_layout.addWidget(self.top_input)
        top_layout.addWidget(self.keyword_input)
        top_layout.addWidget(self.search_btn)

        self.main_layout.addLayout(top_layout)

    def setupCardArea(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")

        self.content_widget = QWidget()
        self.grid = QGridLayout()
        self.grid.setSpacing(4)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.content_widget.setLayout(self.grid)
        self.scroll.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll)

    def setupPagination(self):
        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setAlignment(Qt.AlignCenter)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #00FFC6;
                border: none;
                border-radius: 20px;
                color: black;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #00E6B8;
            }
            QPushButton:disabled {
                background-color: #5A6563;
                color: #888;
            }
        """)

        self.page_label = QLabel()
        self.page_label.setStyleSheet("color: white; font-size: 14px; margin: 0 15px;")
        self.page_label.setAlignment(Qt.AlignCenter)

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #00FFC6;
                border: none;
                border-radius: 20px;
                color: black;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #00E6B8;
            }
            QPushButton:disabled {
                background-color: #5A6563;
                color: #888;
            }
        """)

        self.prev_btn.clicked.connect(self.goToPrevPage)
        self.next_btn.clicked.connect(self.goToNextPage)

        self.pagination_layout.addWidget(self.prev_btn)
        self.pagination_layout.addWidget(self.page_label)
        self.pagination_layout.addWidget(self.next_btn)

        self.main_layout.addLayout(self.pagination_layout)

    def updateCards(self):
        # Bersihkan grid
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        current_items = self.cv_data[start:end]

        for i, (name, matches, skills) in enumerate(current_items):
            card = CVCard(name, matches, skills)
            self.grid.addWidget(card, i // 3, i % 3)

        # Update pagination
        total_pages = (len(self.cv_data) - 1) // self.items_per_page + 1
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(end < len(self.cv_data))

    def goToPage(self, page):
        if 0 <= page < (len(self.cv_data) - 1) // self.items_per_page + 1:
            self.current_page = page
            self.updateCards()

    def goToPrevPage(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.updateCards()

    def goToNextPage(self):
        if (self.current_page + 1) * self.items_per_page < len(self.cv_data):
            self.current_page += 1
            self.updateCards()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SearchApp()
    win.show()
    sys.exit(app.exec_())
