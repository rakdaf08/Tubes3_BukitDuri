import fitz
import re
import os


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()

        # Buat base path untuk file output
        base_path = os.path.splitext(pdf_path)[0]

        # Simpan versi untuk regex (format normal)
        regex_path = f"{base_path}_regex.txt"
        with open(regex_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Simpan versi untuk string matching (single line)
        string_path = f"{base_path}_string.txt"
        # Bersihkan text: hapus multiple spaces dan newlines
        clean_text = " ".join(text.split())
        with open(string_path, "w", encoding="utf-8") as f:
            f.write(clean_text)

        print(f"[INFO] Berhasil menyimpan file regex: {regex_path}")
        print(f"[INFO] Berhasil menyimpan file string matching: {string_path}")

    except Exception as e:
        print(f"[ERROR] Gagal membaca PDF {pdf_path}: {e}")
    return text


def extract_profile_data(text: str) -> dict:
    # Inisialisasi hasil default
    profile = {
        "name": None,
        "email": None,
        "phone": None,
        "overview": None,
        "skills": [],
        "experience": [],
        "education": [],
    }

    # Email - Pattern yang lebih ketat
    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
    )
    if email_match:
        profile["email"] = email_match.group()

    # Nomor telepon - Pattern yang lebih fleksibel
    phone_match = re.search(
        r"(?:\+62|62|0)(?:\s*[-()]?\s*\d){9,}", text.replace(" ", "")
    )
    if phone_match:
        profile["phone"] = phone_match.group()

    # Nama - Improved name detection
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:3]:  # Check first 3 non-empty lines
        if (
            2 <= len(line.split()) <= 5
            and not any(char.isdigit() for char in line)
            and not any(
                word.lower() in line.lower() for word in ["resume", "cv", "curriculum"]
            )
        ):
            profile["name"] = line
            break

    # Overview - Improved pattern
    overview_pattern = r"(?:PROFILE|SUMMARY|OVERVIEW|ABOUT|OBJECTIVE).*?\n(.*?)(?=\n\s*(?:EDUCATION|EXPERIENCE|SKILLS|WORK|EMPLOYMENT)|\Z)"
    overview_match = re.search(overview_pattern, text, re.IGNORECASE | re.DOTALL)
    if overview_match:
        overview_text = overview_match.group(1)
        # Clean up the overview text
        overview_text = " ".join(line.strip() for line in overview_text.splitlines())
        profile["overview"] = overview_text.strip()

    # Skills - Improved detection
    skills_pattern = r"(?:SKILLS|TECHNICAL SKILLS|COMPETENCIES|KEAHLIAN).*?\n(.*?)(?=\n\s*(?:EDUCATION|EXPERIENCE|WORK|EMPLOYMENT)|\Z)"
    skills_match = re.search(skills_pattern, text, re.IGNORECASE | re.DOTALL)
    if skills_match:
        skills_text = skills_match.group(1)
        # Split by common separators
        skills = re.split(r"[,•\n-]|\s{2,}", skills_text)
        profile["skills"] = [
            skill.strip() for skill in skills if len(skill.strip()) > 2
        ]

    # Experience - Improved pattern
    exp_pattern = (
        r"(?:EXPERIENCE|WORK|EMPLOYMENT).*?\n(.*?)(?=\n\s*(?:EDUCATION|SKILLS)|\Z)"
    )
    exp_section = re.search(exp_pattern, text, re.IGNORECASE | re.DOTALL)
    if exp_section:
        exp_text = exp_section.group(1)
        experience_matches = re.finditer(
            r"(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|(?:19|20)\d{2})\s*[-–]\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|(?:19|20)\d{2}|Present|Now|Current|Sekarang).*?\n(.*?)(?=\n\s*(?:\d{4}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)|\Z)",
            exp_text,
            re.IGNORECASE | re.DOTALL,
        )
        for match in experience_matches:
            exp_text = match.group(0).strip()
            date_pattern = r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|(?:19|20)\d{2})\s*[-–]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|(?:19|20)\d{2}|Present|Now|Current|Sekarang)"
            dates = re.search(date_pattern, exp_text, re.IGNORECASE)
            if dates:
                profile["experience"].append(
                    {
                        "start": dates.group(1),
                        "end": dates.group(2),
                        "position": " ".join(exp_text.split("\n")[1:]).strip(),
                    }
                )

    # Education - Improved pattern
    edu_pattern = r"(?:EDUCATION|PENDIDIKAN).*?\n(.*?)(?=\n\s*(?:EXPERIENCE|SKILLS|WORK|EMPLOYMENT)|\Z)"
    edu_section = re.search(edu_pattern, text, re.IGNORECASE | re.DOTALL)
    if edu_section:
        edu_text = edu_section.group(1)
        education_matches = re.finditer(
            r"(?:(?:19|20)\d{2}[-–]\d{4}|(?:19|20)\d{2})\s*(.*?)(?=\n\s*\d{4}|\Z)",
            edu_text,
            re.IGNORECASE | re.DOTALL,
        )
        for match in education_matches:
            profile["education"].append(match.group().strip())

    return profile
