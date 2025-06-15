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
                    break

        # SIGNIFICANTLY IMPROVED SKILLS EXTRACTION based on HR examples
        skills_patterns = [
            # Direct Skills section
            r"(?i)(?:Skills|Technical\s+Skills|Core\s+Competencies|Highlights|Key\s+Skills|Programming\s+Languages|Technologies)\s*:?\s*\n(.*?)(?=\n\s*(?:Experience|Work\s+History|Job\s+History|Education|Employment|Training|Accomplishments|Professional\s+Experience|EXPERIENCE|EDUCATION)|\Z)",
            # Skills at end of resume (common pattern in HR examples)
            r"(?i)Skills\s*:?\s*\n?(.*?)(?=\n\s*(?:Professional\s+Affiliations|Additional\s+Information|References|Interests|Education|Activities)|\Z)",
            # Inline skills listing
            r"(?i)Skills[\s:]*([A-Za-z\s,\.\-&/+#()]+(?:,\s*[A-Za-z\s\.\-&/+#()]+)*)",
        ]
        
        # Enhanced skill extraction from HR patterns
        skills_found = set()
        
        for pattern in skills_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                skills_text = match.group(1).strip()
                                
                # Extract skills from various formats
                current_skills = []
                
                # Split by common delimiters
                for delimiter in [',', ';', '•', '\n', '|', '·']:
                    if delimiter in skills_text:
                        current_skills.extend([skill.strip() for skill in skills_text.split(delimiter)])
                
                # If no delimiters, try to extract from continuous text
                if not current_skills:
                    current_skills = [skills_text]
                
                # Clean and filter skills
                for skill in current_skills:
                    skill = re.sub(r'[^\w\s\+\#\.\-/()]', '', skill).strip()
                    if len(skill) > 1 and len(skill) < 40 and skill.lower() not in ['skills', 'technical skills', 'core competencies']:
                        skills_found.add(skill)
                
                if skills_found:
                    break

        # Extract additional skills from text based on HR examples
        hr_skill_keywords = [
            # HR specific skills from examples
            'HRIS', 'HR', 'Human Resources', 'Payroll', 'Benefits', 'Recruitment', 'Performance Management',
            'Employee Relations', 'Compliance', 'Training', 'Development', 'FMLA', 'Workers Compensation',
            'ADP', 'PeopleSoft', 'SAP', 'Excel', 'Microsoft Office', 'Database', 'Policies', 'Procedures',
            'Hiring', 'Onboarding', 'Exit Interviews', 'Safety', 'OSHA', 'Compensation', 'Benefits Administration',
            'Employment Law', 'Labor Relations', 'Organizational Development', 'Talent Management',
            # Technical skills from examples
            'Word', 'PowerPoint', 'Outlook', 'Windows', 'Database Management', 'Report Writing',
            'Data Entry', 'Filing', 'Customer Service', 'Project Management', 'Leadership',
            'Communication', 'Problem Solving', 'Team Building', 'Conflict Resolution',
            'Time Management', 'Multitasking', 'Detail Oriented', 'Analytical', 'Organizational'
        ]
        
        for skill in hr_skill_keywords:
            if re.search(rf'\b{re.escape(skill)}\b', text, re.IGNORECASE):
                skills_found.add(skill)
        
        profile["skills"] = list(skills_found)[:25]  # Limit to 25 skills

        # SIGNIFICANTLY IMPROVED EXPERIENCE EXTRACTION based on HR examples
        exp_patterns = [
            # Standard Experience section
            r"(?i)(?:Experience|Work\s+History|Professional\s+Experience|Employment\s+History|Job\s+History)\s*:?\s*\n(.*?)(?=\n\s*(?:Education|Skills|Certifications|References|Training|EDUCATION|SKILLS)|\Z)",
            # Experience without header (date-based detection)
            r"((?:\d{2}/\d{4}\s+to\s+\d{2}/\d{4}|\d{2}/\d{4}\s+to\s+Current|\d{2}/\d{4}\s+to\s+\d{2}/\d{4}).*?)(?=\n\s*(?:Education|Skills|Certifications)|\Z)",
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                exp_section = match.group(1).strip()
                                
                # IMPROVED: Split by job entries using multiple patterns
                experiences = []
                
                # Pattern 1: Date ranges (MM/YYYY to MM/YYYY or MM/YYYY to Current)
                date_pattern = r'(\d{2}/\d{4}\s+to\s+(?:\d{2}/\d{4}|Current))'
                date_matches = list(re.finditer(date_pattern, exp_section))
                
                if len(date_matches) >= 1:                    
                    for i in range(len(date_matches)):
                        start_pos = date_matches[i].start()
                        end_pos = date_matches[i+1].start() if i+1 < len(date_matches) else len(exp_section)
                        
                        job_text = exp_section[start_pos:end_pos].strip()
                        
                        if len(job_text) > 50:  # Valid job entry
                            exp_entry = parse_single_experience_improved(job_text)
                            if exp_entry:
                                experiences.append(exp_entry)
                else:
                    # Pattern 2: Company Name patterns
                    company_pattern = r'(Company\s+Name[^\n]*\n.*?)(?=Company\s+Name|\Z)'
                    company_matches = list(re.finditer(company_pattern, exp_section, re.DOTALL))
                    
                    if len(company_matches) >= 1:
                        for match in company_matches:
                            job_text = match.group(1).strip()
                            if len(job_text) > 50:
                                exp_entry = parse_single_experience_improved(job_text)
                                if exp_entry:
                                    experiences.append(exp_entry)
                    else:
                        # Fallback: Single experience
                        exp_entry = parse_single_experience_improved(exp_section)
                        if exp_entry:
                            experiences = [exp_entry]
                
                profile["experience"] = experiences
                break        # SIMPLIFIED EDUCATION EXTRACTION - RAW TEXT ONLY
        edu_patterns = [
            # Main education section pattern - capture everything until next major section
            r"(?i)(?:Education|Educational\s+Background|Academic\s+Background|Academic\s+Qualifications|EDUCATION)\s*:?\s*,?\s*\n(.*?)(?=\n\s*(?:Experience|Work\s+History|Professional\s+Experience|Employment|Skills|Technical\s+Skills|Core\s+Skills|Certifications|References|Training|Summary|Overview|Professional\s+Summary|Accomplishments|Awards|Highlights|EXPERIENCE|WORK|SKILLS|CERTIFICATIONS|REFERENCES|TRAINING|SUMMARY|OVERVIEW|HIGHLIGHTS)|\Z)",
        ]
        
        for pattern in edu_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                edu_section = match.group(1).strip()
                
                # Clean up the text but keep structure
                lines = [line.strip() for line in edu_section.split('\n') if line.strip()]
                
                # Filter out lines that are clearly not education related and remove excessive empty lines
                filtered_lines = []
                empty_line_count = 0
                
                for line in lines:
                    # Skip lines that are clearly section headers for other sections
                    if re.match(r'(?i)^(Experience|Work|Skills|Employment|Training|Certifications|References|Summary|Overview|Highlights)', line):
                        break  # Stop processing when we hit another section
                    
                    if line.strip() == "":
                        empty_line_count += 1
                        if empty_line_count >= 5:  # Stop if more than 5 consecutive empty lines
                            break
                    else:
                        empty_line_count = 0
                        filtered_lines.append(line)
                
                # Create one education entry with raw text
                if filtered_lines and len('\n'.join(filtered_lines)) > 20:
                    education_raw_text = '\n'.join(filtered_lines)
                    profile["education"] = [{
                        "raw_text": education_raw_text,
                        "degree": "Education Background",
                        "institution": "Multiple Institutions",
                        "date": "Multiple Years",
                        "field": ""
                    }]
                break

    except Exception as e:
        print(f"DEBUG - Error in extract_profile_data: {e}")

    # Clean up and remove duplicates
    profile["skills"] = list(dict.fromkeys(profile["skills"]))[:25]
    profile["certifications"] = list(dict.fromkeys(profile["certifications"]))[:5]
    profile["achievements"] = list(dict.fromkeys(profile["achievements"]))[:5]
    
    return profile

def parse_single_experience_improved(job_text):
    """IMPROVED: Parse a single job experience entry with better date extraction"""
    try:
        lines = [line.strip() for line in job_text.split('\n') if line.strip()]
        
        # IMPROVED: Extract dates with comprehensive patterns based on your data
        date_patterns = [
            # MM/YYYY to MM/YYYY or Current patterns
            r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4})',
            r'(\d{1,2}/\d{4})\s+to\s+(Current)',
            # Month YYYY to Month YYYY patterns  
            r'(\w+\s+\d{4})\s+to\s+(\w+\s+\d{4})',
            r'(\w+\s+\d{4})\s+to\s+(Current)',
            # YYYY to YYYY patterns
            r'(\d{4})\s+to\s+(\d{4})',
            r'(\d{4})\s+to\s+(Current)',
            # MM/YYYY - MM/YYYY patterns (with dash)
            r'(\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{4})',
            r'(\d{1,2}/\d{4})\s*-\s*(Current)',
            # Month Year - Month Year patterns
            r'(\w+\s+\d{4})\s*-\s*(\w+\s+\d{4})',
            r'(\w+\s+\d{4})\s*-\s*(Current)',
            # Present variations
            r'(\d{1,2}/\d{4})\s+to\s+(Present)',
            r'(\w+\s+\d{4})\s+to\s+(Present)',
        ]
        
        start_date = ""
        end_date = ""
        period = "Period not specified"
        
        for pattern in date_patterns:
            date_match = re.search(pattern, job_text, re.IGNORECASE)
            if date_match:
                start_date = date_match.group(1).strip()
                end_date = date_match.group(2).strip()
                
                # Normalize "Current" and "Present" to "Now"
                if end_date.lower() in ['current', 'present']:
                    end_date = "Now"
                
                period = f"{start_date} to {end_date}"
                break
        
        # If no paired dates found, try to find individual dates
        if not start_date:
            single_date_patterns = [
                r'(\d{1,2}/\d{4})',
                r'(\w+\s+\d{4})',
                r'(\d{4})'
            ]
            
            for pattern in single_date_patterns:
                matches = re.findall(pattern, job_text)
                if len(matches) >= 2:
                    start_date = matches[0]
                    end_date = matches[1]
                    period = f"{start_date} to {end_date}"
                    break
                elif len(matches) == 1:
                    start_date = matches[0]
                    end_date = "Now"
                    period = f"{start_date} to Now"
                    break
        
        # Extract job title - improved patterns based on HR examples
        title = ""
        title_patterns = [
            r'(?:HR\s+)?(?:Manager|Director|Analyst|Specialist|Coordinator|Assistant|Representative|Administrator|Supervisor|Generalist|Clerk)',
            r'(?:Human\s+Resources?\s+)?(?:Manager|Director|Specialist|Coordinator)',
            r'(?:Senior\s+)?(?:HR\s+)?(?:Analyst|Specialist|Manager)',
            r'(?:Benefits?\s+)?(?:Administrator|Coordinator)',
            r'(?:Recruiting?\s+)?(?:Coordinator|Specialist)',
        ]
        
        for pattern in title_patterns:
            title_match = re.search(pattern, job_text, re.IGNORECASE)
            if title_match:
                # Get more context around the match
                for line in lines:
                    if title_match.group().lower() in line.lower():
                        title = line[:80]  # Limit length
                        break
                break
        
        # Extract company - improved patterns
        company = ""
        company_patterns = [
            r'Company\s+Name[^\n]*',
            r'(?:at\s+)?([A-Z][a-zA-Z\s&,\.]+(?:Inc|Corp|LLC|Ltd|Company|Corporation|Group))',
            r'([A-Z][a-zA-Z\s&,\.]+(?:University|College|Hospital|Medical|Center))',
        ]
        
        for pattern in company_patterns:
            company_match = re.search(pattern, job_text)
            if company_match:
                company = company_match.group().replace('Company Name', '').strip()[:60]
                break
        
        # Extract description - focus on responsibilities and achievements
        description_lines = []
        responsibility_keywords = [
            'responsibilities', 'duties', 'managed', 'coordinated', 'developed', 'implemented',
            'administered', 'supervised', 'conducted', 'maintained', 'processed', 'assisted',
            'provided', 'ensured', 'handled', 'recruited', 'trained', 'analyzed'
        ]
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in responsibility_keywords):
                if len(line) > 20 and not re.match(r'^\d{1,2}/\d{4}', line):
                    description_lines.append(line)
        
        description = ' '.join(description_lines[:3]) if description_lines else job_text[:300]
        
        return {
            'title': title,
            'company': company,
            'period': period,
            'start': start_date,
            'end': end_date,
            'description': description[:400]
        }
    except Exception as e:
        print(f"DEBUG - Error parsing experience: {e}")
        return None

