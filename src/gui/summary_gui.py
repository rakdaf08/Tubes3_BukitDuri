import sys
import os
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QGroupBox, QGridLayout, QSizePolicy, QMessageBox, QTextEdit
)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, QSize

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
        
        self.init_ui()

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
        name_label.setStyleSheet("color: #34BD95; margin: 20px 0px;")  # Changed color, removed background
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

    def create_profile_info_box(self, layout):
        """Create profile information box with proper sizes and spacing"""
        # Create two side-by-side containers
        profile_main_layout = QHBoxLayout()
        profile_main_layout.setSpacing(20)
        
        # Left container - Personal Info (bigger size again)
        left_container = QWidget()
        left_container.setFixedSize(530, 350)  # Increased height from 320 to 350
        left_container.setStyleSheet("""
            QWidget {
                background-color: #037F68;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(25, 30, 25, 30)  # Increased top/bottom margins
        left_layout.setSpacing(15)  # Increased spacing between sections
        
        # Birth date
        birth_date = self.resume_data.get('date_of_birth', '05-19-2025')
        if hasattr(birth_date, 'strftime'):
            birth_date = birth_date.strftime('%m-%d-%Y')
        elif birth_date is None:
            birth_date = 'Not specified'
        else:
            birth_date = str(birth_date)
        
        birth_label = QLabel("Birthdate")
        birth_label.setFont(QFont("Arial", 24, QFont.Bold))
        birth_label.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 3px 0px;")
        birth_value = QLabel(birth_date)
        birth_value.setFont(QFont("Arial", 20))
        birth_value.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 3px 0px 8px 0px;")  # More padding
        birth_value.setMinimumHeight(30)  # Ensure minimum height
        left_layout.addWidget(birth_label)
        left_layout.addWidget(birth_value)
        
        # Address
        address = self.resume_data.get('address', 'Mesjid Salman ITB')
        address = str(address) if address is not None else 'Address not specified'
        
        address_label = QLabel("Address")
        address_label.setFont(QFont("Arial", 24, QFont.Bold))
        address_label.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 3px 0px;")
        address_value = QLabel(address)
        address_value.setFont(QFont("Arial", 20))
        address_value.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 3px 0px 8px 0px;")  # More padding
        address_value.setWordWrap(True)
        address_value.setMinimumHeight(30)  # Ensure minimum height
        left_layout.addWidget(address_label)
        left_layout.addWidget(address_value)
        
        # Phone number
        phone = self.resume_data.get('phone_number', '+6281031231940')
        phone = str(phone) if phone is not None else 'Phone not specified'
        
        phone_label = QLabel("Phone")
        phone_label.setFont(QFont("Arial", 24, QFont.Bold))
        phone_label.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 3px 0px;")
        phone_value = QLabel(phone)
        phone_value.setFont(QFont("Arial", 20))
        phone_value.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 3px 0px 8px 0px;")  # More padding
        phone_value.setMinimumHeight(30)  # Ensure minimum height
        left_layout.addWidget(phone_label)
        left_layout.addWidget(phone_value)
        
        # Applying for
        role = self.resume_data.get('application_role', 'Software Engineer')
        role = str(role) if role is not None else 'Role not specified'
        
        role_label = QLabel("Applying for")
        role_label.setFont(QFont("Arial", 24, QFont.Bold))
        role_label.setStyleSheet("color: white; background: transparent; margin: 0px; padding: 3px 0px;")
        role_value = QLabel(role)
        role_value.setFont(QFont("Arial", 20))
        role_value.setStyleSheet("color: #FFE066; background: transparent; font-weight: bold; margin: 0px; padding: 3px 0px;")
        role_value.setWordWrap(True)
        role_value.setMinimumHeight(30)  # Ensure minimum height
        left_layout.addWidget(role_label)
        left_layout.addWidget(role_value)

        # Right section - Skills with VERTICAL CENTER alignment
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        # Add stretch at top to center vertically
        right_layout.addStretch()
        
        # Skills title - BOLD and centered vertically with profile info
        skills_title = QLabel("Skills")
        skills_title.setFont(QFont("Arial", 24, QFont.Bold))  # Added Bold
        skills_title.setStyleSheet("color: white; background: transparent;")
        skills_title.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(skills_title)
        
        # Create skills container and use existing update_skills_display
        self.skills_container_profile = QWidget()
        self.skills_layout_profile = QVBoxLayout(self.skills_container_profile)
        self.skills_layout_profile.setContentsMargins(0, 0, 0, 0)
        self.skills_layout_profile.setSpacing(8)
        
        # Update skills display using existing function (modified)
        self.update_skills_display_for_profile()
        
        right_layout.addWidget(self.skills_container_profile)
        
        # Add stretch at bottom to center vertically
        right_layout.addStretch()
        
        # Add to main layout
        profile_main_layout.addWidget(left_container)
        profile_main_layout.addLayout(right_layout)
        
        layout.addLayout(profile_main_layout)
    
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

    def create_skills_section(self, layout):
        """Create skills section with pagination"""
        # Skills title
        skills_title = QLabel("Skills & Competencies")
        skills_title.setFont(QFont("Arial", 28, QFont.Bold))
        skills_title.setStyleSheet("color: #00FFC6; margin: 20px 0px 15px 0px;")
        skills_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(skills_title)

        # Get all skills
        all_skills = self.extract_skills_from_data()

        # Skills container
        self.skills_container = QGroupBox()
        self.skills_container.setStyleSheet("""
            QGroupBox {
                background-color: #1A3A35;
                border-radius: 15px;
                border: 2px solid #037F68;
                padding: 20px;
            }
        """)
        
        self.skills_layout = QVBoxLayout(self.skills_container)
        self.skills_layout.setSpacing(15)
        self.skills_layout.setContentsMargins(25, 25, 25, 25)

        # Update skills display
        self.update_skills_display(all_skills)
        
        layout.addWidget(self.skills_container)

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

    def clear_layout(self, layout):
        """Safely clear all widgets from a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())
                
    def update_skills_display_for_profile(self):
        """Update skills display for profile section with wider buttons"""
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
        skills_grid_layout.setSpacing(8)
        skills_grid_layout.setContentsMargins(0, 0, 0, 0)
        
        for i, skill in enumerate(current_skills):
            # Truncate skill text if too long - INCREASED max_chars
            truncated_skill = self.truncate_skill_text(skill, max_chars=25)  # Increased from 15 to 25
            
            skill_btn = QPushButton(truncated_skill)
            skill_btn.setFixedHeight(35)  # Single line height
            skill_btn.setFixedWidth(180)  # INCREASED width from 120 to 180
            skill_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 6px 8px;
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
        
        # Add pagination if needed - COMPACT SPACING
        if len(all_skills) > skills_per_page:
            nav_layout = QHBoxLayout()
            nav_layout.setSpacing(5)  # Very tight spacing
            nav_layout.setAlignment(Qt.AlignCenter)
            
            prev_btn = QPushButton("←")
            prev_btn.setEnabled(self.skills_page > 0)
            prev_btn.setFixedSize(25, 25)  # Smaller buttons
            prev_btn.clicked.connect(lambda: self.change_profile_skills_page(-1))
            prev_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #2BBA91; }
                QPushButton:disabled { background-color: #555555; }
            """)
            
            total_pages = (len(all_skills) - 1) // skills_per_page + 1
            page_info = QLabel(f"{self.skills_page + 1}/{total_pages}")
            page_info.setStyleSheet("color: white; font-size: 11px;")
            page_info.setAlignment(Qt.AlignCenter)
            
            next_btn = QPushButton("→")
            next_btn.setEnabled(end_idx < len(all_skills))
            next_btn.setFixedSize(25, 25)  # Smaller buttons
            next_btn.clicked.connect(lambda: self.change_profile_skills_page(1))
            next_btn.setStyleSheet("""
                QPushButton {
                    background-color: #037F68;
                    color: white;
                    border-radius: 12px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #2BBA91; }
                QPushButton:disabled { background-color: #555555; }
            """)
            
            nav_layout.addWidget(prev_btn)
            nav_layout.addWidget(page_info)
            nav_layout.addWidget(next_btn)
            
            self.skills_layout_profile.addLayout(nav_layout)

    def truncate_skill_text(self, text, max_chars=25):  # Updated default to 25
        """Truncate skill text for single line display"""
        if len(text) <= max_chars:
            return text
        
        # Simple truncation for single line
        return text[:max_chars-3] + "..."

    def change_profile_skills_page(self, direction):
        """Change profile skills page"""
        self.skills_page += direction
        self.update_skills_display_for_profile()

    def create_education_section(self, layout):
        """Create education section like Professional Overview"""
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

        # Update education display
        self.update_education_display_new()
        
        layout.addWidget(edu_container)

    def create_job_history_section(self, layout):
        """Create job history section WITHOUT container"""
        # Job History title
        job_title = QLabel("Job History")
        job_title.setFont(QFont("Arial", 28, QFont.Bold))
        job_title.setStyleSheet("color: #00FFC6; margin: 20px 0px 15px 0px;")
        job_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(job_title)

        # Job History layout (NO CONTAINER)
        self.job_layout = QVBoxLayout()
        self.job_layout.setSpacing(15)

        # Update job history display
        self.update_job_history_display()
        
        layout.addLayout(self.job_layout)  # Add layout directly, not container

    def update_job_history_display(self):
        """Update job history display with 2x2 grid layout"""
        experience_data = self.extract_experience()
        
        if not experience_data:
            placeholder_text = QLabel("Work experience details will be extracted from CV")
            placeholder_text.setFont(QFont("Arial", 16))
            placeholder_text.setStyleSheet("color: white; text-align: center;")
            placeholder_text.setAlignment(Qt.AlignCenter)
            self.job_layout.addWidget(placeholder_text)
            return

        # Calculate pagination (4 items per page for 2x2 grid)
        items_per_page = 4
        start_idx = self.experience_page * items_per_page
        end_idx = start_idx + items_per_page
        current_experiences = experience_data[start_idx:end_idx]

        # Create 2x2 grid layout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        
        for i, exp in enumerate(current_experiences):
            # Create job box (530x150)
            job_box = QWidget()
            job_box.setFixedSize(530, 150)
            job_box.setStyleSheet("""
                QWidget {
                    background-color: #A5C5BE;
                    border-radius: 10px;
                }
            """)
            
            job_layout = QVBoxLayout(job_box)
            job_layout.setContentsMargins(20, 15, 20, 15)
            job_layout.setSpacing(5)
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
            if len(desc_text) > 120:
                desc_text = desc_text[:120] + "..."
            
            desc_label = QLabel(desc_text)
            desc_label.setFont(QFont("Arial", 16))
            desc_label.setStyleSheet("color: #051010; background: transparent; line-height: 20px;")
            desc_label.setWordWrap(True)
            job_layout.addWidget(desc_label)
            
            # Add to grid (2x2 layout)
            row = i // 2
            col = i % 2
            grid_layout.addWidget(job_box, row, col)
        
        self.job_layout.addLayout(grid_layout)

        # Compact Navigation (symbols only, close together)
        if len(experience_data) > items_per_page:
            nav_layout = QHBoxLayout()
            nav_layout.setSpacing(8)  # Tight spacing
            nav_layout.setAlignment(Qt.AlignCenter)
            
            prev_btn = QPushButton("←")  # Symbol only
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
            page_info.setStyleSheet("color: white; font-size: 14px;")  # No background
            page_info.setAlignment(Qt.AlignCenter)
            
            next_btn = QPushButton("→")  # Symbol only
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

    def update_education_display_new(self):
        """Update education display without item backgrounds"""
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

        # Display education entries WITHOUT background containers
        for edu in current_education:
            # Degree with field - NO BACKGROUND
            degree_text = edu.get('degree', 'Degree')
            if edu.get('field', '') and edu.get('field', '').strip():
                degree_text += f" in {edu.get('field', '')}"
            
            degree_label = QLabel(degree_text)
            degree_label.setFont(QFont("Arial", 18, QFont.Bold))
            degree_label.setStyleSheet("color: white; background: transparent; margin-bottom: 5px;")
            degree_label.setWordWrap(True)
            
            # Institution and Year - NO BACKGROUND
            institution_text = edu.get('institution', 'Institution')
            if edu.get('date', '') and edu.get('date', '') != 'Year not specified':
                institution_text += f" • {edu.get('date', '')}"
            
            info_label = QLabel(institution_text)
            info_label.setFont(QFont("Arial", 14))
            info_label.setStyleSheet("color: #00FFC6; background: transparent; margin-bottom: 20px;")
            info_label.setWordWrap(True)
            
            self.edu_layout.addWidget(degree_label)
            self.edu_layout.addWidget(info_label)

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
        """Extract skills from database - improved parsing"""
        # First try to get from skills field
        skills_text = self.resume_data.get('skills', '')
        
        # Also try to extract from content if skills field is empty
        content = self.resume_data.get('extracted_text', '') or self.resume_data.get('content', '')
        
        all_skills = []
        
        if skills_text and skills_text.strip():
            # Split by comma and clean up
            skills = [skill.strip() for skill in skills_text.split(',') if skill.strip()]
            all_skills.extend(skills)
        
        # Also try to extract expertise from Professional Summary
        if content:
            # Look for "Expertise spans:" pattern
            expertise_match = re.search(r'Expertise spans:\s*([^.]+)', content, re.IGNORECASE)
            if expertise_match:
                expertise_text = expertise_match.group(1)
                expertise_skills = [skill.strip() for skill in expertise_text.split(',') if skill.strip()]
                all_skills.extend(expertise_skills)
            
            # Look for skills section
            skills_section_match = re.search(r'(?i)skills[:\s]*\n+(.*?)(?=\n\s*(?:\Z|[A-Z][a-z]+\s*:))', content, re.DOTALL)
            if skills_section_match:
                skills_section = skills_section_match.group(1)
                # Split by comma and clean
                section_skills = [skill.strip() for skill in skills_section.split(',') if skill.strip() and len(skill.strip()) > 2]
                all_skills.extend(section_skills)
        
        # Remove duplicates while preserving order
        seen = set()
        clean_skills = []
        for skill in all_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen and len(skill) > 2:
                seen.add(skill_lower)
                clean_skills.append(skill)
        
        return clean_skills if clean_skills else ["No skills data available"]
    
    def change_experience_page(self, direction):
        """Change experience page"""
        self.experience_page += direction
        # Clear existing layout safely
        self.clear_layout(self.job_layout)
        # Update display
        self.update_job_history_display()

    def change_education_page(self, direction):
        """Change education page"""
        self.education_page += direction
        # Clear existing layout safely
        self.clear_layout(self.edu_layout)
        # Update display
        self.update_education_display_new()
    
    def extract_experience(self):
        """Extract work experience - robust parsing for multiple CV formats"""
        content = self.resume_data.get('extracted_text', '') or self.resume_data.get('content', '')
        
        if not content:
            return []
        
        experiences = []
        
        print(f"DEBUG - Content length: {len(content)}")
        
        # Look for experience sections with multiple possible headers
        exp_headers = [
            r'(?i)(?:work\s+)?experience[:\s]*',
            r'(?i)work\s+history[:\s]*',
            r'(?i)employment[:\s]*',
            r'(?i)professional\s+experience[:\s]*',
            r'(?i)career\s+history[:\s]*'
        ]
        
        exp_section = ""
        for header in exp_headers:
            pattern = header + r'\n+(.*?)(?=\n\s*(?:education|skills|certifications|accomplishments|training)\b|$)'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                exp_section = match.group(1)
                print(f"DEBUG - Found experience section with header: {header}")
                break
        
        if not exp_section:
            print("DEBUG - No experience section found")
            return []
        
        print(f"DEBUG - Experience section preview: {exp_section[:300]}...")
        
        # Multiple parsing strategies
        
        # Strategy 1: Date range patterns (MM/YYYY to MM/YYYY, MM/YYYY to Current, etc.)
        date_patterns = [
            r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current)',  # MM/YYYY to MM/YYYY
            r'(\d{4})\s+to\s+(\d{4}|Current)',                   # YYYY to YYYY
            r'(\w+\s+\d{4})\s+to\s+(\w+\s+\d{4}|Current)',      # Month YYYY to Month YYYY
            r'(\d{1,2}/\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{1,2}/\d{4}|Current)', # MM/DD/YYYY
        ]
        
        for date_pattern in date_patterns:
            matches = list(re.finditer(date_pattern, exp_section))
            if matches:
                print(f"DEBUG - Found {len(matches)} date matches with pattern: {date_pattern}")
                
                for i, match in enumerate(matches):
                    period = match.group(0)
                    start_pos = match.end()
                    
                    # Find end position
                    end_pos = len(exp_section)
                    if i + 1 < len(matches):
                        end_pos = matches[i + 1].start()
                    
                    job_content = exp_section[start_pos:end_pos].strip()
                    
                    # Parse job content
                    job_data = self.parse_job_content(job_content, period)
                    if job_data:
                        experiences.append(job_data)
                
                if experiences:
                    break
        
        # Strategy 2: If no date patterns, look for job titles followed by company names
        if not experiences:
            print("DEBUG - Trying job title pattern matching")
            
            # Look for common job title patterns
            job_title_patterns = [
                r'([A-Z][A-Za-z\s]+(?:Manager|Director|Assistant|Coordinator|Analyst|Engineer|Teacher|Specialist|Supervisor|Lead|Officer|Consultant))\s*,?\s*(\d{1,2}/\d{4}|\d{4}|\w+\s+\d{4})',
                r'([A-Z][A-Za-z\s]+)\s*,\s*(\d{1,2}/\d{4}|\d{4}|\w+\s+\d{4})',
            ]
            
            for pattern in job_title_patterns:
                matches = list(re.finditer(pattern, exp_section))
                if matches:
                    for match in matches:
                        title = match.group(1).strip()
                        date = match.group(2)
                        
                        # Look for company name in the following lines
                        start_pos = match.end()
                        next_content = exp_section[start_pos:start_pos+500]
                        lines = [line.strip() for line in next_content.split('\n') if line.strip()]
                        
                        company = "Company Name"
                        description = ""
                        
                        if lines:
                            # First line might be company
                            if "Company Name" in lines[0] or len(lines[0]) < 100:
                                company = lines[0].replace("Company Name", "Company").strip()
                                description = " ".join(lines[1:5]) if len(lines) > 1 else ""
                            else:
                                description = " ".join(lines[0:5])
                        
                        experiences.append({
                            'title': title,
                            'company': company,
                            'period': date,
                            'description': description[:300]
                        })
                    
                    if experiences:
                        break
        
        # Strategy 3: Parse by line structure (fallback)
        if not experiences:
            print("DEBUG - Trying line-by-line parsing")
            experiences = self.parse_experience_by_lines(exp_section)
        
        print(f"DEBUG - Extracted {len(experiences)} experiences")
        return experiences

    def parse_job_content(self, content, period):
        """Parse individual job content"""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # First line usually contains title and company
        first_line = lines[0]
        
        # Clean special characters
        first_line = re.sub(r'[ï¼​â€"]', '', first_line)
        
        # Extract title and company
        title = ""
        company = "Company Name"
        
        # Pattern: "Title Company Name – Location"
        if 'Company Name' in first_line:
            parts = first_line.split('Company Name')
            title = parts[0].strip()
            if len(parts) > 1:
                company_part = parts[1].strip()
                company = "Company Name"
        else:
            # Try to split by common separators
            separators = [' at ', ' - ', ' – ', ' | ']
            for sep in separators:
                if sep in first_line:
                    parts = first_line.split(sep, 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                    break
            
            if not title:
                title = first_line
        
        # Get description from remaining lines
        description_lines = lines[1:] if len(lines) > 1 else []
        description = " ".join(description_lines)
        description = re.sub(r'\s+', ' ', description)
        description = re.sub(r'[ï¼​â€"]', '', description)
        
        return {
            'title': title if title else 'Position',
            'company': company,
            'period': period,
            'description': description[:400] if description else 'Detailed responsibilities available in full CV.'
        }

    def parse_experience_by_lines(self, exp_section):
        """Parse experience by analyzing line structure"""
        lines = [line.strip() for line in exp_section.split('\n') if line.strip()]
        experiences = []
        
        current_job = {}
        
        for i, line in enumerate(lines):
            line = re.sub(r'[ï¼​â€"]', '', line)
            
            # Look for job title patterns
            if any(keyword in line.lower() for keyword in ['manager', 'director', 'assistant', 'coordinator', 'analyst', 'engineer', 'teacher', 'specialist', 'supervisor']):
                # Save previous job
                if current_job and 'title' in current_job:
                    experiences.append(current_job)
                
                # Start new job
                current_job = {
                    'title': line,
                    'company': 'Company Name',
                    'period': 'Period not specified',
                    'description': ''
                }
            
            # Look for company name
            elif 'Company Name' in line and current_job:
                current_job['company'] = line.replace('Company Name', 'Company').strip()
            
            # Look for dates
            elif re.search(r'\d{1,2}/\d{4}|\d{4}', line) and current_job:
                current_job['period'] = line
            
            # Add to description
            elif current_job and 'description' in current_job:
                if len(current_job['description']) < 300:
                    current_job['description'] += ' ' + line
        
        # Add last job
        if current_job and 'title' in current_job:
            experiences.append(current_job)
        
        return experiences

    def extract_education(self):
        """Extract education - robust parsing for multiple formats"""
        content = self.resume_data.get('extracted_text', '') or self.resume_data.get('content', '')
        
        if not content:
            return []
        
        education = []
        
        # Look for education section with multiple headers
        edu_headers = [
            r'(?i)education[:\s]*',
            r'(?i)education\s+and\s+training[:\s]*',
            r'(?i)academic\s+background[:\s]*',
            r'(?i)qualifications[:\s]*'
        ]
        
        edu_section = ""
        for header in edu_headers:
            pattern = header + r'\n+(.*?)(?=\n\s*(?:skills|certifications|accomplishments|interests|additional)\b|$)'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                edu_section = match.group(1)
                print(f"DEBUG - Found education section with header: {header}")
                break
        
        if not edu_section:
            print("DEBUG - No education section found")
            return []
        
        print(f"DEBUG - Education section preview: {edu_section[:300]}...")
        
        # Parse education entries
        lines = [line.strip() for line in edu_section.split('\n') if line.strip()]
        
        for line in lines:
            line = re.sub(r'[ï¼​â€"]', '', line)
            
            if len(line) < 5:
                continue
            
            # Multiple education patterns
            edu_patterns = [
                # "Bachelor of Science : Field University Year"
                r'(Bachelor|Master|PhD|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)[^:]*:\s*([^0-9]+?)\s+([^0-9]+(?:University|College|Institute)[^0-9]*)\s*(\d{4})?',
                
                # "Degree, Year Institution"
                r'(Bachelor|Master|PhD|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)[^,]*,\s*(\d{4})\s+([^,]+)',
                
                # "Education, Year"
                r'([A-Za-z\s]+),\s*(\d{4})\s*$',
                
                # "Degree Year Institution"
                r'(Bachelor|Master|PhD|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?).*?\s+(\d{4})\s+([A-Za-z\s]+(?:University|College|Institute))',
                
                # Simple "Institution Year"
                r'([A-Za-z\s]+(?:University|College|Institute))[^0-9]*(\d{4})'
            ]
            
            for pattern in edu_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 4:  # Full pattern
                        degree = match.group(1)
                        field = match.group(2).strip()
                        institution = match.group(3).strip()
                        year = match.group(4) if match.group(4) else 'Year not specified'
                    elif len(match.groups()) == 3:
                        degree = match.group(1)
                        field_or_year = match.group(2).strip()
                        institution_or_field = match.group(3).strip()
                        
                        # Determine which is which
                        if field_or_year.isdigit():
                            year = field_or_year
                            institution = institution_or_field
                            field = 'Field of Study'
                        else:
                            year = 'Year not specified'
                            field = field_or_year
                            institution = institution_or_field
                    elif len(match.groups()) == 2:
                        degree = 'Degree'
                        field = match.group(1).strip()
                        institution = 'Institution'
                        year = match.group(2)
                    
                    # Clean up values
                    degree = re.sub(r'[^\w\s]', '', degree).strip()
                    field = re.sub(r'[^\w\s]', '', field).strip()
                    institution = re.sub(r'[^\w\s]', '', institution).strip()
                    
                    education.append({
                        'degree': degree,
                        'field': field if field else 'Field of Study',
                        'institution': institution if institution else 'Institution',
                        'date': year
                    })
                    break
        
        print(f"DEBUG - Extracted {len(education)} education entries")
        return education

    def extract_overview(self):
        """Extract overview/summary - robust parsing for multiple formats"""
        content = self.resume_data.get('extracted_text', '') or self.resume_data.get('content', '')
        
        if not content:
            return "Professional summary will be extracted from the CV document once processed."
        
        # Look for summary sections with multiple headers
        summary_headers = [
            r'(?i)professional\s+summary[:\s]*',
            r'(?i)summary[:\s]*',
            r'(?i)profile[:\s]*',
            r'(?i)objective[:\s]*',
            r'(?i)overview[:\s]*',
            r'(?i)about[:\s]*'
        ]
        
        for header in summary_headers:
            pattern = header + r'\n+(.*?)(?=\n\s*(?:experience|skills|education|core\s+qualifications|highlights)\b)'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                summary = re.sub(r'\s+', ' ', summary)
                summary = re.sub(r'[ï¼​â€"]', '', summary)
                
                if len(summary) > 50:
                    return summary
        
        # Look for job title at the beginning
        lines = content.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 5 and (line.isupper() or any(keyword in line.lower() for keyword in ['manager', 'director', 'coordinator', 'assistant', 'engineer', 'teacher'])):
                return f"Position: {line}\n\nExperienced professional with demonstrated expertise in their field. Complete professional background and detailed experience are available in the full CV document."
        
        return "Experienced professional with demonstrated skills and accomplishments in their field. This candidate brings valuable expertise and a proven track record."
    def update_experience_display(self):
        """Update experience display with pagination"""
        # Clear existing layout safely
        self.clear_layout(self.exp_content_layout)

        experience_data = self.extract_experience()
        print(f"DEBUG - Experience data count: {len(experience_data)}")

        if not experience_data:
            # Placeholder
            exp_placeholder = QGroupBox()
            exp_placeholder.setMinimumHeight(200)
            exp_placeholder.setStyleSheet("""
                QGroupBox {
                    background-color: #1E4A42;
                    border-radius: 12px;
                    border: 2px solid #037F68;
                }
            """)
            placeholder_layout = QVBoxLayout(exp_placeholder)
            placeholder_layout.setAlignment(Qt.AlignCenter)
            
            placeholder_text = QLabel("Work experience details\nwill be extracted from CV")
            placeholder_text.setFont(QFont("Arial", 14))
            placeholder_text.setStyleSheet("color: white; text-align: center;")
            placeholder_text.setAlignment(Qt.AlignCenter)
            placeholder_layout.addWidget(placeholder_text)
            
            self.exp_content_layout.addWidget(exp_placeholder)
        else:
            # Calculate pagination
            start_idx = self.experience_page * self.items_per_page
            end_idx = start_idx + self.items_per_page
            current_experiences = experience_data[start_idx:end_idx]

            # Display experience entries
            for i, exp in enumerate(current_experiences):
                exp_card = QGroupBox()
                exp_card.setMinimumHeight(180)
                exp_card.setStyleSheet("""
                    QGroupBox {
                        background-color: #2A5A50;
                        border-radius: 10px;
                        border: 2px solid #037F68;
                        margin-bottom: 12px;
                    }
                """)
                exp_layout = QVBoxLayout(exp_card)
                exp_layout.setContentsMargins(18, 15, 18, 15)
                exp_layout.setSpacing(8)
                
                # Position title
                title = QLabel(exp.get('title', 'Position'))
                title.setFont(QFont("Arial", 15, QFont.Bold))
                title.setStyleSheet("color: white; font-weight: bold;")
                title.setWordWrap(True)

                # Company and period
                company_period = f"{exp.get('company', 'Company')} • {exp.get('period', 'Period not specified')}"
                company_period_label = QLabel(company_period)
                company_period_label.setFont(QFont("Arial", 12, QFont.Medium))
                company_period_label.setStyleSheet("color: #00FFC6; font-weight: bold; margin-bottom: 5px;")
                
                # Description
                desc_text = exp.get('description', '')
                if len(desc_text) > 300:
                    desc_text = desc_text[:300] + "..."
                elif not desc_text:
                    desc_text = 'Detailed responsibilities and achievements available in full CV.'
                
                desc = QLabel(desc_text)
                desc.setStyleSheet("font-size: 12px; color: white; line-height: 18px;")
                desc.setWordWrap(True)

                exp_layout.addWidget(title)
                exp_layout.addWidget(company_period_label)
                exp_layout.addWidget(desc)
                
                self.exp_content_layout.addWidget(exp_card)

            # Navigation for experience
            if len(experience_data) > self.items_per_page:
                nav_layout = QHBoxLayout()
                
                prev_btn = QPushButton("← Prev")
                prev_btn.setEnabled(self.experience_page > 0)
                prev_btn.setFixedSize(80, 30)
                prev_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #037F68;
                        color: white;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #2BBA91; }
                    QPushButton:disabled { background-color: #555555; color: #888888; }
                """)
                prev_btn.clicked.connect(lambda: self.change_experience_page(-1))
                
                total_pages = (len(experience_data) - 1) // self.items_per_page + 1
                page_info = QLabel(f"{self.experience_page + 1}/{total_pages}")
                page_info.setStyleSheet("color: #00FFC6; font-size: 11px;")
                page_info.setAlignment(Qt.AlignCenter)
                
                next_btn = QPushButton("Next →")
                next_btn.setEnabled(end_idx < len(experience_data))
                next_btn.setFixedSize(80, 30)
                next_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #037F68;
                        color: white;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #2BBA91; }
                    QPushButton:disabled { background-color: #555555; color: #888888; }
                """)
                next_btn.clicked.connect(lambda: self.change_experience_page(1))
                
                nav_layout.addWidget(prev_btn)
                nav_layout.addStretch()
                nav_layout.addWidget(page_info)
                nav_layout.addStretch()
                nav_layout.addWidget(next_btn)
                
                self.exp_content_layout.addLayout(nav_layout)

    def update_education_display(self):
        """Update education display with better formatting"""
        # Clear existing layout safely
        self.clear_layout(self.edu_content_layout)

        education_data = self.extract_education()
        print(f"DEBUG - Education data count: {len(education_data)}")

        if not education_data:
            # Placeholder
            edu_placeholder = QGroupBox()
            edu_placeholder.setMinimumHeight(200)
            edu_placeholder.setStyleSheet("""
                QGroupBox {
                    background-color: #1E4A42;
                    border-radius: 12px;
                    border: 2px solid #037F68;
                }
            """)
            placeholder_layout = QVBoxLayout(edu_placeholder)
            placeholder_layout.setAlignment(Qt.AlignCenter)
            
            placeholder_text = QLabel("Education details\nwill be extracted from CV")
            placeholder_text.setFont(QFont("Arial", 14))
            placeholder_text.setStyleSheet("color: white; text-align: center;")
            placeholder_text.setAlignment(Qt.AlignCenter)
            placeholder_layout.addWidget(placeholder_text)
            
            self.edu_content_layout.addWidget(edu_placeholder)
        else:
            # Calculate pagination
            start_idx = self.education_page * self.items_per_page
            end_idx = start_idx + self.items_per_page
            current_education = education_data[start_idx:end_idx]

            # Display education entries
            for i, edu in enumerate(current_education):
                edu_card = QGroupBox()
                edu_card.setMinimumHeight(120)
                edu_card.setStyleSheet("""
                    QGroupBox {
                        background-color: #1E4A42;
                        border-radius: 10px;
                        border: 2px solid #037F68;
                        margin-bottom: 12px;
                    }
                """)
                edu_layout = QVBoxLayout(edu_card)
                edu_layout.setContentsMargins(18, 15, 18, 15)
                edu_layout.setSpacing(8)
                
                # Degree with field
                degree_text = edu.get('degree', 'Degree')
                if edu.get('field', '') and edu.get('field', '').strip():
                    degree_text += f" in {edu.get('field', '')}"
                
                degree_label = QLabel(degree_text)
                degree_label.setFont(QFont("Arial", 14, QFont.Bold))
                degree_label.setStyleSheet("color: white; font-weight: bold;")
                degree_label.setWordWrap(True)
                
                # Institution and Year
                institution_text = edu.get('institution', 'Institution')
                if edu.get('date', '') and edu.get('date', '') != 'Year not specified':
                    institution_text += f" • {edu.get('date', '')}"
                
                info_label = QLabel(institution_text)
                info_label.setFont(QFont("Arial", 12))
                info_label.setStyleSheet("color: #00FFC6; font-weight: 500;")
                info_label.setWordWrap(True)
                
                edu_layout.addWidget(degree_label)
                edu_layout.addWidget(info_label)
                
                self.edu_content_layout.addWidget(edu_card)

            # Navigation for education
            if len(education_data) > self.items_per_page:
                nav_layout = QHBoxLayout()
                
                prev_btn = QPushButton("← Prev")
                prev_btn.setEnabled(self.education_page > 0)
                prev_btn.setFixedSize(80, 30)
                prev_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #037F68;
                        color: white;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #2BBA91; }
                    QPushButton:disabled { background-color: #555555; color: #888888; }
                """)
                prev_btn.clicked.connect(lambda: self.change_education_page(-1))
                
                total_pages = (len(education_data) - 1) // self.items_per_page + 1
                page_info = QLabel(f"{self.education_page + 1}/{total_pages}")
                page_info.setStyleSheet("color: #00FFC6; font-size: 11px;")
                page_info.setAlignment(Qt.AlignCenter)
                
                next_btn = QPushButton("Next →")
                next_btn.setEnabled(end_idx < len(education_data))
                next_btn.setFixedSize(80, 30)
                next_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #037F68;
                        color: white;
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background-color: #2BBA91; }
                    QPushButton:disabled { background-color: #555555; color: #888888; }
                """)
                next_btn.clicked.connect(lambda: self.change_education_page(1))
                
                nav_layout.addWidget(prev_btn)
                nav_layout.addStretch()
                nav_layout.addWidget(page_info)
                nav_layout.addStretch()
                nav_layout.addWidget(next_btn)
                
                self.edu_content_layout.addLayout(nav_layout)

    def extract_overview(self):
        """Extract overview/summary - improved for debugging"""
        content = self.resume_data.get('extracted_text', '') or self.resume_data.get('content', '')
        
        if not content:
            return "Professional summary will be extracted from the CV document once processed."
        
        print(f"DEBUG - Overview content length: {len(content)}")
        print(f"DEBUG - Overview content preview: {content[:300]}...")
        
        # Look for Professional Summary section
        summary_patterns = [
            r'(?i)professional\s+summary[:\s]*\n+(.*?)(?=\n\s*(?:experience|accomplishments|education|skills)\b)',
            r'(?i)summary[:\s]*\n+(.*?)(?=\n\s*(?:experience|accomplishments|education|skills)\b)',
            r'(?i)profile[:\s]*\n+(.*?)(?=\n\s*(?:experience|accomplishments|education|skills)\b)',
            r'(?i)objective[:\s]*\n+(.*?)(?=\n\s*(?:experience|accomplishments|education|skills)\b)'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                summary = match.group(1).strip()
                # Clean up the text
                summary = re.sub(r'\s+', ' ', summary)
                summary = re.sub(r'[^\w\s.,;:()/-]', '', summary)  # Remove weird characters
                print(f"DEBUG - Found summary with pattern: {pattern}")
                print(f"DEBUG - Summary length: {len(summary)}")
                if len(summary) > 50:
                    return summary
        
        # Look for job title at the beginning
        lines = content.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 5 and line.isupper():  # Job titles are often in CAPS
                print(f"DEBUG - Found job title: {line}")
                return f"Position: {line}\n\nExperienced professional with demonstrated expertise in their field. Complete professional background and detailed experience are available in the full CV document."
        
        return "Experienced professional with demonstrated skills and accomplishments in their field. This candidate brings valuable expertise and a proven track record."
    

    def go_back(self):
        """Go back to previous window"""
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SummaryPage()
    window.show()
    sys.exit(app.exec_())