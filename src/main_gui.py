import sys
import os
import getpass
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QCursor, QIcon, QFontDatabase
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import your existing GUI classes
from gui.landing_gui import BukitDuriApp
from gui.home_gui import SearchApp, CVCard
from gui.summary_gui import SummaryPage

# Import core functionality
from src.core.extractor import extract_text_from_pdf, extract_profile_data
from src.core.matcher import kmp_search, bm_search, ac_search, fuzzy_search
from src.db.db_connector import DatabaseManager

class SearchWorker(QThread):
    results_ready = pyqtSignal(list)  # Add this signal
    error_occurred = pyqtSignal(str)  # Add this signal
    
    def __init__(self, keywords, method, top_matches, db_password=""):
        super().__init__()
        self.keywords = keywords
        self.method = method
        self.top_matches = top_matches
        self.db_password = db_password
    
    def run(self):
        try:
            # Connect tanpa password
            db = DatabaseManager(password="")
            if not db.connect():
                self.error_occurred.emit("Failed to connect to database")
                return
            
            # Perform search based on method
            if self.method == "KMP":
                results = self.search_with_kmp(db)
            elif self.method == "BM":
                results = self.search_with_bm(db)
            elif self.method == "AC":
                results = self.search_with_ac(db)
            else:
                results = []
            
            # Limit results to top matches
            results = results[:self.top_matches]
            
            self.results_ready.emit(results)
            db.disconnect()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def search_with_kmp(self, db):
        # Get all resumes from database
        all_resumes = db.get_all_resumes()
        results = []
        
        keywords = [k.strip() for k in self.keywords.split(',')]
        
        for resume in all_resumes:
            total_matches = 0
            skill_matches = {}
            
            # Search in resume text
            for keyword in keywords:
                matches = kmp_search(resume['content'], keyword)
                if matches:
                    total_matches += len(matches)
                    skill_matches[keyword] = len(matches)
            
            if total_matches > 0:
                results.append({
                    'name': resume['filename'].replace('.pdf', ''),
                    'matches': total_matches,
                    'skills': skill_matches,
                    'resume_id': resume['id']
                })
        
        return sorted(results, key=lambda x: x['matches'], reverse=True)
    
    def search_with_bm(self, db):
        # Similar to KMP but using Boyer-Moore
        all_resumes = db.get_all_resumes()
        results = []
        
        keywords = [k.strip() for k in self.keywords.split(',')]
        
        for resume in all_resumes:
            total_matches = 0
            skill_matches = {}
            
            for keyword in keywords:
                matches = bm_search(resume['content'], keyword)
                if matches:
                    total_matches += len(matches)
                    skill_matches[keyword] = len(matches)
            
            if total_matches > 0:
                results.append({
                    'name': resume['filename'].replace('.pdf', ''),
                    'matches': total_matches,
                    'skills': skill_matches,
                    'resume_id': resume['id']
                })
        
        return sorted(results, key=lambda x: x['matches'], reverse=True)
    
    def search_with_ac(self, db):
        # Using Aho-Corasick for multiple pattern matching
        all_resumes = db.get_all_resumes()
        results = []
        
        keywords = [k.strip() for k in self.keywords.split(',')]
        
        for resume in all_resumes:
            matches = ac_search(resume['content'], keywords)
            if matches:
                total_matches = len(matches)
                skill_matches = {}
                
                for _, pattern in matches:
                    if pattern in skill_matches:
                        skill_matches[pattern] += 1
                    else:
                        skill_matches[pattern] = 1
                
                results.append({
                    'name': resume['filename'].replace('.pdf', ''),
                    'matches': total_matches,
                    'skills': skill_matches,
                    'resume_id': resume['id']
                })
        
        return sorted(results, key=lambda x: x['matches'], reverse=True)

class IntegratedLandingPage(BukitDuriApp):
    """Enhanced landing page with search functionality"""
    
    def __init__(self):
        super().__init__()
        self.db_password = None
        self.search_worker = None
        self.results_window = None
        
        # Connect search button after UI is initialized
        self.connect_search_button()
    
    def connect_search_button(self):
        # Find and connect the search button
        for widget in self.findChildren(QPushButton):
            if widget.text() == "Search":
                widget.clicked.connect(self.perform_search)
                break
    
    def perform_search(self):
        line_edits = self.findChildren(QLineEdit)
        keywords = line_edits[0].text().strip() if line_edits else ""
        top_matches = int(line_edits[1].text() or "3") if len(line_edits) > 1 else 3
        
        print(f"Keywords: {keywords}")  # Debug line
        print(f"Top matches: {top_matches}")  # Debug line
        
        # Get selected method
        method = "KMP"  # Default
        if self.kmp_btn.isChecked():
            method = "KMP"
        elif self.bm_btn.isChecked():
            method = "BM"
        elif self.ac_btn.isChecked():
            method = "AC"
        else:
            # If no method is selected, default to KMP and select it
            self.kmp_btn.setChecked(True)
            method = "KMP"
        
        print(f"Method: {method}")  # Debug line
        
        if not keywords:
            QMessageBox.warning(self, "Warning", "Please enter keywords to search!")
            return
        
        # Show loading dialog
        self.loading_dialog = QProgressDialog("Searching resumes...", "Cancel", 0, 0, self)
        self.loading_dialog.setWindowModality(Qt.WindowModal)
        self.loading_dialog.show()
        
        # Start search in worker thread
        self.search_worker = SearchWorker(keywords, method, top_matches, self.db_password)
        self.search_worker.results_ready.connect(self.show_results)
        self.search_worker.error_occurred.connect(self.show_error)
        self.search_worker.finished.connect(self.search_finished)
        self.search_worker.start()
    
    def show_results(self, results):
        if hasattr(self, 'loading_dialog'):
            self.loading_dialog.close()
        
        print(f"Search completed! Found {len(results)} results")  # Debug line
        
        # Create and show results window
        self.results_window = IntegratedHomePage(results)
        self.results_window.show()
        self.close()
    
    def show_error(self, error_msg):
        if hasattr(self, 'loading_dialog'):
            self.loading_dialog.close()
        QMessageBox.critical(self, "Search Error", f"Error occurred during search:\n{error_msg}")
        print(f"Search error: {error_msg}")  # Debug line
    
    def search_finished(self):
        if hasattr(self, 'loading_dialog'):
            self.loading_dialog.close()
        print("Search worker finished")  # Debug line
    
    def perform_new_search(self):
        keywords = self.keyword_input.text().strip()
        if not keywords:
            QMessageBox.warning(self, "Warning", "Please enter keywords!")
            return
        
        method = self.method_dropdown.currentText()
        top_matches = int(self.top_input.text() or "3")
        
        # Import SearchWorker
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
        
        # Update results count
        self.results_label.setText(f"Found {len(self.cv_data)} resumes")

    def search_error(self, error_msg):
        if hasattr(self, 'loading_dialog'):
            self.loading_dialog.close()
        QMessageBox.critical(self, "Search Error", f"Error: {error_msg}")