def parse_single_education_improved(edu_text):
    """IMPROVED: Parse a single education entry based on HR examples"""
    try:
        lines = [line.strip() for line in edu_text.split('\n') if line.strip()]
        
        # Extract degree with improved patterns
        degree_patterns = [
            r'(Master\s+of\s+(?:Science|Arts|Business\s+Administration|Education))',
            r'(Bachelor\s+of\s+(?:Science|Arts|Commerce))',
            r'(Master|Bachelor|PhD|Doctorate|Associate)',
            r'(MBA|MS|MA|BS|BA|PhD)'
        ]
        
        degree = "Degree"
        for pattern in degree_patterns:
            degree_match = re.search(pattern, edu_text, re.IGNORECASE)
            if degree_match:
                degree = degree_match.group(1)
                break
        
        # Extract field of study - improved patterns
        field = ""
        field_patterns = [
            r'(?:in\s+|:\s*)([A-Za-z\s]+(?:Science|Arts|Management|Engineering|Studies|Administration))',
            r'(?:Major|Field|Study):\s*([A-Za-z\s]+)',
            r'(?:Bachelor|Master|PhD)\s+(?:of\s+)?(?:Science|Arts)\s*:\s*([A-Za-z\s]+)',
        ]
        
        for pattern in field_patterns:
            field_match = re.search(pattern, edu_text, re.IGNORECASE)
            if field_match:
                field = field_match.group(1).strip()[:50]
                break
        
        # Extract institution - improved patterns
        institution = "Institution"
        institution_patterns = [
            r'([A-Z][a-zA-Z\s]+(?:University|College|Institute|School))',
            r'(University\s+of\s+[A-Za-z\s]+)',
            r'([A-Z][a-zA-Z\s]+\s+State\s+University)',
        ]
        
        for pattern in institution_patterns:
            inst_match = re.search(pattern, edu_text)
            if inst_match:
                institution = inst_match.group(1)[:70]
                break
        
        # Extract year - multiple patterns
        year_patterns = [
            r'\b(19|20)\d{2}\b',
            r'(?:Graduated|Completed|Finished):\s*(\d{4})',
        ]
        
        date = "Year not specified"
        for pattern in year_patterns:
            year_match = re.search(pattern, edu_text)
            if year_match:
                date = year_match.group().strip()
                break
        
        return {
            'degree': degree,
            'field': field,
            'institution': institution,
            'date': date
        }
    except Exception as e:
        print(f"DEBUG - Error parsing education: {e}")
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