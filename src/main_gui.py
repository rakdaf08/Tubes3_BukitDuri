import sys
import os
import getpass
import time
from fuzzywuzzy import fuzz
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QCursor, QIcon, QFontDatabase
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from config import DATABASE_CONFIG, SEARCH_SETTINGS

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
    timing_info = pyqtSignal(dict)  # New signal for timing information
    
    def __init__(self, keywords, method, top_matches, db_password=""):
        super().__init__()
        self.keywords = keywords
        self.method = method
        self.top_matches = top_matches
    
    def run(self):
        try:
            # Connect to database
            db = DatabaseManager()
            if not db.connect():
                self.error_occurred.emit("Failed to connect to database")
                return
            
            # Get all resumes
            all_resumes = db.get_all_resumes()
            
            # Perform exact matching first
            exact_start_time = time.time()
            exact_results, found_keywords = self.perform_exact_search(all_resumes)
            exact_time = (time.time() - exact_start_time) * 1000  # Convert to ms
            
            # Get keywords that weren't found in exact matching
            keywords_list = [k.strip() for k in self.keywords.split(',')]
            missing_keywords = [kw for kw in keywords_list if kw not in found_keywords]
            
            # Perform fuzzy matching for missing keywords
            fuzzy_results = []
            fuzzy_time = 0
            
            if missing_keywords:
                fuzzy_start_time = time.time()
                fuzzy_results = self.perform_fuzzy_search(all_resumes, missing_keywords)
                fuzzy_time = (time.time() - fuzzy_start_time) * 1000
            
            # Combine results
            combined_results = self.combine_results(exact_results, fuzzy_results)
            
            # Sort by total matches and limit
            final_results = sorted(combined_results, key=lambda x: x['matches'], reverse=True)[:self.top_matches]
            
            # Emit timing information
            timing_data = {
                'exact_time': exact_time,
                'fuzzy_time': fuzzy_time,
                'exact_count': len(exact_results),
                'fuzzy_count': len(fuzzy_results),
                'total_scanned': len(all_resumes),
                'missing_keywords': missing_keywords
            }
            
            self.timing_info.emit(timing_data)
            self.results_ready.emit(final_results)
            db.disconnect()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def perform_exact_search(self, all_resumes):
        """Perform exact matching using selected algorithm"""
        results = []
        found_keywords = set()
        keywords = [k.strip() for k in self.keywords.split(',')]
        
        for resume in all_resumes:
            search_text = resume.get('content', '') or resume.get('extracted_text', '')
            if not search_text:
                continue
            
            total_matches = 0
            skill_matches = {}
            
            for keyword in keywords:
                # Use selected algorithm for exact matching
                if self.method == "KMP":
                    from src.core.matcher import kmp_search
                    matches = kmp_search(search_text, keyword)
                elif self.method == "BM":
                    from src.core.matcher import bm_search
                    matches = bm_search(search_text, keyword)
                elif self.method == "AC":
                    from src.core.matcher import ac_search
                    matches = ac_search(search_text, [keyword])
                    matches = [pos for pos, _ in matches]
                else:
                    matches = []
                
                if matches:
                    total_matches += len(matches)
                    skill_matches[keyword] = len(matches)
                    found_keywords.add(keyword)
            
            if total_matches > 0:
                display_name = ""
                first_name = resume.get('first_name')
                last_name = resume.get('last_name')
                
                if first_name and last_name:
                    display_name = f"{first_name} {last_name}"
                elif first_name:
                    display_name = first_name
                elif last_name:
                    display_name = last_name
                else:
                    filename = resume['filename'].replace('.pdf', '')
                    if filename.isdigit():
                        display_name = f"Candidate {filename}"
                    else:
                        display_name = filename
                
                results.append({
                    'name': display_name,
                    'matches': total_matches,
                    'skills': skill_matches,
                    'resume_id': resume['id'],
                    'match_type': 'exact',
                    'profile_data': {
                        'first_name': resume.get('first_name'),
                        'last_name': resume.get('last_name'),
                        'application_role': resume.get('application_role'),
                        'date_of_birth': resume.get('date_of_birth'),
                        'address': resume.get('address'),
                        'phone_number': resume.get('phone_number'),
                        'filename': resume.get('filename')
                    }
                })
        
        return results, found_keywords

    def perform_fuzzy_search(self, all_resumes, missing_keywords):
        """Perform fuzzy matching using Levenshtein Distance"""
        results = []
        
        for resume in all_resumes:
            search_text = resume.get('content', '') or resume.get('extracted_text', '')
            if not search_text:
                continue
            
            total_fuzzy_matches = 0
            fuzzy_skill_matches = {}
            
            for keyword in missing_keywords:
                from src.core.matcher import fuzzy_search
                fuzzy_matches = fuzzy_search(search_text, keyword, threshold=60)
                
                if fuzzy_matches:
                    high_sim_matches = [m for m in fuzzy_matches if m[2] >= 70]
                    if high_sim_matches:
                        total_fuzzy_matches += len(high_sim_matches)
                        fuzzy_skill_matches[f"{keyword} (fuzzy)"] = len(high_sim_matches)
            
            if total_fuzzy_matches > 0:
                display_name = ""
                first_name = resume.get('first_name')
                last_name = resume.get('last_name')
                
                if first_name and last_name:
                    display_name = f"{first_name} {last_name}"
                elif first_name:
                    display_name = first_name
                elif last_name:
                    display_name = last_name
                else:
                    filename = resume['filename'].replace('.pdf', '')
                    if filename.isdigit():
                        display_name = f"Candidate {filename}"
                    else:
                        display_name = filename
                
                results.append({
                    'name': display_name,
                    'matches': total_fuzzy_matches,
                    'skills': fuzzy_skill_matches,
                    'resume_id': resume['id'],
                    'match_type': 'fuzzy',
                    'profile_data': {
                        'first_name': resume.get('first_name'),
                        'last_name': resume.get('last_name'),
                        'application_role': resume.get('application_role'),
                        'date_of_birth': resume.get('date_of_birth'),
                        'address': resume.get('address'),
                        'phone_number': resume.get('phone_number'),
                        'filename': resume.get('filename')
                    }
                })
        
        return results
            
    def combine_results(self, exact_results, fuzzy_results):
        """Combine exact and fuzzy results, avoiding duplicates"""
        # Create dict to track resumes by ID
        combined = {}
        
        # Add exact results first (higher priority)
        for result in exact_results:
            resume_id = result['resume_id']
            combined[resume_id] = result
        
        # Add fuzzy results for resumes not in exact results
        for result in fuzzy_results:
            resume_id = result['resume_id']
            if resume_id in combined:
                # Merge fuzzy skills with exact skills
                combined[resume_id]['skills'].update(result['skills'])
                combined[resume_id]['matches'] += result['matches']
                combined[resume_id]['match_type'] = 'both'
            else:
                combined[resume_id] = result
        
        return list(combined.values())
    
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
        
        print(f"Search completed! Found {len(results)} results")
        
        # Get search parameters
        line_edits = self.findChildren(QLineEdit)
        keywords = line_edits[0].text().strip() if line_edits else ""
        top_matches = int(line_edits[1].text() or "3") if len(line_edits) > 1 else 3
        
        method = "KMP"
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
        
        # Create results window with search parameters
        self.results_window = IntegratedHomePage(results, search_params)
        
        # Connect timing signal for landing page search too
        if hasattr(self, 'search_worker'):
            self.search_worker.timing_info.connect(self.results_window.update_timing_display)
        
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
        
        try:
            # Show loading
            self.loading_dialog = QProgressDialog("Searching...", "Cancel", 0, 0, self)
            self.loading_dialog.setWindowModality(Qt.WindowModal)
            self.loading_dialog.show()
            
            # Create search worker
            self.search_worker = SearchWorker(keywords, method, top_matches, "")
            self.search_worker.results_ready.connect(self.update_search_results)
            self.search_worker.timing_info.connect(self.update_timing_display)  # New connection
            self.search_worker.error_occurred.connect(self.search_error)
            self.search_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"Could not start search: {str(e)}")

    def update_timing_display(self, timing_data):
        """Update timing information display"""
        exact_time = timing_data.get('exact_time', 0)
        fuzzy_time = timing_data.get('fuzzy_time', 0)
        exact_count = timing_data.get('exact_count', 0)
        fuzzy_count = timing_data.get('fuzzy_count', 0)
        total_scanned = timing_data.get('total_scanned', 0)
        missing_keywords = timing_data.get('missing_keywords', [])
        
        # Update exact match timing
        exact_text = f"Exact Match: {total_scanned} CVs scanned in {exact_time:.0f}ms"
        if exact_count > 0:
            exact_text += f" • {exact_count} results found"
        self.exact_timing_label.setText(exact_text)
        
        # Update fuzzy match timing
        if fuzzy_time > 0:
            fuzzy_text = f"Fuzzy Match: {total_scanned} CVs scanned in {fuzzy_time:.0f}ms"
            if fuzzy_count > 0:
                fuzzy_text += f" • {fuzzy_count} additional results"
            if missing_keywords:
                fuzzy_text += f" • Keywords: {', '.join(missing_keywords)}"
            self.fuzzy_timing_label.setText(fuzzy_text)
            self.fuzzy_timing_label.show()
        else:
            self.fuzzy_timing_label.setText("Fuzzy Match: Not needed (all keywords found)")
            self.fuzzy_timing_label.show()

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
        self.search_params = search_params or {}
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

    def update_timing_display(self, timing_data):
        """Update timing information display"""
        exact_time = timing_data.get('exact_time', 0)
        fuzzy_time = timing_data.get('fuzzy_time', 0)
        exact_count = timing_data.get('exact_count', 0)
        fuzzy_count = timing_data.get('fuzzy_count', 0)
        total_scanned = timing_data.get('total_scanned', 0)
        missing_keywords = timing_data.get('missing_keywords', [])
        
        # Update exact match timing (only if timing labels exist)
        if hasattr(self, 'exact_timing_label'):
            exact_text = f"Exact Match: {total_scanned} CVs scanned in {exact_time:.0f}ms"
            if exact_count > 0:
                exact_text += f" • {exact_count} results found"
            self.exact_timing_label.setText(exact_text)
        
        # Update fuzzy match timing
        if hasattr(self, 'fuzzy_timing_label'):
            if fuzzy_time > 0:
                fuzzy_text = f"Fuzzy Match: {total_scanned} CVs scanned in {fuzzy_time:.0f}ms"
                if fuzzy_count > 0:
                    fuzzy_text += f" • {fuzzy_count} additional results"
                if missing_keywords:
                    fuzzy_text += f" • Keywords: {', '.join(missing_keywords)}"
                self.fuzzy_timing_label.setText(fuzzy_text)
                self.fuzzy_timing_label.show()
            else:
                self.fuzzy_timing_label.setText("Fuzzy Match: Not needed (all keywords found)")
                self.fuzzy_timing_label.show()

    def perform_new_search(self):
        keywords = self.keyword_input.text().strip()
        if not keywords:
            QMessageBox.warning(self, "Warning", "Please enter keywords!")
            return
        
        method = self.method_dropdown.currentText()
        top_matches = int(self.top_input.text() or "3")
        
        try:
            # Show loading
            self.loading_dialog = QProgressDialog("Searching...", "Cancel", 0, 0, self)
            self.loading_dialog.setWindowModality(Qt.WindowModal)
            self.loading_dialog.show()
            
            # Create search worker
            self.search_worker = SearchWorker(keywords, method, top_matches, "")
            self.search_worker.results_ready.connect(self.update_search_results)
            self.search_worker.timing_info.connect(self.update_timing_display)  # This will now work
            self.search_worker.error_occurred.connect(self.search_error)
            self.search_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"Could not start search: {str(e)}")

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
        if hasattr(self, 'results_label'):
            self.results_label.setText(f"Found {len(self.cv_data)} resumes")

    def search_error(self, error_msg):
        if hasattr(self, 'loading_dialog'):
            self.loading_dialog.close()
        QMessageBox.critical(self, "Search Error", f"Error: {error_msg}")
    
    def setupTopBar(self):
        top_layout = QVBoxLayout()
        
        # First row - navigation and search
        nav_search_layout = QHBoxLayout()
        nav_search_layout.setSpacing(15)
        
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
        
        # Search components (same as before)
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
        
        # Layout first row
        nav_search_layout.addWidget(back_btn)
        nav_search_layout.addWidget(method_label)
        nav_search_layout.addWidget(self.method_dropdown)
        nav_search_layout.addWidget(top_label)
        nav_search_layout.addWidget(self.top_input)
        nav_search_layout.addWidget(self.keyword_input)
        nav_search_layout.addWidget(self.search_btn)
        nav_search_layout.addStretch()
        
        # Results count
        self.results_label = QLabel(f"Found {len(self.cv_data)} resumes")
        self.results_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        nav_search_layout.addWidget(self.results_label)
        
        # Second row - timing information
        self.timing_layout = QHBoxLayout()
        self.timing_layout.setSpacing(20)
        
        # Exact match timing
        self.exact_timing_label = QLabel("")
        self.exact_timing_label.setStyleSheet("""
            color: #00FFC6; 
            font-size: 12px; 
            background-color: #1A3A35;
            border-radius: 8px;
            padding: 5px 10px;
        """)
        
        # Fuzzy match timing
        self.fuzzy_timing_label = QLabel("")
        self.fuzzy_timing_label.setStyleSheet("""
            color: #FFB366; 
            font-size: 12px; 
            background-color: #3A2A1A;
            border-radius: 8px;
            padding: 5px 10px;
        """)
        
        self.timing_layout.addWidget(self.exact_timing_label)
        self.timing_layout.addWidget(self.fuzzy_timing_label)
        self.timing_layout.addStretch()
        
        # Add both rows to main layout
        top_layout.addLayout(nav_search_layout)
        top_layout.addLayout(self.timing_layout)
        
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
            host=DATABASE_CONFIG['host'],  
            user=DATABASE_CONFIG['user'],     
            password=DATABASE_CONFIG['password'] 
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