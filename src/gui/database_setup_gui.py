import os
import sys
import subprocess

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

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

# Import database components
try:
    from db.db_connector import DatabaseManager
    from core.extractor import extract_text_from_pdf, extract_profile_data
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

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
            
            # Call the setup function with progress callbacks
            success = self.setup_database_with_progress()
            
            self.progress_update.emit("Setup completed!" if success else "Setup failed!")
            self.progress_percentage.emit(100)
            self.finished_signal.emit(success)
            
        except Exception as e:
            self.progress_update.emit(f"Error: {str(e)}")
            self.progress_percentage.emit(0)
            self.finished_signal.emit(False)
    
    def setup_database_with_progress(self):
        """Setup database with progress updates"""
        try:
            # Drop existing database first
            self.progress_update.emit("Dropping existing database...")
            self.progress_percentage.emit(10)
            
            import mysql.connector
            try:
                temp_conn = mysql.connector.connect(
                    host='localhost',
                    user='root',
                    password='123'
                )
                cursor = temp_conn.cursor()
                cursor.execute("DROP DATABASE IF EXISTS Tubes3Stima")
                temp_conn.close()
                print("Dropped existing database")
            except Exception as e:
                print(f"Database drop error (normal if not exists): {e}")
            
            self.progress_update.emit("Creating fresh database...")
            self.progress_percentage.emit(15)
            
            db_config = {
                'host': 'localhost',
                'user': 'root',
                'password': '123',
                'database': 'Tubes3Stima',
            }
            
            db = DatabaseManager(**db_config)
            
            self.progress_update.emit("Creating database and tables...")
            self.progress_percentage.emit(20)
            
            if not db.create_database_and_tables():
                self.progress_update.emit("Failed to create database/tables")
                return False
            
            self.progress_update.emit("Connecting to database...")
            self.progress_percentage.emit(25)
            
            if not db.connect():
                self.progress_update.emit("Failed to connect to database")
                return False
            
            # Run seeding if exists
            self.progress_update.emit("Running seeding SQL...")
            self.progress_percentage.emit(30)
            self.run_seeding_sql(db_config)
            
            # Add profile columns
            self.progress_update.emit("Adding profile columns...")
            self.progress_percentage.emit(35)
            self.add_profile_columns_to_resumes(db)
            
            self.progress_update.emit("Loading resume data from PDF files...")
            self.progress_percentage.emit(40)
            
            # Load data with progress updates
            self.load_resume_data_with_progress(db)
            
            self.progress_update.emit("Finalizing setup...")
            self.progress_percentage.emit(95)
            
            db.disconnect()
            return True
            
        except Exception as e:
            self.progress_update.emit(f"Setup error: {str(e)}")
            print(f"Setup database error: {e}")
            return False
    
    def run_seeding_sql(self, db_config):
        """Run seeding SQL if exists"""
        try:
            seeding_file = os.path.join(root_dir, 'tubes3_seeding.sql')
            if os.path.exists(seeding_file):
                print(f"Found seeding file: {seeding_file}")
                # Run MySQL command to execute the SQL file
                cmd = [
                    'mysql',
                    '-h', db_config['host'],
                    '-u', db_config['user'],
                    db_config['database']
                ]
                
                # Add password if not empty
                if db_config['password']:
                    cmd.extend(['-p' + db_config['password']])
                
                # Execute the SQL file
                with open(seeding_file, 'r', encoding='utf-8') as f:
                    result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("Seeding SQL executed successfully")
                else:
                    print(f"Error executing seeding SQL: {result.stderr}")
                return True
            else:
                print("No seeding file found, skipping...")
                return True
            
        except Exception as e:
            print(f"Seeding error: {e}")
            return False
    
    def add_profile_columns_to_resumes(self, db: DatabaseManager):
        """Add profile columns to existing resumes table"""
        try:
            cursor = db.connection.cursor()
            
            # Check if columns already exist
            cursor.execute("DESCRIBE resumes")
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            columns_to_add = [
                ('applicant_id', 'INT DEFAULT NULL'),
                ('first_name', 'VARCHAR(50) DEFAULT NULL'),
                ('last_name', 'VARCHAR(50) DEFAULT NULL'),
                ('date_of_birth', 'DATE DEFAULT NULL'),
                ('address', 'VARCHAR(255) DEFAULT NULL'),
                ('phone_number', 'VARCHAR(20) DEFAULT NULL'),
                ('application_role', 'VARCHAR(100) DEFAULT NULL')
            ]
            
            for col_name, col_def in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE resumes ADD COLUMN {col_name} {col_def}")
                        print(f"✓ Added column {col_name}")
                    except Exception as col_error:
                        print(f"Warning: Could not add column {col_name}: {col_error}")
                else:
                    print(f"✓ Column {col_name} already exists")
            
            db.connection.commit()
            print("✓ Profile columns setup completed")
            
        except Exception as e:
            print(f"Error adding profile columns: {e}")
            db.connection.rollback()
    
    def load_resume_data_with_progress(self, db: DatabaseManager):
        """Load resume data with progress updates"""
        pdf_dir = os.path.join(root_dir, "data", "pdf")
        
        self.progress_update.emit(f"Looking for PDF files in: {pdf_dir}")
        
        if not os.path.exists(pdf_dir):
            self.progress_update.emit("PDF directory not found - skipping data load...")
            print(f"PDF directory not found: {pdf_dir}")
            return
        
        # Count total files
        total_files = 0
        categories = []
        for category in os.listdir(pdf_dir):
            category_path = os.path.join(pdf_dir, category)
            if os.path.isdir(category_path):
                pdf_files = [f for f in os.listdir(category_path) if f.endswith('.pdf')]
                if pdf_files:  # Only add categories with PDF files
                    total_files += len(pdf_files)
                    categories.append((category, pdf_files))
        
        if total_files == 0:
            self.progress_update.emit("No PDF files found")
            print("No PDF files found")
            return
        
        # Process files with progress updates
        processed = 0
        loaded_count = 0
        
        self.progress_update.emit(f"Found {total_files} PDF files to process...")
        print(f"Total files to process: {total_files}")
        
        for category, pdf_files in categories:
            self.progress_update.emit(f"Processing {category} category ({len(pdf_files)} files)...")
            print(f"Processing category {category}: {len(pdf_files)} files")
            files_to_process = pdf_files 
            
            for filename in files_to_process:
                pdf_path = os.path.join(pdf_dir, category, filename)
                
                try:
                    # Extract and process
                    extracted_text = extract_text_from_pdf(pdf_path)
                    if extracted_text:
                        profile = extract_profile_data(extracted_text)
                        
                        # Prepare data for insertion
                        skills = ", ".join(profile.get('skills', []))[:2000]
                        
                        experience_list = []
                        for exp in profile.get('experience', []):
                            exp_text = f"{exp.get('title', '')} ({exp.get('start', '')} - {exp.get('end', '')})"
                            experience_list.append(exp_text)
                        experience = " | ".join(experience_list)[:2000]
                        
                        education_list = []
                        for edu in profile.get('education', []):
                            edu_text = f"{edu.get('degree', '')} in {edu.get('field', '')}"
                            education_list.append(edu_text)
                        education = " | ".join(education_list)[:1000]
                        
                        gpa = float(profile['gpa'][0]) if profile.get('gpa') else None
                        certifications = ", ".join(profile.get('certifications', []))[:1000]
                        
                        # Insert to database
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
                            loaded_count += 1
                            # Only print every 10th success to avoid spam
                            if loaded_count % 10 == 0:
                                print(f"✓ Inserted {loaded_count} files so far...")
                        else:
                            print(f"✗ Failed to insert {filename}")
                    
                    processed += 1
                    
                    progress_percent = 40 + int((processed / total_files) * 50)
                    self.progress_percentage.emit(progress_percent)
                    
                    if processed % 25 == 0:
                        self.progress_update.emit(f"Processed {processed}/{total_files} files ({loaded_count} loaded)...")
                        print(f"Progress: {processed}/{total_files} files processed, {loaded_count} loaded successfully")
                    
                except Exception as e:
                    self.progress_update.emit(f"Error processing {filename}: {str(e)}")
                    print(f"Error processing {filename}: {e}")
                    processed += 1
                    continue
        
        print(f"Final: Successfully loaded {loaded_count} out of {processed} files processed")
        self.progress_update.emit(f"Loaded {loaded_count} resumes successfully!")
        
        # Show final statistics
        self.progress_update.emit(f"Setup completed: {loaded_count}/{total_files} files loaded into database")

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
        
        # Logo section
        logo_layout = QHBoxLayout()
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
        # Remove retry button
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setParent(None)
        
        # Reset UI
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