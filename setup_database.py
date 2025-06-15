import os
import sys
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.dirname(__file__))
from config import DATABASE_CONFIG

from db.db_connector import DatabaseManager
from core.extractor import extract_text_from_pdf, extract_profile_data

def setup_database():
    """Setup database and load initial data"""
    print("=== Setting up Resume Search Database ===")

    db = DatabaseManager(**DATABASE_CONFIG)
    
    print("Creating database and tables...")
    if not db.create_database_and_tables():
        print("Failed to create database/tables")
        return False
    
    print("Connecting to database...")
    if not db.connect():
        print("Failed to connect to database")
        return False
    
    # Run seeding SQL file
    print("Running seeding SQL file...")
    run_seeding_sql(DATABASE_CONFIG)
    
    # Add profile columns to resumes table
    print("Adding profile columns to resumes table...")
    add_profile_columns_to_resumes(db)
    
    print("Loading resume data from PDF files...")
    load_resume_data(db)
    
    db.disconnect()
    print("Database setup completed successfully!")
    return True

def run_seeding_sql(db_config):
    try:
        seeding_file = os.path.join(root_dir, 'tubes3_seeding.sql')
        if os.path.exists(seeding_file):
            print(f"Found seeding file: {seeding_file}")
            # Run MySQL command to execute the SQL file
            cmd = [
                'mysql',
                '-h', db_config['host'],
                '-u', db_config['user'],
                db_config['database']
            ]
            
            # Add password if not empty
            if db_config['password']:
                cmd.extend(['-p' + db_config['password']])
            
            # Execute the SQL file
            with open(seeding_file, 'r', encoding='utf-8') as f:
                result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Seeding SQL executed successfully")
            else:
                print(f"Error executing seeding SQL: {result.stderr}")
            return True
        else:
            print("No seeding file found, skipping...")
            return True
        
    except Exception as e:
        print(f"Seeding error: {e}")
        return False

def add_profile_columns_to_resumes(db: DatabaseManager):
    """Add profile columns to existing resumes table"""
    try:
        cursor = db.connection.cursor()
        
        # Add new columns to existing resumes table
        alter_resumes = """
        ALTER TABLE resumes 
        ADD COLUMN IF NOT EXISTS applicant_id INT DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS first_name VARCHAR(50) DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS last_name VARCHAR(50) DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS date_of_birth DATE DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS address VARCHAR(255) DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20) DEFAULT NULL,
        ADD COLUMN IF NOT EXISTS application_role VARCHAR(100) DEFAULT NULL
        """
        
        try:
            cursor.execute(alter_resumes)
            print("Resumes table updated with profile columns")
        except Exception as e:
            # Try adding columns one by one if batch fails
            columns_to_add = [
                ('applicant_id', 'INT DEFAULT NULL'),
                ('first_name', 'VARCHAR(50) DEFAULT NULL'),
                ('last_name', 'VARCHAR(50) DEFAULT NULL'),
                ('date_of_birth', 'DATE DEFAULT NULL'),
                ('address', 'VARCHAR(255) DEFAULT NULL'),
                ('phone_number', 'VARCHAR(20) DEFAULT NULL'),
                ('application_role', 'VARCHAR(100) DEFAULT NULL')
            ]
            
            for col_name, col_def in columns_to_add:
                try:
                    cursor.execute(f"ALTER TABLE resumes ADD COLUMN {col_name} {col_def}")
                    print(f"✓ Added column {col_name}")
                except Exception as col_error:
                    if "Duplicate column name" not in str(col_error):
                        print(f"Warning: Could not add column {col_name}: {col_error}")
        
        db.connection.commit()
        
    except Exception as e:
        print(f"Error adding profile columns: {e}")
        db.connection.rollback()

