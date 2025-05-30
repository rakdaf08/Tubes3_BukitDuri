import fitz
import re
import os


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        base_dir = os.path.dirname(os.path.dirname(pdf_path))
        regex_dir = os.path.join(base_dir, "regex")
        string_dir = os.path.join(base_dir, "string")

        os.makedirs(regex_dir, exist_ok=True)
        os.makedirs(string_dir, exist_ok=True)

        # Extract text from PDF
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()

        # Get filename without extension
        filename = os.path.splitext(os.path.basename(pdf_path))[0]

        # Save regex version (normal format)
        regex_path = os.path.join(regex_dir, f"{filename}_regex.txt")
        with open(regex_path, "w", encoding="utf-8") as f:
            f.write(text)

        # Save string matching version (single line)
        string_path = os.path.join(string_dir, f"{filename}_string.txt")
        clean_text = " ".join(text.split())
        with open(string_path, "w", encoding="utf-8") as f:
            f.write(clean_text)

        print(f"[INFO] Berhasil menyimpan file regex: {regex_path}")
        print(f"[INFO] Berhasil menyimpan file string matching: {string_path}")

    except Exception as e:
        print(f"[ERROR] Gagal membaca PDF {pdf_path}: {e}")
    return text


def extract_profile_data(text: str) -> dict:
    profile = {
        "overview": None,
        "skills": [],
        "experience": [],
        "education": [],
        "gpa": [],
        "certifications": [],
        "achievements": [],
    }

    # Overview
    overview_pattern = r"(?i)(PROFILE|SUMMARY|OVERVIEW|ABOUT|OBJECTIVE)[^\n]*\n+(.*?)(?=\n\s*(EDUCATION|EXPERIENCE|SKILLS|WORK|EMPLOYMENT|TRAINING)|\Z)"
    overview_match = re.search(overview_pattern, text, re.DOTALL)
    if overview_match:
        overview_text = " ".join(
            line.strip() for line in overview_match.group(2).splitlines()
        )
        profile["overview"] = overview_text.strip()

    # Skills
    skills_pattern = r"(?i)^skills\s*\n(.*?)(?=\n\s*(?:accomplishments|certifications|education|experience|work|employment|training)|\Z)"
    skills_match = re.search(
        skills_pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE
    )
    if skills_match:
        skills = re.split(r"[,•\n\-]|\s{2,}", skills_match.group(1))
        profile["skills"] = [
            skill.strip() for skill in skills if len(skill.strip()) > 1
        ]

    # Experience (support "Title MM/YYYY to MM/YYYY" pattern)
    experience_matches = re.finditer(
        r"(?i)(.*?)\s+(\d{2}/\d{4})\s+to\s+(\d{2}/\d{4})\n(.*?)(?=\n\S.*?\d{2}/\d{4}\s+to|\Z)",
        text,
        re.DOTALL,
    )
    for match in experience_matches:
        job_title = match.group(1).strip()
        start = match.group(2)
        end = match.group(3)
        description = " ".join(match.group(4).splitlines()).strip()
        profile["experience"].append(
            {"title": job_title, "start": start, "end": end, "description": description}
        )

    # Education (line contains degree, field, and date)
    edu_pattern = r"(?i)(Bachelor|Associate|Master|Ph\.?D)[^:\n]*[:\s]+(.+?)\s+(May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?\s*(\d{4})"
    edu_matches = re.finditer(edu_pattern, text)
    for match in edu_matches:
        profile["education"].append(
            {
                "degree": match.group(1),
                "field": match.group(2).strip(),
                "date": f"{match.group(3)} {match.group(4)}".strip(),
            }
        )

    # GPA
    gpa_matches = re.findall(r"GPA[-:]?\s*(\d\.\d+)", text)
    profile["gpa"] = gpa_matches

    # Certifications
    cert_match = re.search(
        r"(?i)^certifications\s*\n(.*?)(?=\n\s*(skills|experience|education|accomplishments)|\Z)",
        text,
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    if cert_match:
        certs = re.split(r"[,•\n\-]|\s{2,}", cert_match.group(1))
        profile["certifications"] = [c.strip() for c in certs if len(c.strip()) > 2]

    # Achievements / Accomplishments
    achievements_match = re.search(
        r"(?i)^accomplishments\s*\n(.*?)(?=\n\s*(skills|experience|education|certifications)|\Z)",
        text,
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    if achievements_match:
        items = [
            line.strip()
            for line in achievements_match.group(1).splitlines()
            if line.strip()
        ]
        profile["achievements"] = [i.strip() for i in items if len(i.strip()) > 2]

    return profile


def print_profile(profile: dict):
    """Print profile data in a formatted way with newlines between sections"""
    print("\n=== EXTRACTED PROFILE DATA ===\n")

    # Overview
    print("OVERVIEW:")
    print(f"{profile['overview']}\n")

    # Skills
    print("SKILLS:")
    print("• " + "\n• ".join(profile["skills"]) + "\n")

    # Experience
    print("EXPERIENCE:")
    for exp in profile["experience"]:
        print(f"• {exp['start']} to {exp['end']}")
        print(f"  {exp['description']}")
    print()

    # Education
    print("EDUCATION:")
    for edu in profile["education"]:
        print(f"• {edu['degree']} in {edu['field']}")
        print(f"  Graduated: {edu['date']}")
    print()

    # GPA
    print("GPA:")
    print("• " + "\n• ".join(profile["gpa"]) + "\n")

    # Certifications
    print("CERTIFICATIONS:")
    print("• " + "\n• ".join(profile["certifications"]) + "\n")

    # Achievements
    print("ACHIEVEMENTS:")
    print("• " + "\n• ".join(profile["achievements"]) + "\n")
