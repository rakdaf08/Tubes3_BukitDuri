import sys
import os
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QGroupBox, QGridLayout, QSizePolicy, QMessageBox, QTextEdit
)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, QSize

# Add path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.extractor import extract_profile_data

class SummaryPage(QWidget):
    def __init__(self, resume_data=None):
        super().__init__()
        self.resume_data = resume_data or {}
        self.setWindowTitle("CV Summary")
        self.setMinimumSize(1280, 720)
        self.setStyleSheet("background-color: #0B1917; color: white;")
        
        # Pagination variables
        self.skills_page = 0
        self.experience_page = 0
        self.education_page = 0
        self.skills_per_page = 12
        self.items_per_page = 2
        
        # Cache extracted data to avoid multiple extractions
        self._cached_profile = None
        
        self.init_ui()

    def get_cached_profile(self):
        """Get cached profile data to avoid multiple extractions"""
        if self._cached_profile is None:
            content = self.resume_data.get('extracted_text', '') or self.resume_data.get('content', '')
            if content:
                try:
                    self._cached_profile = extract_profile_data(content)
                    print(f"DEBUG - Cached profile with {len(self._cached_profile.get('experience', []))} experiences and {len(self._cached_profile.get('education', []))} education entries")
                except Exception as e:
                    print(f"DEBUG - Error caching profile: {e}")
                    self._cached_profile = {}
            else:
                self._cached_profile = {}
        return self._cached_profile

    def init_ui(self): 
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: #0B1917;
            }
            QScrollBar:vertical {
                background-color: #2C2C2C;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #037F68;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #2BBA91;
            }
        """)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setSpacing(25)
        layout.setContentsMargins(40, 30, 40, 30)

        # Header with back button
        self.create_header(layout)
        
        # Candidate name
        self.create_candidate_name(layout)
        
        # Profile Information Box (Birthdate, Address, Phone, Applying for)
        self.create_profile_info_box(layout)
        
        # Professional Overview section
        self.create_professional_overview_section(layout)
        
        # Job History section (separate)
        self.create_job_history_section(layout)
        
        # Education section (separate)
        self.create_education_section(layout)
        
        layout.addStretch()

    def create_header(self, layout):
        """Create header with back button same as home_gui"""
        header = QHBoxLayout()
        
        # Back button - same style as home_gui
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
        back_btn.clicked.connect(self.go_back)
        
        header.addWidget(back_btn)
        header.addStretch()
        layout.addLayout(header)

    def create_candidate_name(self, layout):
        """Create candidate name display without background"""
        # PRIORITIZED NAME DISPLAY with safe conversion
        display_name = "Unknown Candidate"
        
        # First try to get real name from profile
        first_name = self.safe_str(self.resume_data.get('first_name'), "")
        last_name = self.safe_str(self.resume_data.get('last_name'), "")
        
        if first_name and last_name:
            display_name = f"{first_name} {last_name}"
        elif first_name:
            display_name = first_name
        elif last_name:
            display_name = last_name
        else:
            # Fallback to filename without .pdf and without numbers
            filename = self.safe_str(self.resume_data.get('filename', 'Unknown'))
            if filename.endswith('.pdf'):
                filename = filename[:-4]
            
            # If filename is just numbers, use a generic name
            if filename.isdigit():
                display_name = f"Candidate {filename}"
            else:
                display_name = filename
        
        # Simple name label without background
        name_label = QLabel(display_name)
        name_label.setFont(QFont("Arial", 42, QFont.Bold))
        name_label.setStyleSheet("color: #34BD95; margin: 20px 0px;")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

    def create_profile_info_box(self, layout):
        """Create profile information box with proper sizes and spacing"""
        # Create two side-by-side containers
        profile_main_layout = QHBoxLayout()
        profile_main_layout.setSpacing(20)
        
        left_container = QWidget()
        left_container.setFixedSize(450, 320)  
        left_container.setStyleSheet("""
            QWidget {
                background-color: #037F68;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(20, 20, 20, 20)  
        left_layout.setSpacing(12)  
        
        # Birth date
        birth_date = self.safe_str(self.resume_data.get('date_of_birth'), '01-12-2003')
        
        birth_label = QLabel("Birthdate")
        birth_label.setFont(QFont("Arial", 18, QFont.Bold))  
        birth_label.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 2px 0px;")
        birth_value = QLabel(birth_date)
        birth_value.setFont(QFont("Arial", 14)) 
        birth_value.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 2px 0px 6px 0px;")
        birth_value.setMinimumHeight(25)  
        left_layout.addWidget(birth_label)
        left_layout.addWidget(birth_value)
        
        # Address
        address = self.safe_str(self.resume_data.get('address'), 'Jl. Bayam No. 11, Pangkalpinang')
        
        address_label = QLabel("Address")
        address_label.setFont(QFont("Arial", 18, QFont.Bold))  
        address_label.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 2px 0px;")
        address_value = QLabel(address)
        address_value.setFont(QFont("Arial", 14))  
        address_value.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 2px 0px 6px 0px;")
        address_value.setWordWrap(True)
        address_value.setMinimumHeight(25)  
        left_layout.addWidget(address_label)
        left_layout.addWidget(address_value)
        
        # Phone number
        phone = self.safe_str(self.resume_data.get('phone_number'), '082154321987')
        
        phone_label = QLabel("Phone")
        phone_label.setFont(QFont("Arial", 18, QFont.Bold))  
        phone_label.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 2px 0px;")
        phone_value = QLabel(phone)
        phone_value.setFont(QFont("Arial", 14))  
        phone_value.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 2px 0px 6px 0px;")
        phone_value.setMinimumHeight(25)  
        left_layout.addWidget(phone_label)
        left_layout.addWidget(phone_value)
        
        # Applying for
        role = self.safe_str(self.resume_data.get('application_role'), 'Quality Control Inspector')
        
        role_label = QLabel("Applying for")
        role_label.setFont(QFont("Arial", 18, QFont.Bold))  
        role_label.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 2px 0px;")
        role_value = QLabel(role)
        role_value.setFont(QFont("Arial", 14))  
        role_value.setStyleSheet("color: #FFE066; background: transparent; font-weight: bold; margin: 0px; padding: 2px 0px;")
        role_value.setWordWrap(True)
        role_value.setMinimumHeight(25)  
        left_layout.addWidget(role_label)
        left_layout.addWidget(role_value)

        # Right section - Skills with VERTICAL CENTER alignment
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        # Add stretch at top to center vertically
        right_layout.addStretch()
        
        # Skills title - REDUCED SIZE
        skills_title = QLabel("Skills")
        skills_title.setFont(QFont("Arial", 20, QFont.Bold)) 
        skills_title.setStyleSheet("color: white; background: transparent;")
        skills_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(skills_title)
        
        # Create skills container and use existing update_skills_display
        self.skills_container_profile = QWidget()
        self.skills_layout_profile = QVBoxLayout(self.skills_container_profile)
        self.skills_layout_profile.setContentsMargins(0, 0, 0, 0)
        self.skills_layout_profile.setSpacing(6)  
        
        # Update skills display using existing function (modified)
        self.update_skills_display_for_profile()
        
        right_layout.addWidget(self.skills_container_profile)
        
        # Add stretch at bottom to center vertically
        right_layout.addStretch()
        
        # Add to main layout
        profile_main_layout.addWidget(left_container)
        profile_main_layout.addLayout(right_layout)
        
        layout.addLayout(profile_main_layout)

    def update_skills_display_for_profile(self):
        """Update skills display for profile section with smaller buttons"""
        # Clear existing layout
        self.clear_layout(self.skills_layout_profile)
        
        # Get all skills
        all_skills = self.extract_skills_from_data()
        
        # Remove dummy HTML skills if we have real skills
        if len(all_skills) > 1 and "No skills data available" not in all_skills:
            all_skills = [skill for skill in all_skills if skill != "HTML"]
        
        # Calculate pagination (9 skills per page for 3x3 grid)
        skills_per_page = 9
        start_idx = self.skills_page * skills_per_page
        end_idx = start_idx + skills_per_page
        current_skills = all_skills[start_idx:end_idx]
        
        # Create 3x3 grid for current skills
        skills_grid_widget = QWidget()
        skills_grid_layout = QGridLayout(skills_grid_widget)
        skills_grid_layout.setSpacing(6)  
        skills_grid_layout.setContentsMargins(0, 0, 0, 0)
        
        for i, skill in enumerate(current_skills):
            # Truncate skill text if too long
            truncated_skill = self.truncate_skill_text(skill, max_chars=20)  
            
            skill_btn = QPushButton(truncated_skill)
            skill_btn.setFixedHeight(30)  
            skill_btn.setFixedWidth(160)  
            skill_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 5px;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 4px 6px;
                    border: 1px solid #2BBA91;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #2BBA91;
                }
            """)
            
            row = i // 3
            col = i % 3
            skills_grid_layout.addWidget(skill_btn, row, col)
        
        self.skills_layout_profile.addWidget(skills_grid_widget)
        
        # Add pagination if needed
        if len(all_skills) > skills_per_page:
            nav_layout = QHBoxLayout()
            nav_layout.setSpacing(4)
            nav_layout.setAlignment(Qt.AlignCenter)
            
            prev_btn = QPushButton("←")
            prev_btn.setEnabled(self.skills_page > 0)
            prev_btn.setFixedSize(20, 20)  
            prev_btn.clicked.connect(lambda: self.change_profile_skills_page(-1))
            prev_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #2BBA91; }
                QPushButton:disabled { background-color: #555555; }
            """)
            
            total_pages = (len(all_skills) - 1) // skills_per_page + 1
            page_info = QLabel(f"{self.skills_page + 1}/{total_pages}")
            page_info.setStyleSheet("color: white; font-size: 10px;")  
            page_info.setAlignment(Qt.AlignCenter)
            
            next_btn = QPushButton("→")
            next_btn.setEnabled(end_idx < len(all_skills))
            next_btn.setFixedSize(20, 20)  
            next_btn.clicked.connect(lambda: self.change_profile_skills_page(1))
            next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #2BBA91; }
                QPushButton:disabled { background-color: #555555; }
            """)
            
            nav_layout.addWidget(prev_btn)
            nav_layout.addWidget(page_info)
            nav_layout.addWidget(next_btn)
            
            self.skills_layout_profile.addLayout(nav_layout)

    def safe_str(self, value, default="Not specified"):
        """Safely convert any value to string for display"""
        if value is None:
            return default
        elif hasattr(value, 'strftime'):  # datetime objects
            return value.strftime('%m-%d-%Y')
        elif hasattr(value, 'date'):  # datetime.datetime objects
            return value.date().strftime('%m-%d-%Y')
        else:
            return str(value)

    def create_professional_overview_section(self, layout):
        """Create professional overview section above job history"""
        overview_title = QLabel("Professional Overview")
        overview_title.setFont(QFont("Arial", 28, QFont.Bold))
        overview_title.setStyleSheet("color: #00FFC6; margin: 20px 0px 15px 0px;")
        overview_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(overview_title)

        # Overview container
        overview_container = QGroupBox()
        overview_container.setStyleSheet("""
            QGroupBox {
                background-color: #1E4A42;
                border-radius: 15px;
                border: 2px solid #037F68;
                padding: 20px;
            }
        """)
        overview_layout = QVBoxLayout(overview_container)
        overview_layout.setContentsMargins(25, 25, 25, 25)

        # Overview text
        overview_data = self.extract_overview()
        overview_text = QLabel(overview_data)
        overview_text.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                line-height: 28px;
                background: transparent;
                padding: 15px;
                font-weight: 400;
            }
        """)
        overview_text.setWordWrap(True)
        overview_text.setAlignment(Qt.AlignLeft)
        overview_layout.addWidget(overview_text)

        layout.addWidget(overview_container)

    def create_job_history_section(self, layout):
        """Create job history section - MODIFIED untuk menampilkan setiap job terpisah"""
        # Job History title
        job_title = QLabel("Job History")
        job_title.setFont(QFont("Arial", 28, QFont.Bold))
        job_title.setStyleSheet("color: #00FFC6; margin: 20px 0px 15px 0px;")
        job_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(job_title)

        # Job History layout
        self.job_layout = QVBoxLayout()
        self.job_layout.setSpacing(15)

        # Update job history display - MODIFIED
        self.update_job_history_display_separated()
        
        layout.addLayout(self.job_layout)

    def create_education_section(self, layout):
        """Create education section - MODIFIED untuk menampilkan setiap education terpisah"""
        # Education title
        edu_title = QLabel("Education")
        edu_title.setFont(QFont("Arial", 28, QFont.Bold))
        edu_title.setStyleSheet("color: #00FFC6; margin: 20px 0px 15px 0px;")
        edu_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(edu_title)

        # Education container
        edu_container = QGroupBox()
        edu_container.setStyleSheet("""
            QGroupBox {
                background-color: #1E4A42;
                border-radius: 15px;
                border: 2px solid #037F68;
                padding: 20px;
            }
        """)
        
        self.edu_layout = QVBoxLayout(edu_container)
        self.edu_layout.setContentsMargins(25, 25, 25, 25)
        self.edu_layout.setSpacing(15)

        # Update education display - MODIFIED
        self.update_education_display_separated()
        
        layout.addWidget(edu_container)

    def clear_layout(self, layout):
        """Safely clear all widgets from a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

    def update_job_history_display_separated(self):
        """MODIFIED - Update job history display dengan setiap job terpisah dalam card individual"""
        experience_data = self.extract_experience()
        
        if not experience_data:
            placeholder_text = QLabel("Work experience details will be extracted from CV")
            placeholder_text.setFont(QFont("Arial", 16))
            placeholder_text.setStyleSheet("color: white; text-align: center;")
            placeholder_text.setAlignment(Qt.AlignCenter)
            self.job_layout.addWidget(placeholder_text)
            return

        # Calculate pagination (2 items per page)
        items_per_page = 2
        start_idx = self.experience_page * items_per_page
        end_idx = start_idx + items_per_page
        current_experiences = experience_data[start_idx:end_idx]

        # Create layout untuk menampilkan setiap job dalam card terpisah
        jobs_container = QVBoxLayout()
        jobs_container.setSpacing(20)
        
        for i, exp in enumerate(current_experiences):
            # Create individual job card dengan background
            job_card = QGroupBox()
            job_card.setStyleSheet("""
                QGroupBox {
                    background-color: #A5C5BE;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px 0px;
                }
            """)
            
            job_layout = QVBoxLayout(job_card)
            job_layout.setContentsMargins(20, 15, 20, 15)
            job_layout.setSpacing(8)
            job_layout.setAlignment(Qt.AlignTop)
            
            # Position title (Bold, Size 24, Color #051010)
            title_label = QLabel(exp.get('title', 'Position'))
            title_label.setFont(QFont("Arial", 24, QFont.Bold))
            title_label.setStyleSheet("color: #051010; background: transparent;")
            title_label.setWordWrap(True)
            job_layout.addWidget(title_label)
            
            # Company and period (Medium, Size 20, Color #051010)
            company_period = f"{exp.get('company', 'Company')} • {exp.get('period', 'Period not specified')}"
            company_label = QLabel(company_period)
            company_label.setFont(QFont("Arial", 20, QFont.DemiBold))
            company_label.setStyleSheet("color: #051010; background: transparent;")
            company_label.setWordWrap(True)
            job_layout.addWidget(company_label)
            
            # Description (Regular, Size 16, Color #051010)
            desc_text = exp.get('description', 'Detailed responsibilities available in full CV.')
            if len(desc_text) > 200:
                desc_text = desc_text[:200] + "..."
            
            desc_label = QLabel(desc_text)
            desc_label.setFont(QFont("Arial", 16))
            desc_label.setStyleSheet("color: #051010; background: transparent; line-height: 20px;")
            desc_label.setWordWrap(True)
            job_layout.addWidget(desc_label)
            
            # Add individual job card to container
            jobs_container.addWidget(job_card)
        
        # Add jobs container to main layout
        jobs_widget = QWidget()
        jobs_widget.setLayout(jobs_container)
        self.job_layout.addWidget(jobs_widget)

        # Navigation
        if len(experience_data) > items_per_page:
            nav_layout = QHBoxLayout()
            nav_layout.setSpacing(8)
            nav_layout.setAlignment(Qt.AlignCenter)
            
            prev_btn = QPushButton("←")
            prev_btn.setEnabled(self.experience_page > 0)
            prev_btn.setFixedSize(30, 30)
            prev_btn.clicked.connect(lambda: self.change_experience_page(-1))
            prev_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 16px;
                }
                QPushButton:hover { background-color: #2BBA91; }
                QPushButton:disabled { background-color: #555555; }
            """)
            
            total_pages = (len(experience_data) - 1) // items_per_page + 1
            page_info = QLabel(f"Page {self.experience_page + 1} of {total_pages}")
            page_info.setStyleSheet("color: white; font-size: 14px;")
            page_info.setAlignment(Qt.AlignCenter)
            
            next_btn = QPushButton("→")
            next_btn.setEnabled(end_idx < len(experience_data))
            next_btn.setFixedSize(30, 30)
            next_btn.clicked.connect(lambda: self.change_experience_page(1))
            next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 16px;
                }
                QPushButton:hover { background-color: #2BBA91; }
                QPushButton:disabled { background-color: #555555; }
            """)
            
            nav_layout.addWidget(prev_btn)
            nav_layout.addWidget(page_info)
            nav_layout.addWidget(next_btn)
            
            self.job_layout.addLayout(nav_layout)

    def update_education_display_separated(self):
        """MODIFIED - Update education display dengan setiap education terpisah"""
        education_data = self.extract_education()
        
        if not education_data:
            placeholder_text = QLabel("Education details will be extracted from CV")
            placeholder_text.setFont(QFont("Arial", 16))
            placeholder_text.setStyleSheet("color: white; background: transparent; text-align: center;")
            placeholder_text.setAlignment(Qt.AlignCenter)
            self.edu_layout.addWidget(placeholder_text)
            return

        # Calculate pagination
        start_idx = self.education_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        current_education = education_data[start_idx:end_idx]

        # Display education entries - SETIAP EDUCATION DALAM CARD TERPISAH
        for edu in current_education:
            # Create individual education card
            edu_card = QGroupBox()
            edu_card.setStyleSheet("""
                QGroupBox {
                    background-color: #2A5A50;
                    border-radius: 10px;
                    border: 1px solid #037F68;
                    padding: 15px;
                    margin: 8px 0px;
                }
            """)
            
            edu_card_layout = QVBoxLayout(edu_card)
            edu_card_layout.setContentsMargins(15, 12, 15, 12)
            edu_card_layout.setSpacing(6)
            
            # Degree with field 
            degree_text = edu.get('degree', 'Degree')
            if edu.get('field', '') and edu.get('field', '').strip() and edu.get('field', '') != 'Field of Study':
                degree_text += f" in {edu.get('field', '')}"
            
            degree_label = QLabel(degree_text)
            degree_label.setFont(QFont("Arial", 18, QFont.Bold))
            degree_label.setStyleSheet("color: #00FFC6; background: transparent; margin-bottom: 5px;")
            degree_label.setWordWrap(True)
            
            # Institution and Year 
            institution_text = edu.get('institution', 'Institution')
            if edu.get('date', '') and edu.get('date', '') != 'Year not specified':
                institution_text += f" • {edu.get('date', '')}"
            
            info_label = QLabel(institution_text)
            info_label.setFont(QFont("Arial", 14))
            info_label.setStyleSheet("color: white; background: transparent; margin-bottom: 8px;")
            info_label.setWordWrap(True)
            
            edu_card_layout.addWidget(degree_label)
            edu_card_layout.addWidget(info_label)
            
            # Add individual education card to main layout
            self.edu_layout.addWidget(edu_card)

        # Navigation
        if len(education_data) > self.items_per_page:
            nav_layout = QHBoxLayout()
            
            prev_btn = QPushButton("← Previous")
            prev_btn.setEnabled(self.education_page > 0)
            prev_btn.clicked.connect(lambda: self.change_education_page(-1))
            prev_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #2BBA91; }
                QPushButton:disabled { background-color: #555555; }
            """)
            
            total_pages = (len(education_data) - 1) // self.items_per_page + 1
            page_info = QLabel(f"Page {self.education_page + 1} of {total_pages}")
            page_info.setStyleSheet("color: #00FFC6; font-size: 14px;")
            page_info.setAlignment(Qt.AlignCenter)
            
            next_btn = QPushButton("Next →")
            next_btn.setEnabled(end_idx < len(education_data))
            next_btn.clicked.connect(lambda: self.change_education_page(1))
            next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #2BBA91; }
                QPushButton:disabled { background-color: #555555; }
            """)
            
            nav_layout.addWidget(prev_btn)
            nav_layout.addStretch()
            nav_layout.addWidget(page_info)
            nav_layout.addStretch()
            nav_layout.addWidget(next_btn)
            
            self.edu_layout.addLayout(nav_layout)

    def extract_skills_from_data(self):
        """Extract skills using cached profile data"""
        try:
            profile = self.get_cached_profile()
            skills = profile.get('skills', [])
            
            print(f"DEBUG - Using cached skills: {len(skills)} found")
            return skills if skills else ["No skills data available"]
        except Exception as e:
            print(f"Error extracting skills: {e}")
            return ["Skills extraction error"]

    def extract_experience(self):
        """Extract work experience using cached profile data - FIXED untuk mendapatkan semua data"""
        try:
            profile = self.get_cached_profile()
            experiences = profile.get('experience', [])
            
            print(f"DEBUG - Using cached experiences: {len(experiences)} found")
            
            # Convert to expected format
            formatted_experiences = []
            for exp in experiences:
                if isinstance(exp, dict):
                    formatted_exp = {
                        'title': exp.get('title', 'Position'),
                        'company': exp.get('company', 'Company'),
                        'period': f"{exp.get('start', 'Start')} - {exp.get('end', 'End')}",
                        'description': exp.get('description', 'Job responsibilities and achievements.')
                    }
                    formatted_experiences.append(formatted_exp)
            
            return formatted_experiences
            
        except Exception as e:
            print(f"DEBUG - Error extracting experience: {e}")
            return []

    def extract_education(self):
        """Extract education using cached profile data - FIXED untuk mendapatkan semua data"""
        try:
            profile = self.get_cached_profile()
            education = profile.get('education', [])
            
            print(f"DEBUG - Using cached education: {len(education)} found")
            
            # Convert to expected format
            formatted_education = []
            for edu in education:
                if isinstance(edu, dict):
                    formatted_edu = {
                        'degree': edu.get('degree', 'Degree'),
                        'field': edu.get('field', ''),
                        'institution': edu.get('institution', 'Institution'),
                        'date': edu.get('date', 'Year not specified')
                    }
                    formatted_education.append(formatted_edu)
            
            return formatted_education
            
        except Exception as e:
            print(f"DEBUG - Error extracting education: {e}")
            return []

    def extract_overview(self):
        """Extract overview using cached profile data"""
        try:
            profile = self.get_cached_profile()
            overview = profile.get('overview', '')
            
            if overview and len(overview.strip()) > 50:
                return overview
            
            # Fallback
            return "No overview has found. Experienced professional with demonstrated skills and accomplishments in their field."
            
        except Exception as e:
            print(f"DEBUG - Error extracting overview: {e}")
            return "Professional summary will be extracted from the CV document once processed."

    def extract_gpa(self):
        """Extract GPA using cached profile data"""
        try:
            profile = self.get_cached_profile()
            gpa_list = profile.get('gpa', [])
            
            return gpa_list[0] if gpa_list else None
        except Exception as e:
            print(f"Error extracting GPA: {e}")
            return None

    def extract_certifications(self):
        """Extract certifications using cached profile data"""
        try:
            profile = self.get_cached_profile()
            return profile.get('certifications', [])
        except Exception as e:
            print(f"Error extracting certifications: {e}")
            return []

    def extract_achievements(self):
        """Extract achievements using cached profile data"""
        try:
            profile = self.get_cached_profile()
            return profile.get('achievements', [])
        except Exception as e:
            print(f"Error extracting achievements: {e}")
            return []

    def truncate_skill_text(self, text, max_chars=25):
        """Truncate skill text for single line display"""
        if len(text) <= max_chars:
            return text
        
        # Simple truncation for single line
        return text[:max_chars-3] + "..."

    def change_profile_skills_page(self, direction):
        """Change profile skills page"""
        self.skills_page += direction
        self.update_skills_display_for_profile()
    
    def change_experience_page(self, direction):
        """Change experience page - MODIFIED"""
        self.experience_page += direction
        # Clear existing layout safely
        self.clear_layout(self.job_layout)
        # Update display
        self.update_job_history_display_separated()

    def change_education_page(self, direction):
        """Change education page - MODIFIED"""
        self.education_page += direction
        # Clear existing layout safely
        self.clear_layout(self.edu_layout)
        # Update display
        self.update_education_display_separated()

    def go_back(self):
        """Go back to previous window"""
        try:
            self.close()
        except Exception as e:
            print(f"DEBUG - Error in go_back: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SummaryPage()
    window.show()
    sys.exit(app.exec_())