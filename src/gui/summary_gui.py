import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QGroupBox, QGridLayout, QSizePolicy, QMessageBox
)
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, QSize

class SummaryPage(QWidget):
    def __init__(self, resume_data=None):
        super().__init__()
        self.resume_data = resume_data or {}
        self.setWindowTitle("CV Summary")
        self.setFixedSize(1280, 720)
        self.setStyleSheet("background-color: #0B1917; color: white;")
        self.init_ui()

    def init_ui(self): 
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header with back button
        self.create_header(layout)
        
        # Candidate name
        self.create_candidate_name(layout)
        
        # Personal Info + Skills section
        self.create_info_skills_section(layout)
        
        # Overview/Summary section
        self.create_overview_section(layout)
        
        # Experience section
        self.create_experience_section(layout)
        
        # Education section
        self.create_education_section(layout)
        
        layout.addStretch()

    def create_header(self, layout):
        """Create header with back button"""
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(100, 40)
        back_btn.setFont(QFont("Arial", 14))
        back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #037F68;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2BBA91;
            }
        """)
        back_btn.clicked.connect(self.go_back)
        
        header.addWidget(back_btn)
        header.addStretch()
        layout.addLayout(header)

    def create_candidate_name(self, layout):
        """Create candidate name display"""
        name_text = self.resume_data.get('name', 'Unknown Candidate')
        if name_text.endswith('.pdf'):
            name_text = name_text[:-4]  # Remove .pdf extension
        
        name = QLabel(name_text)
        name.setFont(QFont("Arial", 48, QFont.Bold))
        name.setStyleSheet("color: #00FFC6; margin-bottom: 20px;")
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)

    def create_info_skills_section(self, layout):
        """Create personal info and skills section"""
        top = QHBoxLayout()
        top.setSpacing(40)

        # Personal Info Card
        info_card = self.create_personal_info_card()
        top.addWidget(info_card)

        # Skills Card
        skills_card = self.create_skills_card()
        top.addWidget(skills_card)

        layout.addLayout(top)

    def create_personal_info_card(self):
        """Create personal information card"""
        info_card = QGroupBox()
        info_card.setFixedSize(530, 300)
        info_card.setStyleSheet("background-color: #037F68; border-radius: 12px;")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(15)
        info_layout.setContentsMargins(25, 25, 25, 25)

        # Title
        title = QLabel("Personal Information")
        title.setStyleSheet("color: #00FFC6; font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        info_layout.addWidget(title)

        # Extract personal info from resume data
        personal_info = self.extract_personal_info()
        
        for label, value in personal_info:
            label_widget = QLabel(label)
            label_widget.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
            
            value_widget = QLabel(value)
            value_widget.setStyleSheet("color: #E0E0E0; font-size: 14px; margin-bottom: 8px;")
            value_widget.setWordWrap(True)
            
            info_layout.addWidget(label_widget)
            info_layout.addWidget(value_widget)

        info_layout.addStretch()
        info_card.setLayout(info_layout)
        return info_card

    def create_skills_card(self):
        """Create skills card with pagination"""
        skills_group = QGroupBox()
        skills_group.setStyleSheet("border: none;")
        skills_group.setFixedWidth(640)
        
        skills_layout_wrapper = QVBoxLayout()
        
        # Title
        skills_title = QLabel("Skills")
        skills_title.setStyleSheet("color: #00FFC6; font-weight: bold; font-size: 20px; margin-bottom: 15px;")
        skills_title.setAlignment(Qt.AlignCenter)
        skills_layout_wrapper.addWidget(skills_title)

        # Get skills data
        skills_from_db = self.resume_data.get('skills', [])
        if isinstance(skills_from_db, str):
            all_skills = [s.strip() for s in skills_from_db.split(',') if s.strip()]
        else:
            all_skills = skills_from_db if skills_from_db else ["No skills data available"]
        
        if not all_skills:
            all_skills = ["No skills information available"]

        skills_per_page = 9
        self.current_skill_page = 0
        total_pages = max(1, (len(all_skills) + skills_per_page - 1) // skills_per_page)

        # Skills grid container
        skills_container = QWidget()
        skills_grid = QGridLayout()
        skills_container.setLayout(skills_grid)

        def update_skills_display():
            # Clear existing skills
            for i in reversed(range(skills_grid.count())):
                skills_grid.itemAt(i).widget().setParent(None)
            
            # Display current page skills
            start_idx = self.current_skill_page * skills_per_page
            end_idx = min(start_idx + skills_per_page, len(all_skills))
            
            for i in range(start_idx, end_idx):
                skill = QPushButton(all_skills[i])
                skill.setFixedSize(180, 35)
                skill.setStyleSheet("""
                    QPushButton {
                        background-color: #037F68;
                        color: white;
                        border-radius: 6px;
                        font-size: 14px;
                        border: 1px solid #2BBA91;
                    }
                    QPushButton:hover {
                        background-color: #2BBA91;
                    }
                """)
                row = (i - start_idx) // 3
                col = (i - start_idx) % 3
                skills_grid.addWidget(skill, row, col)

        skills_layout_wrapper.addWidget(skills_container)

        # Pagination controls (only if more than one page)
        if total_pages > 1:
            pagination_layout = QHBoxLayout()
            
            prev_btn = QPushButton("◀")
            prev_btn.setFixedSize(30, 30)
            prev_btn.setStyleSheet("background-color: #037F68; color: white; border-radius: 15px; font-size: 16px;")
            
            page_label = QLabel(f"Page {self.current_skill_page + 1} of {total_pages}")
            page_label.setStyleSheet("color: white; font-size: 14px; margin: 0 10px;")
            page_label.setAlignment(Qt.AlignCenter)
            
            next_btn = QPushButton("▶")
            next_btn.setFixedSize(30, 30)
            next_btn.setStyleSheet("background-color: #037F68; color: white; border-radius: 15px; font-size: 16px;")
            
            def prev_page():
                if self.current_skill_page > 0:
                    self.current_skill_page -= 1
                    update_skills_display()
                    page_label.setText(f"Page {self.current_skill_page + 1} of {total_pages}")
                    prev_btn.setEnabled(self.current_skill_page > 0)
                    next_btn.setEnabled(self.current_skill_page < total_pages - 1)

            def next_page():
                if self.current_skill_page < total_pages - 1:
                    self.current_skill_page += 1
                    update_skills_display()
                    page_label.setText(f"Page {self.current_skill_page + 1} of {total_pages}")
                    prev_btn.setEnabled(self.current_skill_page > 0)
                    next_btn.setEnabled(self.current_skill_page < total_pages - 1)

            prev_btn.clicked.connect(prev_page)
            next_btn.clicked.connect(next_page)
            
            pagination_layout.addStretch()
            pagination_layout.addWidget(prev_btn)
            pagination_layout.addWidget(page_label)
            pagination_layout.addWidget(next_btn)
            pagination_layout.addStretch()
            
            skills_layout_wrapper.addLayout(pagination_layout)

        # Initial display
        update_skills_display()
        if total_pages > 1:
            prev_btn.setEnabled(False)
            next_btn.setEnabled(total_pages > 1)

        skills_group.setLayout(skills_layout_wrapper)
        return skills_group

    def create_overview_section(self, layout):
        """Create overview/summary section"""
        overview_data = self.extract_overview()
        if not overview_data or overview_data.strip() == "":
            # Show a default overview section even if no data
            overview_data = "Overview information will be displayed here once extracted from the CV."
            
        overview_label = QLabel("Overview")
        overview_label.setFont(QFont("Arial", 24, QFont.Bold))
        overview_label.setStyleSheet("color: #00FFC6; margin-top: 20px;")
        overview_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(overview_label)

        overview_card = QGroupBox()
        overview_card.setStyleSheet("background-color: #037F68; border-radius: 12px; padding: 20px;")
        overview_layout = QVBoxLayout()
        overview_layout.setContentsMargins(25, 25, 25, 25)

        overview_text = QLabel(overview_data)
        overview_text.setStyleSheet("color: white; font-size: 14px; line-height: 1.5;")
        overview_text.setWordWrap(True)
        overview_layout.addWidget(overview_text)

        overview_card.setLayout(overview_layout)
        layout.addWidget(overview_card)

    def create_experience_section(self, layout):
        """Create work experience section"""
        experience_data = self.extract_experience()
        
        layout.addSpacing(20)
        job_label = QLabel("Work Experience")
        job_label.setFont(QFont("Arial", 24, QFont.Bold))
        job_label.setStyleSheet("color: #00FFC6;")
        job_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(job_label)

        if not experience_data:
            # Show placeholder if no experience data
            job_placeholder = QGroupBox()
            job_placeholder.setFixedSize(896, 100)
            job_placeholder.setStyleSheet("background-color: #037F68; border-radius: 8px; margin-bottom: 10px;")
            inner = QVBoxLayout()
            inner.setContentsMargins(20, 20, 20, 20)
            
            placeholder_text = QLabel("Work experience information will be displayed here once extracted from the CV.")
            placeholder_text.setFont(QFont("Arial", 14))
            placeholder_text.setStyleSheet("color: #E0E0E0; text-align: center;")
            placeholder_text.setWordWrap(True)
            placeholder_text.setAlignment(Qt.AlignCenter)
            
            inner.addWidget(placeholder_text)
            job_placeholder.setLayout(inner)
            layout.addWidget(job_placeholder, alignment=Qt.AlignCenter)
            return

        job_layout = QGridLayout()
        job_layout.setSpacing(15)
        
        for i, exp in enumerate(experience_data[:6]):  # Limit to 6 entries
            job = QGroupBox()
            job.setFixedSize(530, 130)
            job.setStyleSheet("background-color: #B9DCD2; border-radius: 8px; color: #051010;")
            inner = QVBoxLayout()
            inner.setSpacing(5)
            inner.setContentsMargins(15, 15, 15, 15)
            
            title = QLabel(exp.get('title', 'Position Not Specified'))
            title.setFont(QFont("Arial", 18, QFont.Bold))
            title.setStyleSheet("color: #051010;")

            period = QLabel(f"{exp.get('start', 'N/A')} - {exp.get('end', 'N/A')}")
            period.setFont(QFont("Arial", 14, QFont.Medium))
            period.setStyleSheet("color: #2C5530;")
            
            desc = QLabel(exp.get('description', 'No description available')[:100] + "..." if len(exp.get('description', '')) > 100 else exp.get('description', 'No description available'))
            desc.setStyleSheet("font-size: 12px; color: #051010;")
            desc.setWordWrap(True)

            inner.addWidget(title)
            inner.addWidget(period)
            inner.addWidget(desc)
            job.setLayout(inner)
            job_layout.addWidget(job, i // 2, i % 2)

        layout.addLayout(job_layout)

    def create_education_section(self, layout):
        """Create education section"""
        education_data = self.extract_education()

        layout.addSpacing(20)
        edu_label = QLabel("Education")
        edu_label.setFont(QFont("Arial", 24, QFont.Bold))
        edu_label.setStyleSheet("color: #00FFC6;")
        edu_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(edu_label)

        if not education_data:
            # Show placeholder if no education data
            edu_placeholder = QGroupBox()
            edu_placeholder.setFixedSize(896, 80)
            edu_placeholder.setStyleSheet("background-color: #037F68; border-radius: 8px; margin-bottom: 10px;")
            inner = QVBoxLayout()
            inner.setContentsMargins(20, 15, 20, 15)
            
            placeholder_text = QLabel("Education information will be displayed here once extracted from the CV.")
            placeholder_text.setFont(QFont("Arial", 14))
            placeholder_text.setStyleSheet("color: #E0E0E0; text-align: center;")
            placeholder_text.setWordWrap(True)
            placeholder_text.setAlignment(Qt.AlignCenter)
            
            inner.addWidget(placeholder_text)
            edu_placeholder.setLayout(inner)
            layout.addWidget(edu_placeholder, alignment=Qt.AlignCenter)
            return

        for i, edu in enumerate(education_data[:5]):  # Limit to 5 entries
            edu_card = QGroupBox()
            edu_card.setFixedSize(896, 80)
            edu_card.setStyleSheet("background-color: #037F68; border-radius: 8px; margin-bottom: 10px;")
            inner = QVBoxLayout()
            inner.setContentsMargins(20, 15, 20, 15)
            inner.setSpacing(5)
            
            degree_field = f"{edu.get('degree', 'Degree')} in {edu.get('field', 'Field of Study')}"
            school = QLabel(degree_field)
            school.setFont(QFont("Arial", 16, QFont.Bold))
            school.setStyleSheet("color: white;")
            
            date_info = edu.get('date', 'Date not specified')
            if not date_info or date_info == '':
                date_info = "Date not specified"
            
            year = QLabel(date_info)
            year.setFont(QFont("Arial", 14, QFont.Medium))
            year.setStyleSheet("color: #E0E0E0;")
            
            # Add GPA if available
            if self.resume_data.get('gpa'):
                gpa_text = f"GPA: {self.resume_data['gpa']}"
                gpa_label = QLabel(gpa_text)
                gpa_label.setFont(QFont("Arial", 12))
                gpa_label.setStyleSheet("color: #00FFC6;")
                inner.addWidget(gpa_label)
            
            inner.addWidget(school)
            inner.addWidget(year)
            edu_card.setLayout(inner)
            layout.addWidget(edu_card, alignment=Qt.AlignCenter)

    def extract_personal_info(self):
        """Extract personal information from resume data"""
        info = []
        
        # Add available information from database
        if self.resume_data.get('file_path'):
            file_name = os.path.basename(self.resume_data['file_path'])
            info.append(("File Name:", file_name))
        
        # Add category from database if available
        if hasattr(self, 'resume_data') and 'category' in self.resume_data:
            info.append(("Category:", self.resume_data['category']))
        
        # Add certifications if available
        if self.resume_data.get('certifications') and self.resume_data['certifications'].strip():
            cert_text = self.resume_data['certifications']
            if len(cert_text) > 100:
                cert_text = cert_text[:100] + "..."
            info.append(("Certifications:", cert_text))
        
        # Add GPA if available
        if self.resume_data.get('gpa'):
            info.append(("GPA:", str(self.resume_data['gpa'])))
        
        # Extract contact info from text if available
        if self.resume_data.get('extracted_text'):
            contact_info = self.extract_contact_from_text(self.resume_data['extracted_text'])
            info.extend(contact_info)
        
        # Add placeholder info if no contact info found
        if not any('contact' in key.lower() or 'phone' in key.lower() or 'email' in key.lower() 
                  for key, _ in info):
            info.extend([
                ("Contact:", "Available in full CV"),
                ("Location:", "Available in full CV")
            ])
        
        return info

    def extract_contact_from_text(self, text):
        """Extract contact information from CV text using regex"""
        contact_info = []
        
        import re
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info.append(("Email:", emails[0]))
        
        # Extract phone numbers
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
            r'\b\(\d{3}\)\s?\d{3}[-.]?\d{4}\b',  # (123) 456-7890
            r'\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'  # International
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                contact_info.append(("Phone:", phones[0]))
                break
        
        return contact_info

    def extract_overview(self):
        """Extract overview/summary from resume data"""
        if not self.resume_data.get('extracted_text'):
            return ""
            
        text = self.resume_data['extracted_text']
        import re
        
        # Look for common summary section headers
        summary_patterns = [
            r"(?i)(PROFILE|SUMMARY|OVERVIEW|ABOUT ME|OBJECTIVE|PROFESSIONAL SUMMARY)[:\s]*\n+(.*?)(?=\n\s*[A-Z]{2,}|\Z)",
            r"(?i)(CAREER OBJECTIVE|PERSONAL STATEMENT)[:\s]*\n+(.*?)(?=\n\s*[A-Z]{2,}|\Z)"
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match and len(match.groups()) >= 2:
                summary = match.group(2).strip()
                # Clean up the summary
                summary = re.sub(r'\n+', ' ', summary)  # Replace multiple newlines with space
                summary = re.sub(r'\s+', ' ', summary)  # Replace multiple spaces with single space
                
                if len(summary) > 50:  # Only return if substantial content
                    return summary[:500] + "..." if len(summary) > 500 else summary
        
        return ""

    def extract_experience(self):
        """Extract work experience from resume data"""
        experiences = []
        
        # First try to get from structured database field
        if self.resume_data.get('experience') and self.resume_data['experience'].strip():
            exp_text = self.resume_data['experience']
            # Parse experience text - handle various formats
            exp_entries = exp_text.split(' | ')
            
            for entry in exp_entries:
                if entry.strip():
                    import re
                    # Try to parse format: "Title (Start - End)" or "Title at Company (Start - End)"
                    match = re.match(r'(.*?)\s*(?:at\s+.*?)?\s*\((.*?)\s*-\s*(.*?)\)', entry.strip())
                    if match:
                        experiences.append({
                            'title': match.group(1).strip(),
                            'start': match.group(2).strip(), 
                            'end': match.group(3).strip(),
                            'description': 'Details available in full CV'
                        })
                    else:
                        # Fallback - just use the text as title
                        experiences.append({
                            'title': entry.strip(),
                            'start': 'N/A',
                            'end': 'N/A', 
                            'description': 'Details available in full CV'
                        })
        
        # If no structured data, try to extract from CV text
        if not experiences and self.resume_data.get('extracted_text'):
            text = self.resume_data['extracted_text']
            import re
            
            # Look for experience section
            exp_section_pattern = r'(?i)(EXPERIENCE|EMPLOYMENT|WORK HISTORY)[:\s]*\n+(.*?)(?=\n\s*[A-Z]{2,}|\Z)'
            exp_match = re.search(exp_section_pattern, text, re.DOTALL)
            
            if exp_match:
                exp_section = exp_match.group(2)
                
                # Look for job entries with dates
                job_patterns = [
                    r'([A-Z][^\n]*(?:Engineer|Manager|Developer|Analyst|Consultant|Director|Specialist|Coordinator|Assistant)[^\n]*)\s*\n.*?(\d{4})\s*[-–]\s*(\d{4}|present|current)',
                    r'([A-Z][^\n]*)\s*\n.*?(\d{4})\s*[-–]\s*(\d{4}|present|current)'
                ]
                
                for pattern in job_patterns:
                    matches = re.finditer(pattern, exp_section, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        experiences.append({
                            'title': match.group(1).strip(),
                            'start': match.group(2),
                            'end': match.group(3),
                            'description': 'Details available in full CV'
                        })
                        if len(experiences) >= 6:  # Limit entries
                            break
                    
                    if experiences:
                        break
        
        return experiences

    def extract_education(self):
        """Extract education information from resume data"""
        education = []
        
        # First try to get from structured database field
        if self.resume_data.get('education') and self.resume_data['education'].strip():
            edu_text = self.resume_data['education']
            # Parse education text - handle various formats
            edu_entries = edu_text.split(' | ')
            
            for entry in edu_entries:
                if entry.strip():
                    import re
                    # Try to parse format: "Degree in Field" or "Degree, Field"
                    patterns = [
                        r'(.*?)\s+in\s+(.*)',
                        r'(.*?),\s*(.*)',
                        r'(Bachelor|Master|PhD|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)\s*(.*)'
                    ]
                    
                    for pattern in patterns:
                        match = re.match(pattern, entry.strip(), re.IGNORECASE)
                        if match:
                            education.append({
                                'degree': match.group(1).strip(),
                                'field': match.group(2).strip() if len(match.groups()) > 1 else 'Field of Study',
                                'date': 'Date available in full CV'
                            })
                            break
                    else:
                        # Fallback - use entire entry as degree
                        education.append({
                            'degree': entry.strip(),
                            'field': 'Field of Study',
                            'date': 'Date available in full CV'
                        })
        
        # If no structured data, try to extract from CV text
        if not education and self.resume_data.get('extracted_text'):
            text = self.resume_data['extracted_text']
            import re
            
            # Look for education section
            edu_section_pattern = r'(?i)(EDUCATION|ACADEMIC)[:\s]*\n+(.*?)(?=\n\s*[A-Z]{2,}|\Z)'
            edu_match = re.search(edu_section_pattern, text, re.DOTALL)
            
            if edu_match:
                edu_section = edu_match.group(2)
                
                # Look for degree patterns
                degree_patterns = [
                    r'(Bachelor|Master|PhD|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)\s*(?:of|in|degree)?\s*([^,\n]*)',
                    r'(Associate|Diploma)\s+(?:of|in)?\s*([^,\n]*)'
                ]
                
                for pattern in degree_patterns:
                    matches = re.finditer(pattern, edu_section, re.IGNORECASE)
                    for match in matches:
                        education.append({
                            'degree': match.group(1).strip(),
                            'field': match.group(2).strip() if match.group(2).strip() else 'Field of Study',
                            'date': 'Date available in full CV'
                        })
                        if len(education) >= 5:  # Limit entries
                            break
                    
                    if education:
                        break
        
        return education

    def go_back(self):
        """Go back to previous window"""
        self.close()
        # You can add navigation logic here to return to the search results

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Sample data for testing
    sample_data = {
        'name': 'John Doe',
        'skills': 'Python, Java, Machine Learning, Data Analysis, SQL, Git, Docker',
        'experience': 'Software Engineer at Tech Corp (2020 - 2023) | Data Analyst at Data Inc (2018 - 2020)',
        'education': 'Bachelor in Computer Science | Master in Data Science',
        'gpa': '3.8',
        'certifications': 'AWS Certified Developer, Google Cloud Professional',
        'category': 'Engineering',
        'file_path': '/path/to/john_doe.pdf',
        'extracted_text': '''
        PROFILE
        Experienced software engineer with strong background in machine learning and data analysis.
        
        EXPERIENCE
        Software Engineer at Tech Corp
        2020 - 2023
        Developed machine learning models and data pipelines.
        
        Data Analyst at Data Inc
        2018 - 2020
        Analyzed large datasets and created reports.
        
        EDUCATION
        Master of Science in Data Science
        University of Technology, 2018
        
        Bachelor of Science in Computer Science  
        State University, 2016
        '''
    }
    
    window = SummaryPage(sample_data)
    window.show()
    sys.exit(app.exec_())