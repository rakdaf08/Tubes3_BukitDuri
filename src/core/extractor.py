import fitz
import re
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file using PyMuPDF"""
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        
        text = text.replace('\n\n', '\n').strip()
        
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    
    return text

def extract_profile_data(text: str) -> dict:
    """Extract structured profile data from resume text"""
    profile = {
        "overview": None,
        "skills": [],
        "experience": [],
        "education": [],
        "gpa": [],
        "certifications": [],
        "achievements": [],
    }

    try:
        # summary
        overview_pattern = r"(?i)(PROFILE|SUMMARY|OVERVIEW|ABOUT|OBJECTIVE)[^\n]*\n+(.*?)(?=\n\s*(EDUCATION|EXPERIENCE|SKILLS|WORK|EMPLOYMENT|TRAINING)|\Z)"
        overview_match = re.search(overview_pattern, text, re.DOTALL)
        if overview_match:
            profile["overview"] = overview_match.group(2).strip()

        # skills
        skills_patterns = [
            r"(?i)(?:SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES)[^\n]*\n(.*?)(?=\n\s*(?:ACCOMPLISHMENTS|CERTIFICATIONS|EDUCATION|EXPERIENCE|WORK|EMPLOYMENT|TRAINING)|\Z)",
            r"(?i)(?:PROGRAMMING LANGUAGES?|TECHNOLOGIES?)[^\n]*\n(.*?)(?=\n\s*(?:ACCOMPLISHMENTS|CERTIFICATIONS|EDUCATION|EXPERIENCE|WORK)|\Z)"
        ]
        
        for pattern in skills_patterns:
            try:
                skills_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
                if skills_match:
                    skills_text = skills_match.group(1)
                    skills_list = re.split(r'[,\n•·▪▫\-\|]', skills_text)
                    skills = [skill.strip() for skill in skills_list if skill.strip() and len(skill.strip()) > 1]
                    profile["skills"].extend(skills)
                    break
            except Exception as e:
                print(f"Error in skills extraction: {e}")
                continue

        # common skill
        common_skills = [
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'SQL', 'HTML', 'CSS', 'React', 'Angular',
            'Node.js', 'Machine Learning', 'Data Analysis', 'Project Management', 'Leadership',
            'Communication', 'Problem Solving', 'Teamwork', 'Git', 'AWS', 'Docker', 'Kubernetes',
            'Excel', 'PowerPoint', 'Word', 'Accounting', 'Finance', 'Budgeting', 'Auditing'
        ]
        
        for skill in common_skills:
            try:
                if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                    if skill not in profile["skills"]:
                        profile["skills"].append(skill)
            except Exception as e:
                continue

        # exp
        exp_patterns = [
            r"(?i)([A-Z][^0-9\n]*)\s+(\d{4})\s*[-–]\s*(\d{4}|present|current)",
            r"(?i)([A-Z][^0-9\n]*)\s+(\d{1,2}[/\-]\d{4})\s*[-–]\s*(\d{1,2}[/\-]\d{4}|present|current)"
        ]
        
        for pattern in exp_patterns:
            try:
                experience_matches = re.finditer(pattern, text)
                for match in experience_matches:
                    if len(match.groups()) >= 3:
                        exp_entry = {
                            "title": match.group(1).strip(),
                            "start": match.group(2).strip(),
                            "end": match.group(3).strip(),
                            "description": ""
                        }
                        profile["experience"].append(exp_entry)
            except Exception as e:
                print(f"Error in experience extraction: {e}")
                continue

        # edu
        edu_patterns = [
            r"(?i)(Bachelor|Associate|Master|Ph\.?D|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?)\s*(?:of|in)?\s*([^,\n]+)",
            r"(?i)(Bachelor|Master|PhD)\s+([^,\n]+)"
        ]
        
        for pattern in edu_patterns:
            try:
                edu_matches = re.finditer(pattern, text)
                for match in edu_matches:
                    if len(match.groups()) >= 2:
                        edu_entry = {
                            "degree": match.group(1).strip(),
                            "field": match.group(2).strip(),
                            "date": ""
                        }
                        profile["education"].append(edu_entry)
            except Exception as e:
                print(f"Error in education extraction: {e}")
                continue

        # gpa
        gpa_patterns = [
            r"(?i)(?:GPA|Grade Point Average)[:\s]*(\d+\.?\d*)",
            r"(\d+\.\d+)\s*/\s*4\.0"
        ]
        
        for pattern in gpa_patterns:
            try:
                gpa_matches = re.findall(pattern, text)
                for gpa in gpa_matches:
                    try:
                        gpa_val = float(gpa)
                        if 0.0 <= gpa_val <= 4.0:  # valid GPA
                            profile["gpa"].append(str(gpa_val))
                    except ValueError:
                        continue
            except Exception as e:
                print(f"Error in GPA extraction: {e}")
                continue

        cert_patterns = [
            r"(?i)(?:CERTIFICATIONS?|CERTIFICATES?)[^\n]*\n([^0-9]*?)(?=\n\s*(?:[A-Z]{2,}|EDUCATION|EXPERIENCE|SKILLS|\Z))",
            r"(?i)(Certified\s+[^,\n]+)"
        ]
        
        for pattern in cert_patterns:
            try:
                cert_matches = re.findall(pattern, text, re.DOTALL)
                for cert_text in cert_matches:
                    if isinstance(cert_text, tuple):
                        cert_text = cert_text[0] if cert_text else ""
                    
                    cert_list = re.split(r'[,\n•·▪▫\-]', cert_text)
                    certs = [cert.strip() for cert in cert_list if cert.strip() and len(cert.strip()) > 2]
                    profile["certifications"].extend(certs)
            except Exception as e:
                print(f"Error in certifications extraction: {e}")
                continue

        highlights_pattern = r"(?i)(?:HIGHLIGHTS|ACCOMPLISHMENTS)[^\n]*\n(.*?)(?=\n\s*(?:[A-Z]{2,}|EDUCATION|EXPERIENCE|\Z))"
        try:
            highlights_match = re.search(highlights_pattern, text, re.DOTALL)
            if highlights_match:
                highlights_text = highlights_match.group(1)
                highlight_list = re.split(r'[,\n•·▪▫\-]', highlights_text)
                for highlight in highlight_list:
                    cleaned = highlight.strip()
                    if cleaned and len(cleaned) > 5:
                        profile["skills"].append(cleaned)
        except Exception as e:
            print(f"Error in highlights extraction: {e}")

    except Exception as e:
        print(f"General error in profile extraction: {e}")

    # remove duplikat
    profile["skills"] = list(set(profile["skills"]))
    
    return profile

def print_profile(profile: dict):
    """Print formatted profile data"""
    print("=== EXTRACTED PROFILE DATA ===")
    
    if profile.get("overview"):
        print(f"Overview: {profile['overview'][:100]}...")
    
    if profile.get("skills"):
        print(f"Skills ({len(profile['skills'])}): {', '.join(profile['skills'][:10])}...")
    
    if profile.get("experience"):
        print(f"Experience ({len(profile['experience'])} entries):")
        for exp in profile['experience'][:3]:
            print(f"  - {exp.get('title', 'N/A')} ({exp.get('start', '')} - {exp.get('end', '')})")
    
    if profile.get("education"):
        print(f"Education ({len(profile['education'])} entries):")
        for edu in profile['education']:
            print(f"  - {edu.get('degree', '')} in {edu.get('field', '')}")
    
    if profile.get("gpa"):
        print(f"GPA: {profile['gpa'][0]}")
    
    if profile.get("certifications"):
        print(f"Certifications ({len(profile['certifications'])}): {', '.join(profile['certifications'][:3])}...")