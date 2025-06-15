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
        # IMPROVED OVERVIEW/SUMMARY EXTRACTION
        overview_patterns = [
            r"(?i)(?:Summary|Professional\s+Summary|Executive\s+Summary|Profile|About|Overview|Objective|Career\s+Summary)\s*:?\s*\n(.*?)(?=\n\s*(?:Highlights|Skills|Experience|Work\s+History|Job\s+History|Education|Employment|Training|Accomplishments|Core\s+Qualifications|HIGHLIGHTS|SKILLS|EXPERIENCE|EDUCATION)|\Z)",
            r"(?i)(?:Professional\s+Experience|Core\s+Accomplishments)\s*:?\s*\n(.*?)(?=\n\s*(?:Experience|Work\s+History|Education|Skills|EXPERIENCE|EDUCATION|SKILLS)|\Z)",
            r"(?i)(?:Dedicated|Experienced|Motivated|Dynamic).{20,200}(?=\n\s*(?:Highlights|Skills|Experience|Education))"
        ]
        
        for pattern in overview_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                overview = match.group(1).strip()
                if len(overview) > 30:
                    profile["overview"] = re.sub(r'\s+', ' ', overview)
                    print(f"DEBUG - Found overview: {len(overview)} chars")
                    break

        # IMPROVED SKILLS EXTRACTION
        skills_patterns = [
            r"(?i)(?:Skills|Technical\s+Skills|Core\s+Competencies|Highlights|Key\s+Skills|Programming\s+Languages|Technologies)\s*:?\s*\n(.*?)(?=\n\s*(?:Experience|Work\s+History|Job\s+History|Education|Employment|Training|Accomplishments|Professional\s+Experience|EXPERIENCE|EDUCATION)|\Z)",
            r"(?i)Skills[\s:]*([A-Za-z\s,\.\-&/+#]+(?:,\s*[A-Za-z\s\.\-&/+#]+)*)",
        ]
        
        for pattern in skills_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                skills_text = match.group(1).strip()
                print(f"DEBUG - Found skills section: {skills_text[:100]}...")
                
                # Extract skills from various formats
                skills = []
                
                # Split by common delimiters
                for delimiter in [',', ';', '•', '\n', '|']:
                    if delimiter in skills_text:
                        skills.extend([skill.strip() for skill in skills_text.split(delimiter)])
                
                # Clean and filter skills
                cleaned_skills = []
                for skill in skills:
                    skill = re.sub(r'[^\w\s\+\#\.\-]', '', skill).strip()
                    if len(skill) > 1 and len(skill) < 30 and skill.lower() not in ['skills', 'technical skills']:
                        cleaned_skills.append(skill)
                
                profile["skills"].extend(cleaned_skills)
                if cleaned_skills:
                    break

        # FIXED EXPERIENCE EXTRACTION - Split multiple experiences
        exp_patterns = [
            r"(?i)(?:Experience|Work\s+History|Professional\s+Experience|Employment\s+History|Job\s+History)\s*:?\s*\n(.*?)(?=\n\s*(?:Education|Skills|Certifications|References|Training|EDUCATION|SKILLS)|\Z)",
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                exp_section = match.group(1).strip()
                print(f"DEBUG - Found experience section: {exp_section[:100]}...")
                
                # SPLIT BY DATE PATTERNS to separate multiple jobs
                date_pattern = r'\b(?:0[1-9]|1[0-2])/(?:19|20)\d{2}\b'
                
                # Find all date matches with their positions
                date_matches = list(re.finditer(date_pattern, exp_section))
                
                if len(date_matches) >= 2:  # Multiple jobs found
                    print(f"DEBUG - Found {len(date_matches)} date patterns, splitting experiences")
                    
                    experiences = []
                    for i in range(len(date_matches)):
                        start_pos = date_matches[i].start()
                        end_pos = date_matches[i+1].start() if i+1 < len(date_matches) else len(exp_section)
                        
                        job_text = exp_section[start_pos:end_pos].strip()
                        
                        if len(job_text) > 20:  # Valid job entry
                            exp_entry = parse_single_experience(job_text)
                            if exp_entry:
                                experiences.append(exp_entry)
                    
                    profile["experience"] = experiences
                    print(f"DEBUG - Extracted {len(experiences)} separate experiences")
                else:
                    # Single experience or fallback
                    exp_entry = parse_single_experience(exp_section)
                    if exp_entry:
                        profile["experience"] = [exp_entry]
                break

        # FIXED EDUCATION EXTRACTION - Split multiple degrees
        edu_patterns = [
            r"(?i)(?:Education|Educational\s+Background|Academic\s+Background)\s*:?\s*\n(.*?)(?=\n\s*(?:Experience|Work|Skills|Certifications|References|Training|EXPERIENCE|WORK|SKILLS)|\Z)",
        ]
        
        for pattern in edu_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                edu_section = match.group(1).strip()
                print(f"DEBUG - Found education section: {edu_section[:100]}...")
                
                # SPLIT BY DEGREE KEYWORDS to separate multiple degrees
                degree_keywords = ['Master of Science', 'Master of Arts', 'Bachelor of Science', 'Bachelor of Arts', 'Master', 'Bachelor', 'PhD', 'Doctorate']
                
                education_entries = []
                remaining_text = edu_section
                
                # Find degree positions
                degree_positions = []
                for keyword in degree_keywords:
                    for match in re.finditer(rf'\b{re.escape(keyword)}\b', remaining_text, re.IGNORECASE):
                        degree_positions.append((match.start(), keyword, match.group()))
                
                # Sort by position
                degree_positions.sort(key=lambda x: x[0])
                
                if len(degree_positions) >= 2:  # Multiple degrees found
                    print(f"DEBUG - Found {len(degree_positions)} degrees, splitting education")
                    
                    for i in range(len(degree_positions)):
                        start_pos = degree_positions[i][0]
                        end_pos = degree_positions[i+1][0] if i+1 < len(degree_positions) else len(edu_section)
                        
                        degree_text = edu_section[start_pos:end_pos].strip()
                        
                        if len(degree_text) > 10:  # Valid degree entry
                            edu_entry = parse_single_education(degree_text)
                            if edu_entry:
                                education_entries.append(edu_entry)
                    
                    profile["education"] = education_entries
                    print(f"DEBUG - Extracted {len(education_entries)} separate education entries")
                else:
                    # Single education or fallback
                    edu_entry = parse_single_education(edu_section)
                    if edu_entry:
                        profile["education"] = [edu_entry]
                break

        # Add common technical skills found in text
        tech_skills = ['Python', 'Java', 'JavaScript', 'SQL', 'HTML', 'CSS', 'React', 'Node.js', 'Git', 'Linux']
        for skill in tech_skills:
            if skill.lower() in text.lower() and skill not in profile["skills"]:
                profile["skills"].append(skill)

    except Exception as e:
        print(f"DEBUG - Error in extract_profile_data: {e}")

    # Clean up and remove duplicates
    profile["skills"] = list(dict.fromkeys(profile["skills"]))[:20]
    profile["certifications"] = list(dict.fromkeys(profile["certifications"]))[:5]
    profile["achievements"] = list(dict.fromkeys(profile["achievements"]))[:5]
    
    return profile

def parse_single_experience(job_text):
    """Parse a single job experience entry"""
    try:
        lines = [line.strip() for line in job_text.split('\n') if line.strip()]
        
        # Extract dates (first line usually contains dates)
        date_pattern = r'(?:0[1-9]|1[0-2])/(?:19|20)\d{2}'
        period = "Period not specified"
        
        for line in lines[:2]:
            if re.search(date_pattern, line):
                period = line
                break
        
        # Extract title and company
        title = "Position"
        company = "Company"
        description = job_text
        
        # Look for job titles in first few lines
        title_keywords = ['manager', 'analyst', 'engineer', 'director', 'specialist', 'coordinator', 'assistant', 'developer', 'consultant']
        for line in lines[:3]:
            if any(keyword in line.lower() for keyword in title_keywords):
                title = line[:50]  # Limit title length
                break
        
        # Extract company (usually after title)
        for line in lines[:3]:
            if 'company' in line.lower() or 'corp' in line.lower() or 'inc' in line.lower():
                company = line[:50]
                break
        
        return {
            'title': title,
            'company': company,
            'period': period,
            'start': period.split(' to ')[0] if ' to ' in period else 'Start',
            'end': period.split(' to ')[1] if ' to ' in period else 'End',
            'description': description[:300]  # Limit description
        }
    except Exception as e:
        print(f"DEBUG - Error parsing experience: {e}")
        return None

def parse_single_education(edu_text):
    """Parse a single education entry"""
    try:
        lines = [line.strip() for line in edu_text.split('\n') if line.strip()]
        
        # Extract degree
        degree_keywords = ['Master of Science', 'Master of Arts', 'Bachelor of Science', 'Bachelor of Arts', 'Master', 'Bachelor', 'PhD']
        degree = "Degree"
        
        for keyword in degree_keywords:
            if keyword.lower() in edu_text.lower():
                degree = keyword
                break
        
        # Extract institution
        institution = "Institution"
        institution_keywords = ['university', 'college', 'institute']
        for line in lines:
            if any(keyword in line.lower() for keyword in institution_keywords):
                institution = line[:60]
                break
        
        # Extract year
        year_pattern = r'\b(19|20)\d{2}\b'
        year_match = re.search(year_pattern, edu_text)
        date = year_match.group(0) if year_match else "Year not specified"
        
        # Extract field of study
        field = ""
        field_indicators = [':', 'in ', 'of ']
        for indicator in field_indicators:
            if indicator in edu_text:
                parts = edu_text.split(indicator)
                if len(parts) > 1:
                    field = parts[1].split('\n')[0].strip()[:50]
                    break
        
        return {
            'degree': degree,
            'field': field,
            'institution': institution,
            'date': date
        }
    except Exception as e:
        print(f"DEBUG - Error pasdasdaarsing education: {e}")
        return None
        
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
            print(f"  - {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('start', '')} - {exp.get('end', '')})")
    
    if profile.get("education"):
        print(f"Education ({len(profile['education'])} entries):")
        for edu in profile['education']:
            print(f"  - {edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}")
    
    if profile.get("gpa"):
        print(f"GPA: {profile['gpa'][0]}")
    
    if profile.get("certifications"):
        print(f"Certifications ({len(profile['certifications'])}): {', '.join(profile['certifications'][:3])}...")