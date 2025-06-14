import sys
import os
import getpass
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QCursor, QIcon, QFontDatabase
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer

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
    results_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, keywords, method, top_matches, db_password=""):
        super().__init__()
        self.keywords = keywords
        self.method = method
        self.top_matches = top_matches
        self.db_password = db_password
    
    def run(self):
        try:
            # Connect to database with empty password
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
            
            # Search in resume content (extracted_text)
            search_text = resume.get('content', '') or resume.get('extracted_text', '')
            if not search_text:
                continue
                
            for keyword in keywords:
                from src.core.matcher import kmp_search
                matches = kmp_search(search_text, keyword)
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
            
            search_text = resume.get('content', '') or resume.get('extracted_text', '')
            if not search_text:
                continue
            
            for keyword in keywords:
                from src.core.matcher import bm_search
                matches = bm_search(search_text, keyword)
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
            search_text = resume.get('content', '') or resume.get('extracted_text', '')
            if not search_text:
                continue
                
            from src.core.matcher import ac_search
            matches = ac_search(search_text, keywords)
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
        
        # Prepare search parameters to pass to home page
        line_edits = self.findChildren(QLineEdit)
        keywords = line_edits[0].text().strip() if line_edits else ""
        top_matches = int(line_edits[1].text() or "3") if len(line_edits) > 1 else 3
        
        # Get selected method
        method = "KMP"  # Default
        if self.kmp_btn.isChecked():
            method = "KMP"
        elif self.bm_btn.isChecked():
            method = "BM"
        elif self.ac_btn.isChecked():
            method = "AC"
        
        search_params = {
            'keywords': keywords,
            'method': method,
            'top_matches': top_matches
        }
        
        # Create and show results window with search parameters
        self.results_window = IntegratedHomePage(results, search_params)
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
    def __init__(self, search_results=None, search_params=None):
        self.search_results = search_results or []
        self.search_params = search_params or {}  # Store search parameters
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
        
        # Populate search fields with previous values
        self.populate_search_fields()
        self.updateCards()
    
    def populate_search_fields(self):
        """Populate search fields with values from landing page"""
        if hasattr(self, 'keyword_input') and self.search_params.get('keywords'):
            self.keyword_input.setText(self.search_params['keywords'])
        
        if hasattr(self, 'method_dropdown') and self.search_params.get('method'):
            method = self.search_params['method']
            index = self.method_dropdown.findText(method)
            if index >= 0:
                self.method_dropdown.setCurrentIndex(index)
        
        if hasattr(self, 'top_input') and self.search_params.get('top_matches'):
            self.top_input.setText(str(self.search_params['top_matches']))
    
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
        
        # Populate search fields AFTER UI elements are created
        self.populate_search_fields()
    
    def go_back_to_search(self):
        """Go back to landing page with current search values"""
        try:
            # Create landing page
            self.landing_page = IntegratedLandingPage()
            
            # Populate landing page with current search values
            if hasattr(self, 'keyword_input') and hasattr(self, 'method_dropdown') and hasattr(self, 'top_input'):
                # Wait for landing page to be fully initialized
                QTimer.singleShot(100, lambda: self.populate_landing_page())
            
            self.landing_page.show()
            self.close()
        except Exception as e:
            print(f"Error going back to search: {e}")
            self.close()

    def populate_landing_page(self):
        """Populate landing page with current search values"""
        try:
            # Get current values
            current_keywords = self.keyword_input.text()
            current_method = self.method_dropdown.currentText()
            current_top = self.top_input.text()
            
            # Find and populate landing page fields
            line_edits = self.landing_page.findChildren(QLineEdit)
            if len(line_edits) >= 2:
                line_edits[0].setText(current_keywords)  # Keywords field
                line_edits[1].setText(current_top)        # Top matches field
            
            # Set method button
            if current_method == "KMP":
                self.landing_page.kmp_btn.setChecked(True)
            elif current_method == "BM":
                self.landing_page.bm_btn.setChecked(True)
            elif current_method == "AC":
                self.landing_page.ac_btn.setChecked(True)
                
        except Exception as e:
            print(f"Error populating landing page: {e}")

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
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.setApplicationName("Bukit Duri CV Analyzer")
        self.load_fonts()
        self.check_database_setup()
    
    def load_fonts(self):
        """Load custom fonts for the application"""
        try:
            # Try to load Inter font
            font_path = os.path.join(os.path.dirname(__file__), "font", "Inter_24pt-Regular.ttf")
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        self.setFont(QFont(families[0], 10))
                        print(f"Loaded custom font: {families[0]}")
                    else:
                        self.setFont(QFont("Arial", 10))
                else:
                    print("Failed to load custom font, using Arial")
                    self.setFont(QFont("Arial", 10))
            else:
                print("Font file not found, using Arial")
                self.setFont(QFont("Arial", 10))
        except Exception as e:
            print(f"Error loading fonts: {e}")
            self.setFont(QFont("Arial", 10))
    
    def check_database_setup(self):
        """Always run fresh database setup"""
        try:
            # Always reset database first
            self.reset_database()
            # Then show setup GUI
            self.show_setup_gui()
        except Exception as e:
            print(f"Database reset error: {e}")
            self.show_setup_gui()

    def reset_database(self):
        """Reset database before setup"""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from src.db.db_connector import DatabaseManager
            
            # Connect without specifying database
            import mysql.connector
            temp_conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password=''
            )
            cursor = temp_conn.cursor()
            
            # Drop existing database
            cursor.execute("DROP DATABASE IF EXISTS Tubes3Stima")
            print("Dropped existing database")
            
            temp_conn.close()
            
        except Exception as e:
            print(f"Database reset error: {e}")
    
    def show_setup_gui(self):
        try:
            # Fix import path
            sys.path.append(os.path.join(os.path.dirname(__file__), 'gui'))
            from database_setup_gui import DatabaseSetupGUI
            
            self.setup_gui = DatabaseSetupGUI()
            self.setup_gui.setup_completed.connect(self.on_setup_completed)
            self.setup_gui.show()
            self.setup_gui.start_setup()
        except ImportError as e:
            print(f"Setup GUI import error: {e}")
            # If setup GUI doesn't exist, try direct setup
            print("Setup GUI not found, running direct setup...")
            self.run_direct_setup()
        except Exception as e:
            print(f"Setup GUI error: {e}")
            self.run_direct_setup()
    
    def run_direct_setup(self):
        """Run setup directly without GUI"""
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from setup_database import setup_database
            
            print("Running database setup...")
            success = setup_database()
            
            if success:
                print("Database setup completed!")
                self.show_main_app()
            else:
                print("Database setup failed!")
                self.quit()
        except Exception as e:
            print(f"Direct setup error: {e}")
            self.quit()
    
    def on_setup_completed(self, success):
        """Handle setup completion"""
        if hasattr(self, 'setup_gui'):
            self.setup_gui.close()
        
        if success:
            self.show_main_app()
        else:
            # Show error and exit
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Setup Failed")
            msg.setText("Database setup failed. Please check your MySQL installation.")
            msg.exec_()
            self.quit()
    
    def show_main_app(self):
        """Show main application"""
        self.landing_page = IntegratedLandingPage()
        self.landing_page.show()

def main():
    
    # Add src to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, 'src')
    sys.path.insert(0, src_dir)
    sys.path.insert(0, current_dir)
    
    try:
        app = MainApplication(sys.argv)
        return app.exec_()
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())