import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QMovie, QPalette, QColor

# Fix import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # Go up from gui to src
root_dir = os.path.dirname(parent_dir)     # Go up from src to root

sys.path.append(parent_dir)  # Add src directory
sys.path.append(root_dir)    # Add root directory

# Import SVG support
try:
    from PyQt5.QtSvg import QSvgWidget
except ImportError:
    print("QSvgWidget not available, using text fallback")

# Now import with correct paths
from db.db_connector import DatabaseManager
from core.extractor import extract_text_from_pdf, extract_profile_data

class DatabaseSetupWorker(QThread):
    progress_update = pyqtSignal(str)
    progress_percentage = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            self.progress_update.emit("Initializing database setup...")
            self.progress_percentage.emit(5)
            
            # Call the silent setup function directly
            success = setup_database_silent(self.progress_update.emit, self.progress_percentage.emit)
            
            self.progress_update.emit("Setup completed!" if success else "Setup failed!")
            self.progress_percentage.emit(100)
            self.finished_signal.emit(success)
            
        except Exception as e:
            self.progress_update.emit(f"Error: {str(e)}")
            self.progress_percentage.emit(0)
            self.finished_signal.emit(False)

def setup_database_silent(progress_callback=None, percentage_callback=None):
    """Silent setup database with progress callbacks"""
    try:
        # Always drop existing database first
        if progress_callback:
            progress_callback("Dropping existing database...")
        if percentage_callback:
            percentage_callback(10)
        
        import mysql.connector
        try:
            temp_conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password=''
            )
            cursor = temp_conn.cursor()
            cursor.execute("DROP DATABASE IF EXISTS Tubes3Stima")
            temp_conn.close()
            print("Dropped existing database")
        except Exception as e:
            print(f"Database drop error (normal if not exists): {e}")
        
        if progress_callback:
            progress_callback("Creating fresh database...")
        if percentage_callback:
            percentage_callback(15)
        
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'Tubes3Stima',
        }
        
        db = DatabaseManager(**db_config)
        
        if progress_callback:
            progress_callback("Creating database and tables...")
        if percentage_callback:
            percentage_callback(20)
        
        if not db.create_database_and_tables():
            if progress_callback:
                progress_callback("Failed to create database/tables")
            return False
        
        if progress_callback:
            progress_callback("Connecting to database...")
        if percentage_callback:
            percentage_callback(25)
        
        if not db.connect():
            if progress_callback:
                progress_callback("Failed to connect to database")
            return False
        
        if progress_callback:
            progress_callback("Loading resume data from PDF files...")
        if percentage_callback:
            percentage_callback(30)
        
        # Load data silently
        load_resume_data_silent(db, progress_callback, percentage_callback)
        
        if progress_callback:
            progress_callback("Finalizing setup...")
        if percentage_callback:
            percentage_callback(95)
        
        db.disconnect()
        return True
        
    except Exception as e:
        if progress_callback:
            progress_callback(f"Setup error: {str(e)}")
        print(f"Setup database error: {e}")
        return False

def load_resume_data_silent(db: DatabaseManager, progress_callback=None, percentage_callback=None):
    """Load resume data silently without user input - always process all files"""
    # Use root directory for finding data folder
    pdf_dir = os.path.join(root_dir, "data", "pdf")
    
    if progress_callback:
        progress_callback(f"Looking for PDF files in: {pdf_dir}")
    
    if not os.path.exists(pdf_dir):
        if progress_callback:
            progress_callback("PDF directory not found - skipping data load...")
        print(f"PDF directory not found: {pdf_dir}")
        return
    
    # Count total files
    total_files = 0
    categories = []
    for category in os.listdir(pdf_dir):
        category_path = os.path.join(pdf_dir, category)
        if os.path.isdir(category_path):
            pdf_files = [f for f in os.listdir(category_path) if f.endswith('.pdf')]
            total_files += len(pdf_files)
            categories.append((category, pdf_files))
    
    if total_files == 0:
        if progress_callback:
            progress_callback("No PDF files found")
        print("No PDF files found")
        return
    
    # Process ALL files automatically
    processed = 0
    
    if progress_callback:
        progress_callback(f"Processing all {total_files} PDF files...")
    
    print(f"Total PDF files found: {total_files}")
    
    for category, pdf_files in categories:
        if progress_callback:
            progress_callback(f"Processing {category} category...")
        
        print(f"Processing category: {category}")
        
        for filename in pdf_files:
            pdf_path = os.path.join(pdf_dir, category, filename)
            
            try:
                # Extract and process
                extracted_text = extract_text_from_pdf(pdf_path)
                if extracted_text:
                    profile = extract_profile_data(extracted_text)
                    
                    # Insert to database
                    skills = ", ".join(profile.get('skills', []))[:2000]
                    experience_list = [f"{exp.get('title', '')} ({exp.get('start', '')} - {exp.get('end', '')})" 
                                     for exp in profile.get('experience', [])]
                    experience = " | ".join(experience_list)[:2000]
                    
                    education_list = [f"{edu.get('degree', '')} in {edu.get('field', '')}" 
                                    for edu in profile.get('education', [])]
                    education = " | ".join(education_list)[:1000]
                    
                    gpa = float(profile['gpa'][0]) if profile.get('gpa') else None
                    certifications = ", ".join(profile.get('certifications', []))[:1000]
                    
                    resume_id = db.insert_resume(
                        filename=filename,
                        category=category,
                        file_path=pdf_path,
                        extracted_text=extracted_text[:100000],
                        skills=skills,
                        experience=experience,
                        education=education,
                        gpa=gpa,
                        certifications=certifications
                    )
                    
                    if resume_id and resume_id > 0:
                        print(f"Inserted {filename} with ID: {resume_id}")
                    else:
                        print(f"Failed to insert {filename}")
                
                processed += 1
                
                # Update progress
                if percentage_callback:
                    progress_percent = 30 + int((processed / total_files) * 60)
                    percentage_callback(progress_percent)
                
                if progress_callback:
                    progress_callback(f"Processed {processed}/{total_files} files...")
                
                # Print progress every 10 files
                if processed % 10 == 0:
                    print(f"Progress: {processed}/{total_files} files processed")
                    
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Error processing {filename}: {str(e)}")
                print(f"Error processing {filename}: {e}")
                continue
    
    print(f"Final: Successfully processed {processed} out of {total_files} files")