def load_resume_data(db: DatabaseManager):
    """Load resume data from PDF files into database with profile integration"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_dir = os.path.join(base_dir, "data", "pdf")
    
    print(f"Looking for PDF files in: {pdf_dir}")
    
    if not os.path.exists(pdf_dir):
        print(f"PDF directory not found: {pdf_dir}")
        print("Please download and organize the dataset first")
        return
    
    # Get seeding data for profile matching
    cursor = db.connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT ad.detail_id, ad.applicant_id, ad.application_role, ad.cv_path,
               ap.first_name, ap.last_name, ap.date_of_birth, ap.address, ap.phone_number
        FROM ApplicationDetail ad
        JOIN ApplicantProfile ap ON ad.applicant_id = ap.applicant_id
    """)
    seeding_profiles = {row['cv_path']: row for row in cursor.fetchall()}
    
    print(f"Found {len(seeding_profiles)} seeding profiles for matching")
    
    loaded_count = 0
    error_count = 0
    total_files = 0
    
    # Count total files
    for category in os.listdir(pdf_dir):
        category_path = os.path.join(pdf_dir, category)
        if os.path.isdir(category_path):
            pdf_files = [f for f in os.listdir(category_path) if f.endswith('.pdf')]
            total_files += len(pdf_files)
    
    print(f"Total PDF files found: {total_files}")

    limit = None
    for category in os.listdir(pdf_dir):
        category_path = os.path.join(pdf_dir, category)
        if not os.path.isdir(category_path):
            continue
            
        print(f"\nProcessing category: {category}")
        
        pdf_files = [f for f in os.listdir(category_path) if f.endswith('.pdf')]
        print(f"Found {len(pdf_files)} PDF files in {category}")
        
        files_to_process = pdf_files if limit is None else pdf_files[:limit]
        if limit and len(pdf_files) > limit:
            print(f"Processing first {limit} files only...")
        
        for idx, filename in enumerate(files_to_process, 1):
            pdf_path = os.path.join(category_path, filename)
            
            try:
                print(f"Processing ({idx}/{len(files_to_process)}): {filename}")
                
                extracted_text = extract_text_from_pdf(pdf_path)
                if not extracted_text:
                    print(f"No text extracted from {filename}")
                    error_count += 1
                    continue
                
                print(f"Extracted {len(extracted_text)} characters")
                
                profile = extract_profile_data(extracted_text)
                
                skills = ", ".join(profile.get('skills', []))[:2000] 
                
                experience_list = []
                for exp in profile.get('experience', []):
                    exp_text = f"{exp.get('title', '')} at {exp.get('company', '')} ({exp.get('period', '')})"
                    experience_list.append(exp_text)
                experience = " | ".join(experience_list)[:2000] 
                
                education_list = []
                for edu in profile.get('education', []):
                    edu_text = f"{edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}"
                    education_list.append(edu_text)
                education = " | ".join(education_list)[:1000]  
                
                gpa = None
                if profile.get('gpa'):
                    try:
                        gpa = float(profile['gpa'][0])
                    except:
                        gpa = None
                        
                certifications = ", ".join(profile.get('certifications', []))[:1000]
                
                # Check if this file has seeding profile data
                relative_path = f"data/pdf/{category}/{filename}"
                seeding_data = seeding_profiles.get(relative_path)
                
                if seeding_data:
                    # Use seeding profile data
                    resume_id = db.insert_resume_with_profile(
                        filename=filename,
                        category=category,
                        file_path=pdf_path,
                        extracted_text=extracted_text[:100000],
                        skills=skills,
                        experience=experience,
                        education=education,
                        gpa=gpa,
                        certifications=certifications,
                        applicant_id=seeding_data['applicant_id'],
                        first_name=seeding_data['first_name'],
                        last_name=seeding_data['last_name'],
                        date_of_birth=seeding_data['date_of_birth'],
                        address=seeding_data['address'],
                        phone_number=seeding_data['phone_number'],
                        application_role=seeding_data['application_role']
                    )
                    print(f"✓ Inserted with profile data: {seeding_data['first_name']} {seeding_data['last_name']}")
                else:
                    # Regular insert without profile data
                    resume_id = db.insert_resume(
                        filename=filename,
                        category=category,
                        file_path=pdf_path,
                        extracted_text=extracted_text[:100000],
                        skills=skills,
                        experience=experience,
                        education=education,
                        gpa=gpa,
                        certifications=certifications
                    )
                    print(f"✓ Inserted without profile data")
                
                if resume_id > 0:
                    loaded_count += 1
                else:
                    print(f"✗ Failed to insert {filename}")
                    error_count += 1
                        
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                error_count += 1
                continue
            
            if idx % 3 == 0:  # Show progress every 3 files
                print(f"Progress: {idx}/{len(files_to_process)} files in {category}")
    
    print(f"\nFinal Summary:")
    print(f"Successfully loaded: {loaded_count} resumes")
    print(f"Errors: {error_count} files")
    print(f"Success rate: {(loaded_count/(loaded_count+error_count)*100):.1f}%" if (loaded_count+error_count) > 0 else "No files processed")

if __name__ == "__main__":
    setup_database()