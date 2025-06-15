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
            try:
                overview_match = re.search(pattern, text, re.DOTALL)
                if overview_match:
                    overview_text = overview_match.group(1).strip()
                    # Clean up overview
                    overview_text = re.sub(r'\n+', ' ', overview_text)
                    overview_text = re.sub(r'[•·▪▫\-]\s*', '', overview_text)
                    overview_text = ' '.join(overview_text.split())
                    if len(overview_text) > 30 and len(overview_text) < 500:
                        profile["overview"] = overview_text
                        break
            except Exception as e:
                print(f"Error in overview extraction: {e}")
                continue

        # IMPROVED SKILLS EXTRACTION
        skills_patterns = [
            r"(?i)(?:Skills|Technical\s+Skills|Core\s+Competencies|Highlights|Key\s+Skills|Programming\s+Languages|Technologies)\s*:?\s*\n(.*?)(?=\n\s*(?:Experience|Work\s+History|Job\s+History|Education|Employment|Training|Accomplishments|Professional\s+Experience|EXPERIENCE|EDUCATION)|\Z)",
            r"(?i)Skills[\s:]*([A-Za-z\s,\.\-&/+#]+(?:,\s*[A-Za-z\s\.\-&/+#]+)*)",
        ]
        
        for pattern in skills_patterns:
            try:
                skills_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if skills_match:
                    skills_text = skills_match.group(1)
                    # Split skills dengan berbagai delimiter
                    skills_list = re.split(r'[,\n•·▪▫\-\|;]', skills_text)
                    skills = []
                    for skill in skills_list:
                        cleaned_skill = skill.strip()
                        # Filter skills yang valid
                        if (cleaned_skill and 
                            len(cleaned_skill) > 1 and 
                            len(cleaned_skill) < 50 and
                            not re.match(r'^\d+$', cleaned_skill) and
                            not re.match(r'^[^\w\s]+$', cleaned_skill) and
                            not re.match(r'^(and|or|with|the|in|of|for|to|a|an)$', cleaned_skill, re.IGNORECASE)):
                            skills.append(cleaned_skill)
                    
                    profile["skills"].extend(skills[:20])
                    if profile["skills"]:
                        break
            except Exception as e:
                print(f"Error in skills extraction: {e}")
                continue

        # Add common technical skills found in text
        common_skills = [
            'Python', 'Java', 'JavaScript', 'C++', 'C#', 'SQL', 'HTML', 'CSS', 'React', 'Angular',
            'Node.js', 'PHP', 'Ruby', 'Go', 'Swift', 'Kotlin', 'TypeScript', 'Vue.js', 'jQuery',
            'Bootstrap', 'Git', 'GitHub', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'Linux', 'Windows',
            'MySQL', 'PostgreSQL', 'MongoDB', 'Machine Learning', 'Data Analysis', 'Project Management',
            'Excel', 'PowerPoint', 'Photoshop', 'Accounting', 'Finance', 'Marketing'
        ]
        
        skills_found = 0
        for skill in common_skills:
            if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                if skill not in profile["skills"] and skills_found < 15:
                    profile["skills"].append(skill)
                    skills_found += 1

        # IMPROVED EXPERIENCE EXTRACTION - Ambil seluruh section
        exp_section_patterns = [
            r"(?i)(Experience|Work\s+History|Job\s+History|Professional\s+Experience|Employment\s+History|Career\s+History|Work\s+Experience)\s*:?\s*\n(.*?)(?=\n\s*(?:Education|Skills|Certifications|References|Achievements|Accomplishments|EDUCATION|SKILLS|CERTIFICATIONS)|\Z)",
        ]
        
        experience_section = ""
        for pattern in exp_section_patterns:
            try:
                exp_match = re.search(pattern, text, re.DOTALL)
                if exp_match:
                    experience_section = exp_match.group(2).strip()
                    print(f"DEBUG - Found experience section: {experience_section[:200]}...")
                    break
            except Exception as e:
                print(f"Error finding experience section: {e}")
                continue
        
        # Parse experience section jika ditemukan
        if experience_section:
            try:
                # Split berdasarkan pattern umum yang memisahkan entry pekerjaan
                # Biasanya dipisahkan oleh 2+ newlines atau pattern tertentu
                entries = re.split(r'\n\s*\n', experience_section)
                
                for entry in entries:
                    if not entry.strip():
                        continue
                    
                    # Ekstrak informasi dari setiap entry
                    lines = [line.strip() for line in entry.split('\n') if line.strip()]
                    
                    if len(lines) >= 2:
                        title = ""
                        company = ""
                        date_range = ""
                        description = ""
                        
                        # Cari pattern tanggal (biasanya berisi tahun)
                        date_pattern = r'(\d{4}|\d{1,2}/\d{4}|[A-Za-z]+\s+\d{4})'
                        
                        for i, line in enumerate(lines):
                            # Jika line berisi tanggal, kemungkinan ini adalah date range
                            if re.search(date_pattern, line) and ('to' in line.lower() or '-' in line or '–' in line or 'present' in line.lower() or 'current' in line.lower()):
                                date_range = line
                                # Line sebelumnya kemungkinan title atau company
                                if i > 0:
                                    if not title:
                                        title = lines[i-1]
                                    elif not company and i > 1:
                                        company = lines[i-2] if i-2 >= 0 else ""
                                break
                        
                        # Jika tidak ada date range yang jelas, ambil dari pattern umum
                        if not date_range:
                            for line in lines:
                                if re.search(r'\d{4}', line):
                                    date_range = line
                                    break
                        
                        # Jika masih belum ada title, ambil line pertama
                        if not title and lines:
                            title = lines[0]
                        
                        # Jika masih belum ada company, cari line yang mungkin company
                        if not company:
                            for line in lines[1:3]:  # Cek 2 line setelah title
                                if line != title and line != date_range:
                                    # Cek apakah ini kemungkinan nama company
                                    if (re.search(r'(Inc|LLC|Corp|Company|Ltd|University|College|Institute|Group|Solutions|Technologies|Systems)', line, re.IGNORECASE) or
                                        (len(line.split()) <= 5 and not re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December|\d{4})', line, re.IGNORECASE))):
                                        company = line
                                        break
                        
                        # Ambil description dari sisa lines
                        desc_lines = []
                        for line in lines:
                            if line != title and line != company and line != date_range:
                                desc_lines.append(line)
                        description = ' '.join(desc_lines[:3]) if desc_lines else "Professional responsibilities in this role."
                        
                        # Parse date range
                        start_date = "Not specified"
                        end_date = "Not specified"
                        if date_range:
                            # Cari pattern start - end
                            date_split_patterns = [r'\s+to\s+', r'\s*-\s*', r'\s*–\s*', r'\s*~\s*']
                            for split_pattern in date_split_patterns:
                                if re.search(split_pattern, date_range, re.IGNORECASE):
                                    parts = re.split(split_pattern, date_range, flags=re.IGNORECASE)
                                    if len(parts) == 2:
                                        start_date = parts[0].strip()
                                        end_date = parts[1].strip()
                                        break
                        
                        # Clean up data
                        title = title[:80] if title else "Position"
                        company = company[:80] if company else "Company"
                        description = description[:200] if description else "Professional experience."
                        
                        exp_entry = {
                            "title": title,
                            "company": company,
                            "start": start_date,
                            "end": end_date,
                            "description": description
                        }
                        
                        # Avoid duplicates dan entries yang terlalu pendek
                        if (len(title) > 2 and 
                            not any(exp.get('title', '').lower() == title.lower() and 
                                   exp.get('company', '').lower() == company.lower() 
                                   for exp in profile["experience"])):
                            profile["experience"].append(exp_entry)
                        
                        if len(profile["experience"]) >= 6:
                            break
                            
            except Exception as e:
                print(f"Error parsing experience section: {e}")

        # IMPROVED EDUCATION EXTRACTION - Ambil seluruh section
        education_section_patterns = [
            r"(?i)(Education|Educational\s+Background|Academic\s+Background|Qualifications|Academic\s+Qualifications)\s*:?\s*\n(.*?)(?=\n\s*(?:Experience|Work\s+History|Skills|Certifications|References|Achievements|EXPERIENCE|WORK|SKILLS|CERTIFICATIONS)|\Z)",
        ]
        
        education_section = ""
        for pattern in education_section_patterns:
            try:
                edu_match = re.search(pattern, text, re.DOTALL)
                if edu_match:
                    education_section = edu_match.group(2).strip()
                    print(f"DEBUG - Found education section: {education_section[:200]}...")
                    break
            except Exception as e:
                print(f"Error finding education section: {e}")
                continue
        
        # Parse education section jika ditemukan
        if education_section:
            try:
                # Split berdasarkan pattern umum yang memisahkan entry pendidikan
                entries = re.split(r'\n\s*\n', education_section)
                
                for entry in entries:
                    if not entry.strip():
                        continue
                    
                    lines = [line.strip() for line in entry.split('\n') if line.strip()]
                    
                    if len(lines) >= 1:
                        degree = ""
                        field = ""
                        institution = ""
                        date = ""
                        
                        # Cari pattern tahun
                        year_pattern = r'\b(19|20)\d{2}\b'
                        
                        for line in lines:
                            # Cari institution (biasanya mengandung kata kunci tertentu)
                            if re.search(r'(University|College|Institute|School|Academy)', line, re.IGNORECASE):
                                institution = line
                            # Cari degree (biasanya mengandung kata kunci degree)
                            elif re.search(r'(Bachelor|Master|Associate|Ph\.?D|B\.?S|M\.?S|B\.?A|M\.?A|MBA|Diploma)', line, re.IGNORECASE):
                                degree = line
                            # Cari tahun
                            elif re.search(year_pattern, line):
                                date = re.search(year_pattern, line).group()
                        
                        # Jika tidak ada degree yang jelas, ambil line pertama
                        if not degree and lines:
                            degree = lines[0]
                        
                        # Jika tidak ada institution yang jelas, cari dari lines
                        if not institution:
                            for line in lines:
                                if line != degree and not re.search(year_pattern, line):
                                    institution = line
                                    break
                        
                        # Cari field dari degree line
                        if degree:
                            # Extract field from degree line
                            field_patterns = [
                                r'(?:in|of)\s+([A-Za-z\s&,.-]+?)(?:\s+from|\s+at|\s*,|\s*$)',
                                r'(?:Bachelor|Master|Associate|Ph\.?D|B\.?S|M\.?S|B\.?A|M\.?A|MBA|Diploma).*?(?:in|of)\s+([A-Za-z\s&,.-]+)',
                            ]
                            
                            for pattern in field_patterns:
                                field_match = re.search(pattern, degree, re.IGNORECASE)
                                if field_match:
                                    field = field_match.group(1).strip()
                                    break
                        
                        # Clean up data
                        degree = degree[:80] if degree else "Degree"
                        field = field[:80] if field else "Field of Study"
                        institution = institution[:100] if institution else "Institution"
                        date = date if date else "Year not specified"
                        
                        edu_entry = {
                            "degree": degree,
                            "field": field,
                            "institution": institution,
                            "date": date
                        }
                        
                        # Avoid duplicates
                        if not any(edu.get('degree', '').lower() == degree.lower() and 
                                 edu.get('institution', '').lower() == institution.lower() 
                                 for edu in profile["education"]):
                            profile["education"].append(edu_entry)
                        
                        if len(profile["education"]) >= 4:
                            break
                            
            except Exception as e:
                print(f"Error parsing education section: {e}")

        # GPA EXTRACTION
        gpa_patterns = [
            r"(?i)(?:GPA|Grade\s+Point\s+Average)[:\s]*(\d+\.?\d*)",
            r"(\d+\.\d+)\s*/\s*4\.0",
            r"(?i)GPA[:\s]*(\d+\.\d+)"
        ]
        
        for pattern in gpa_patterns:
            try:
                gpa_matches = re.findall(pattern, text)
                for gpa in gpa_matches:
                    try:
                        gpa_val = float(gpa)
                        if 0.0 <= gpa_val <= 4.0:
                            profile["gpa"].append(str(gpa_val))
                    except ValueError:
                        continue
            except Exception as e:
                print(f"Error in GPA extraction: {e}")
                continue

        # CERTIFICATIONS EXTRACTION
        cert_patterns = [
            r"(?i)(?:Certifications?|Certificates?|Licenses?|Professional\s+Affiliations)\s*:?\s*\n(.*?)(?=\n\s*(?:[A-Z]{2,}|Education|Experience|Skills|\Z))",
            r"(?i)(Certified\s+[A-Za-z\s]+)",
            r"(?i)([A-Za-z\s]+Certificate)",
            r"(?i)([A-Za-z\s]+Certification)",
            r"(?i)(Licensed\s+[A-Za-z\s]+)"
        ]
        
        for pattern in cert_patterns:
            try:
                cert_matches = re.findall(pattern, text, re.DOTALL)
                for cert_text in cert_matches:
                    if isinstance(cert_text, tuple):
                        cert_text = cert_text[0] if cert_text else ""
                    
                    cert_list = re.split(r'[,\n•·▪▫\-]', cert_text)
                    certs = [cert.strip() for cert in cert_list 
                            if cert.strip() and len(cert.strip()) > 5 and len(cert.strip()) < 100]
                    profile["certifications"].extend(certs[:5])
            except Exception as e:
                print(f"Error in certifications extraction: {e}")
                continue

        # ACHIEVEMENTS/HIGHLIGHTS EXTRACTION
        highlights_patterns = [
            r"(?i)(?:Highlights|Accomplishments|Achievements|Key\s+Accomplishments)\s*:?\s*\n(.*?)(?=\n\s*(?:[A-Z]{2,}|Education|Experience|\Z))",
            r"(?i)(?:Awards?|Honors?|Recognition)\s*:?\s*\n(.*?)(?=\n\s*(?:[A-Z]{2,}|Education|Experience|\Z))"
        ]
        
        for pattern in highlights_patterns:
            try:
                highlights_match = re.search(pattern, text, re.DOTALL)
                if highlights_match:
                    highlights_text = highlights_match.group(1)
                    highlight_list = re.split(r'[,\n•·▪▫\-]', highlights_text)
                    for highlight in highlight_list:
                        cleaned = highlight.strip()
                        if cleaned and len(cleaned) > 15 and len(cleaned) < 200:
                            profile["achievements"].append(cleaned)
                    break
            except Exception as e:
                print(f"Error in highlights extraction: {e}")

    except Exception as e:
        print(f"General error in profile extraction: {e}")

    # Clean up and remove duplicates
    profile["skills"] = list(dict.fromkeys(profile["skills"]))[:20]
    profile["certifications"] = list(dict.fromkeys(profile["certifications"]))[:5]
    profile["achievements"] = list(dict.fromkeys(profile["achievements"]))[:5]
    
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
            print(f"  - {exp.get('title', 'N/A')} at {exp.get('company', 'N/A')} ({exp.get('start', '')} - {exp.get('end', '')})")
    
    if profile.get("education"):
        print(f"Education ({len(profile['education'])} entries):")
        for edu in profile['education']:
            print(f"  - {edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}")
    
    if profile.get("gpa"):
        print(f"GPA: {profile['gpa'][0]}")
    
    if profile.get("certifications"):
        print(f"Certifications ({len(profile['certifications'])}): {', '.join(profile['certifications'][:3])}...")