# Rest of the GUI code remains the same...
class DatabaseSetupGUI(QWidget):
    setup_completed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bukit Duri - Database Setup")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet("background-color: #051010; color: #00E4AA;")
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Logo section (sama seperti landing_gui)
        logo_layout = QHBoxLayout()
        try:
            # Try to load SVG logo
            from PyQt5.QtSvg import QSvgWidget
            logo_path = os.path.join(root_dir, "src", "gui", "logo_bukdur.svg")
            if os.path.exists(logo_path):
                logo = QSvgWidget(logo_path)
                logo.setFixedSize(250, 130)  # Smaller than landing
                logo_layout.addWidget(logo, alignment=Qt.AlignCenter)
            else:
                # Fallback to text if SVG not found
                title = QLabel("BUKIT DURI")
                title.setFont(QFont("Arial", 32, QFont.Bold))
                title.setStyleSheet("color: #00FFC6;")
                title.setAlignment(Qt.AlignCenter)
                logo_layout.addWidget(title)
        except ImportError:
            # Fallback if QSvgWidget not available
            title = QLabel("BUKIT DURI")
            title.setFont(QFont("Arial", 32, QFont.Bold))
            title.setStyleSheet("color: #00FFC6;")
            title.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(title)
        
        layout.addLayout(logo_layout)
        
        # Setup message
        self.setup_label = QLabel("Setting up database...")
        self.setup_label.setFont(QFont("Arial", 14))
        self.setup_label.setStyleSheet("color: white;")
        self.setup_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.setup_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setFixedWidth(400)  
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #00E4AA;
                border-radius: 15px;
                background-color: #1A1A1A;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #00FFC6;
                border-radius: 13px;
            }
        """)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setStyleSheet("color: #B0B0B0;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Spinning animation
        self.spinner_label = QLabel("⟳")
        self.spinner_label.setFont(QFont("Arial", 24))
        self.spinner_label.setStyleSheet("color: #00FFC6;")
        self.spinner_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.spinner_label)
        
        self.spinner_timer = QTimer()
        self.spinner_timer.timeout.connect(self.rotate_spinner)
        self.spinner_symbols = ["⟳", "⟲", "⟳", "⟲"]
        self.spinner_index = 0
        
        self.setLayout(layout)
        
    def start_setup(self):
        self.spinner_timer.start(300)
        self.worker = DatabaseSetupWorker()
        self.worker.progress_update.connect(self.update_status)
        self.worker.progress_percentage.connect(self.update_progress)
        self.worker.finished_signal.connect(self.setup_finished)
        self.worker.start()
        
    def rotate_spinner(self):
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_symbols)
        self.spinner_label.setText(self.spinner_symbols[self.spinner_index])
        
    def update_status(self, message):
        self.status_label.setText(message)
        
    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage)
        
    def setup_finished(self, success):
        self.spinner_timer.stop()
        
        if success:
            self.spinner_label.setText("✓")
            self.spinner_label.setStyleSheet("color: #00FFC6; font-size: 32px;")
            self.setup_label.setText("Database setup completed successfully!")
            QTimer.singleShot(2000, lambda: self.setup_completed.emit(True))
        else:
            self.spinner_label.setText("✗")
            self.spinner_label.setStyleSheet("color: #FF6B6B; font-size: 32px;")
            self.setup_label.setText("Database setup failed!")
            
            retry_btn = QPushButton("Retry Setup")
            retry_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0AD87E;
                    color: #06312D;
                    font-weight: bold;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #11f59b;
                }
            """)
            retry_btn.clicked.connect(self.retry_setup)
            self.layout().addWidget(retry_btn)
            
    def retry_setup(self):
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setParent(None)
        
        self.spinner_label.setText("⟳")
        self.spinner_label.setStyleSheet("color: #00FFC6; font-size: 24px;")
        self.setup_label.setText("Retrying database setup...")
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing...")
        self.start_setup()

# Test the setup GUI directly
if __name__ == "__main__":
    app = QApplication(sys.argv)
    setup_gui = DatabaseSetupGUI()
    setup_gui.show()
    setup_gui.start_setup()
    sys.exit(app.exec_())