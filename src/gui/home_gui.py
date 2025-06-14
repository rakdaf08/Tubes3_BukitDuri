import sys
import subprocess
import platform
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QCursor, QIcon
from PyQt5.QtCore import Qt, QSize

# Add path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import GUI components
from gui.summary_gui import SummaryPage
from src.db.db_connector import DatabaseManager

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
        name_label.setFont(QFont("Arial", 16, QFont.Bold)) 
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
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.append(current_dir)
            
            db = DatabaseManager(password="123")
            if db.connect():
                resume = db.get_resume_by_id(self.resume_id)
                if resume:
                    display_name = ""
                    if resume.get('first_name') and resume.get('last_name'):
                        display_name = f"{resume['first_name']} {resume['last_name']}"
                    elif resume.get('first_name'):
                        display_name = resume['first_name']
                    elif resume.get('last_name'):
                        display_name = resume['last_name']
                    else:
                        display_name = resume['filename'].replace('.pdf', '')
                    
                    resume_data = {
                        'name': display_name,
                        'first_name': resume.get('first_name'),
                        'last_name': resume.get('last_name'),
                        'date_of_birth': resume.get('date_of_birth'),
                        'address': resume.get('address'),
                        'phone_number': resume.get('phone_number'),
                        'application_role': resume.get('application_role'),
                        'skills': resume['skills'] if resume['skills'] else 'No skills data available',
                        'experience': resume['experience'] if resume['experience'] else '',
                        'education': resume['education'] if resume['education'] else '',
                        'gpa': resume['gpa'] if resume['gpa'] else None,
                        'certifications': resume['certifications'] if resume['certifications'] else '',
                        'category': resume.get('category', 'Unknown'),
                        'resume_id': self.resume_id,
                        'file_path': resume['file_path'],
                        'extracted_text': resume.get('extracted_text', '') or resume.get('content', ''),
                        'created_at': resume.get('created_at', 'Unknown'),
                        'filename': resume.get('filename')
                    }
                    
                    print(f"DEBUG - Resume data being sent to summary:")
                    print(f"Name: {resume_data['name']}")
                    print(f"First Name: {resume_data['first_name']}")
                    print(f"Last Name: {resume_data['last_name']}")
                    print(f"Date of Birth: {resume_data['date_of_birth']}")
                    print(f"Address: {resume_data['address']}")
                    print(f"Phone: {resume_data['phone_number']}")
                    
                    self.summary_page = SummaryPage(resume_data)
                    self.summary_page.show()
                else:
                    QMessageBox.information(self, "Error", "Resume data not found in database")
                db.disconnect()
            else:
                QMessageBox.critical(self, "Database Error", "Could not connect to database")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open summary: {str(e)}")
            print(f"DEBUG - Error in view_more_clicked: {e}")

    def view_cv_clicked(self):
        try:
            # Get resume data from database
            from src.db.db_connector import DatabaseManager
            db = DatabaseManager(password="123")
            if db.connect():
                resume = db.get_resume_by_id(self.resume_id)
                if resume and resume['file_path']:
                    file_path = resume['file_path']
                    
                    # Check if file exists
                    if os.path.exists(file_path):
                        # Open PDF with default system viewer
                        if platform.system() == 'Darwin':  # macOS
                            subprocess.run(['open', file_path])
                        elif platform.system() == 'Windows':
                            os.startfile(file_path)
                        else:  # Linux
                            subprocess.run(['xdg-open', file_path])
                    else:
                        QMessageBox.warning(self, "File Not Found", 
                                        f"PDF file not found:\n{file_path}")
                else:
                    QMessageBox.information(self, "No File", "No PDF file associated with this resume")
                db.disconnect()
            else:
                QMessageBox.critical(self, "Database Error", "Could not connect to database")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open PDF:\n{str(e)}")

    def get_resume_data(self):
        # Return resume data structure
        return {
            'name': getattr(self, 'name', 'Unknown'),
            'skills': getattr(self, 'skills', {}),
            'resume_id': self.resume_id
        }



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
        # Simplified version for base SearchApp
        top_layout = QHBoxLayout()
        
        title = QLabel("CV Search Results")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        top_layout.addWidget(title)
        top_layout.addStretch()
        
        self.main_layout.addLayout(top_layout)

    def perform_new_search(self):
        keywords = self.keyword_input.text().strip()
        if not keywords:
            QMessageBox.warning(self, "Warning", "Please enter keywords!")
            return
        
        method = self.method_dropdown.currentText()
        top_matches = int(self.top_input.text() or "3")
        
        # Fix import - import SearchWorker from main_gui
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            sys.path.append(parent_dir)
            
            from main_gui import SearchWorker
            
            # Show loading
            self.loading_dialog = QProgressDialog("Searching...", "Cancel", 0, 0, self)
            self.loading_dialog.setWindowModality(Qt.WindowModal)
            self.loading_dialog.show()
            
            # Create search worker
            self.search_worker = SearchWorker(keywords, method, top_matches, "")
            self.search_worker.results_ready.connect(self.update_search_results)
            self.search_worker.error_occurred.connect(self.search_error)
            self.search_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Could not import SearchWorker: {str(e)}")
            print(f"SearchWorker import error: {e}")

    def update_search_results(self, results):
        if hasattr(self, 'loading_dialog'):
            self.loading_dialog.close()
        
        # Update data
        self.search_results = results
        self.cv_data = []
        for result in results:
            self.cv_data.append({
                'name': result['name'],
                'matches': result['matches'],
                'skills': result['skills'],
                'resume_id': result['resume_id']
            })
        
        self.current_page = 0
        self.updateCards()
        
        # Update results count if results_label exists
        if hasattr(self, 'results_label'):
            self.results_label.setText(f"Found {len(self.cv_data)} resumes")

    def search_error(self, error_msg):
        if hasattr(self, 'loading_dialog'):
            self.loading_dialog.close()
        QMessageBox.critical(self, "Search Error", f"Error: {error_msg}")

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
        # Clear existing widgets
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        current_items = self.cv_data[start:end]

        for i, item_data in enumerate(current_items):
            # Handle different data formats
            if isinstance(item_data, dict):
                # Format from search results
                name = item_data.get('name', 'Unknown')
                matches = item_data.get('matches', 0)
                skills = item_data.get('skills', {})
                resume_id = item_data.get('resume_id')
            elif isinstance(item_data, tuple) and len(item_data) >= 3:
                # Tuple format (name, matches, skills, resume_id)
                name = item_data[0]
                matches = item_data[1]
                skills = item_data[2]
                resume_id = item_data[3] if len(item_data) > 3 else None
            else:
                # Fallback
                name = "Unknown"
                matches = 0
                skills = {}
                resume_id = None
            
            card = CVCard(name, matches, skills, resume_id)
            self.grid.addWidget(card, i // 3, i % 3)

        # Update pagination
        total_pages = (len(self.cv_data) - 1) // self.items_per_page + 1 if self.cv_data else 1
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
