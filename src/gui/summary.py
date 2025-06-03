import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QGroupBox, QGridLayout, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSize

class SummaryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Summary Page")
        self.setFixedSize(1280, 720)
        self.setStyleSheet("background-color: #0B1917; color: white;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        layout = QVBoxLayout(container)

        # Header
        header = QHBoxLayout()
        back = QLabel("<")
        back.setFont(QFont("Arial", 24))
        back.setStyleSheet("color: white;")
        header.addWidget(back)
        header.addStretch()
        layout.addLayout(header)

        name = QLabel("Raka Daffa Iftikhaar")
        name.setFont(QFont("Arial", 48, QFont.Bold))
        name.setStyleSheet("color: #00FFC6;")
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)

        # Personal Info + Skills
        top = QHBoxLayout()

        # Personal Info
        info_card = QGroupBox()
        info_card.setFixedSize(530, 260)
        info_card.setStyleSheet("background-color: #037F68; border-radius: 12px;")
        info_layout = QVBoxLayout()

        # Birthdate
        birth_title = QLabel("Birthdate")
        birth_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        birth_value = QLabel("05-19-2025")
        birth_value.setStyleSheet("color: white; font-size: 20px; margin-bottom: 12px;")

        # Address
        address_title = QLabel("Address")
        address_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        address_value = QLabel("Mesjid Salman ITB")
        address_value.setStyleSheet("color: white; font-size: 20px; margin-bottom: 12px;")

        # Phone
        phone_title = QLabel("Phone")
        phone_title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        phone_value = QLabel("+62810312319402")
        phone_value.setStyleSheet("color: white; font-size: 20px;")

        # Tambahkan ke layout
        info_layout.addWidget(birth_title)
        info_layout.addWidget(birth_value)
        info_layout.addWidget(address_title)
        info_layout.addWidget(address_value)
        info_layout.addWidget(phone_title)
        info_layout.addWidget(phone_value)

        info_card.setLayout(info_layout)
        top.addWidget(info_card)

        # Skills (judul terpisah di tengah)
        skills_layout_wrapper = QVBoxLayout()
        skills_title = QLabel("Skills")
        skills_title.setStyleSheet("color: white; font-weight: bold; font-size: 24px;")
        skills_title.setAlignment(Qt.AlignCenter)
        skills_layout_wrapper.addWidget(skills_title)

        # Sample skills data (replace with your actual skills list)
        all_skills = ["HTML", "CSS", "JavaScript", "Python", "React", "Node.js", "SQL", "Git", "Docker", "AWS", "MongoDB", "Vue.js"]
        skills_per_page = 9
        self.current_page = 0  # Use self to make it accessible
        total_pages = (len(all_skills) + skills_per_page - 1) // skills_per_page

        # Skills grid container
        skills_container = QWidget()
        skills_grid = QGridLayout()
        skills_container.setLayout(skills_grid)

        def update_skills_display():
            # Clear existing skills
            for i in reversed(range(skills_grid.count())):
                skills_grid.itemAt(i).widget().setParent(None)
            
            # Display current page skills
            start_idx = self.current_page * skills_per_page
            end_idx = min(start_idx + skills_per_page, len(all_skills))
            
            for i in range(start_idx, end_idx):
                skill = QPushButton(all_skills[i])
                skill.setFixedSize(160, 35)
                skill.setStyleSheet("""
                    QPushButton {
                        background-color: #037F68;
                        color: white;
                        border-radius: 6px;
                        font-size: 16px;
                    }
                """)
                row = (i - start_idx) // 3
                col = (i - start_idx) % 3
                skills_grid.addWidget(skill, row, col)

        skills_layout_wrapper.addWidget(skills_container)

        # Pagination controls
        if total_pages > 1:
            pagination_layout = QHBoxLayout()
            
            prev_btn = QPushButton("◀")
            prev_btn.setFixedSize(30, 30)
            prev_btn.setStyleSheet("background-color: #037F68; color: white; border-radius: 15px; font-size: 16px;")
            prev_btn.clicked.connect(lambda: prev_page())
            
            page_label = QLabel(f"Page {self.current_page + 1} of {total_pages}")
            page_label.setStyleSheet("color: white; font-size: 14px; margin: 0 10px;")
            page_label.setAlignment(Qt.AlignCenter)
            
            next_btn = QPushButton("▶")
            next_btn.setFixedSize(30, 30)
            next_btn.setStyleSheet("background-color: #037F68; color: white; border-radius: 15px; font-size: 16px;")
            next_btn.clicked.connect(lambda: next_page())
            
            pagination_layout.addStretch()
            pagination_layout.addWidget(prev_btn)
            pagination_layout.addWidget(page_label)
            pagination_layout.addWidget(next_btn)
            pagination_layout.addStretch()
            
            skills_layout_wrapper.addLayout(pagination_layout)

        def prev_page():
            if self.current_page > 0:
                self.current_page -= 1
                update_skills_display()
                page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
                prev_btn.setEnabled(self.current_page > 0)
                next_btn.setEnabled(self.current_page < total_pages - 1)

        def next_page():
            if self.current_page < total_pages - 1:
                self.current_page += 1
                update_skills_display()
                page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
                prev_btn.setEnabled(self.current_page > 0)
                next_btn.setEnabled(self.current_page < total_pages - 1)

        # Initial display
        update_skills_display()
        if total_pages > 1:
            prev_btn.setEnabled(False)
            next_btn.setEnabled(total_pages > 1)

        skills_group = QGroupBox()
        skills_group.setStyleSheet("border: none;")
        skills_group.setFixedWidth(640)
        skills_group.setLayout(skills_layout_wrapper)

        top.addWidget(skills_group)
        layout.addLayout(top)

        # Job History
        layout.addSpacing(20)
        job_label = QLabel("Job History")
        job_label.setFont(QFont("Arial", 24, QFont.Bold))
        job_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(job_label)

        job_layout = QGridLayout()
        for i in range(4):
            job = QGroupBox()
            job.setFixedSize(530, 130)
            job.setStyleSheet("background-color: #B9DCD2; border-radius: 8px; color: #051010;")
            inner = QVBoxLayout()
            inner.setSpacing(0)
            title = QLabel("CTO")
            title.setFont(QFont("Arial", 24, QFont.Bold))

            year = QLabel("2013 - 2015")
            year.setFont(QFont("Arial", 20, QFont.Medium))
            desc = QLabel()
            desc.setText("Leading the organization's technology strategies and lead everything")
            desc.setStyleSheet("font-size: 16px;")

            inner.addWidget(title)
            inner.addWidget(year)
            inner.addWidget(desc)
            job.setLayout(inner)
            job_layout.addWidget(job, i // 2, i % 2)

        layout.addLayout(job_layout)

        # Education Title
        layout.addSpacing(20)
        edu_label = QLabel("Education")
        edu_label.setFont(QFont("Arial", 24, QFont.Bold))
        edu_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(edu_label)

        # Education Layout
        for i in range(3):
            edu = QGroupBox()
            edu.setFixedSize(896, 75)
            edu.setStyleSheet("background-color: #037F68; border-radius: 8px;")
            inner = QVBoxLayout()
            school = QLabel("Informatics Engineering (Institut Teknologi Bandung)")
            school.setFont(QFont("Arial", 20, QFont.Bold))
            year = QLabel("2013 - 2015")
            year.setFont(QFont("Arial", 20, QFont.Medium))
            for c in [school, year]:
                c.setStyleSheet("color: white;")
                inner.addWidget(c)
            edu.setLayout(inner)
            layout.addWidget(edu, alignment=Qt.AlignCenter)

        layout.addStretch()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SummaryPage()
    window.show()
    sys.exit(app.exec_())