class IntegratedHomePage(SearchApp):
    """Enhanced homepage with real search results"""
    
    def __init__(self, search_results=None):
        self.search_results = search_results or []
        super().__init__()
        
        # Convert search results to consistent format
        if self.search_results:
            self.cv_data = []
            for result in self.search_results:
                self.cv_data.append({
                    'name': result['name'],
                    'matches': result['matches'], 
                    'skills': result['skills'],
                    'resume_id': result['resume_id']
                })
        
        self.updateCards()
    
    def setupTopBar(self):
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        
        # Circular back button
        back_btn = QPushButton("‹")
        back_btn.setFixedSize(40, 40)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #00FFC6;
                border-radius: 20px;
                color: black;
                font-weight: bold;
                font-size: 24px;
            }
            QPushButton:hover {
                background-color: #00E6B8;
            }
        """)
        back_btn.clicked.connect(self.go_back_to_search)
        
        # Search components
        method_label = QLabel("Method:")
        method_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.method_dropdown = QComboBox()
        self.method_dropdown.addItems(["KMP", "BM", "AC"])
        self.method_dropdown.setFixedSize(80, 36)
        self.method_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #6D797A;
                color: white;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        top_label = QLabel("Top:")
        top_label.setStyleSheet("color: white; font-size: 14px;")
        
        self.top_input = QLineEdit("3")
        self.top_input.setFixedSize(50, 36)
        self.top_input.setStyleSheet("""
            QLineEdit {
                background-color: #6D797A;
                color: white;
                border-radius: 4px;
                padding: 4px;
                text-align: center;
            }
        """)
        
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Enter keywords...")
        self.keyword_input.setFixedHeight(36)
        self.keyword_input.setFixedWidth(250)
        self.keyword_input.setStyleSheet("""
            QLineEdit {
                background-color: #6D797A;
                color: white;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedSize(80, 36)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #0AD87E;
                color: #06312D;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #11f59b;
            }
        """)
        self.search_btn.clicked.connect(self.perform_new_search)
        
        # Layout
        top_layout.addWidget(back_btn)
        top_layout.addWidget(method_label)
        top_layout.addWidget(self.method_dropdown)
        top_layout.addWidget(top_label)
        top_layout.addWidget(self.top_input)
        top_layout.addWidget(self.keyword_input)
        top_layout.addWidget(self.search_btn)
        top_layout.addStretch()
        
        # Results count on the right
        self.results_label = QLabel(f"Found {len(self.cv_data)} resumes")
        self.results_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        top_layout.addWidget(self.results_label)
        
        self.main_layout.addLayout(top_layout)
    
    def go_back_to_search(self):
        from gui.main_gui import IntegratedLandingPage
        self.landing_page = IntegratedLandingPage()
        self.landing_page.show()
        self.close()

class IntegratedSummaryPage(SummaryPage):
    """Enhanced summary page with real resume data"""
    
    def __init__(self, resume_data=None):
        self.resume_data = resume_data
        super().__init__()
        
        if resume_data:
            self.populate_with_real_data()
    
    def populate_with_real_data(self):
        # Update name
        name_label = self.findChild(QLabel, "name")
        if name_label and self.resume_data:
            name_label.setText(self.resume_data.get('name', 'Unknown'))
        
        # Update skills with real data
        if 'skills' in self.resume_data:
            # Update the skills list
            pass  # Implementation depends on your data structure

class MainApplication(QApplication):
    """Main application controller"""
    
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.setApplicationName("Bukit Duri CV Analyzer")
        
        # Load fonts
        self.load_fonts()
        
        # Show landing page
        self.landing_page = IntegratedLandingPage()
        self.landing_page.show()
    
    def load_fonts(self):
        try:
            font_path = os.path.join(os.path.dirname(__file__), "font/Inter_24pt-Regular.ttf")
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    self.setFont(QFont(families[0] if families else "Arial", 10))
        except Exception as e:
            print(f"Font loading error: {e}")
            self.setFont(QFont("Arial", 10))

def main():
    app = MainApplication(sys.argv)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()