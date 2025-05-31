import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from db.db_connector import DatabaseManager
from core.extractor import extract_text_from_pdf, extract_profile_data

def setup_database():
    """Setup database and load initial data"""
    print("=== Setting up Resume Search Database ===")
    
    # 123
    mysql_password = input("Enter MySQL root password: ")
    
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': mysql_password,
        'database': 'Tubes3Stima'
    }
    
    db = DatabaseManager(**db_config)
    
    print("Creating database and tables...")
    if not db.create_database_and_tables():
        print("Failed to create database/tables")
        return False
    
    print("Connecting to database...")
    if not db.connect():
        print("Failed to connect to database")
        return False
    
    print("Loading resume data from PDF files...")
    load_resume_data(db)
    
    print("Testing search functionality...")
    test_search(db)
    
    db.disconnect()
    print("Database setup completed successfully!")
    return True

def load_resume_data(db: DatabaseManager):
    """Load resume data from PDF files into database"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_dir = os.path.join(base_dir, "data", "pdf")
    
    print(f"Looking for PDF files in: {pdf_dir}")
    
    if not os.path.exists(pdf_dir):
        print(f"PDF directory not found: {pdf_dir}")
        print("Please download and organize the dataset first:")
        print("1. Download from: https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset")
        print("2. Extract to data/pdf/ folder")
        return
    
    categories = [d for d in os.listdir(pdf_dir) if os.path.isdir(os.path.join(pdf_dir, d))]
    if not categories:
        print("No category folders found in PDF directory")
        return
    
    print(f"Found {len(categories)} categories: {categories[:5]}...")
    
    loaded_count = 0
    error_count = 0
    
    for category in categories:
        category_path = os.path.join(pdf_dir, category)
        
        print(f"\nProcessing category: {category}")
        
        pdf_files = [f for f in os.listdir(category_path) if f.endswith('.pdf')]
        print(f"Found {len(pdf_files)} PDF files in {category}")
        
        for filename in pdf_files[:10]: 
            pdf_path = os.path.join(category_path, filename)
            
            try:
                print(f"Processing: {filename}")
                
                extracted_text = extract_text_from_pdf(pdf_path)
                if not extracted_text:
                    print(f"  - No text extracted from {filename}")
                    continue
                
                print(f"  - Extracted {len(extracted_text)} characters")
                
                profile = extract_profile_data(extracted_text)
                
                skills = ", ".join(profile.get('skills', []))
                
                experience_list = []
                for exp in profile.get('experience', []):
                    exp_text = f"{exp.get('title', '')} ({exp.get('start', '')} - {exp.get('end', '')}): {exp.get('description', '')}"
                    experience_list.append(exp_text)
                experience = " | ".join(experience_list)
                
                education_list = []
                for edu in profile.get('education', []):
                    edu_text = f"{edu.get('degree', '')} in {edu.get('field', '')} ({edu.get('date', '')})"
                    education_list.append(edu_text)
                education = " | ".join(education_list)
                
                gpa = float(profile['gpa'][0]) if profile.get('gpa') and profile['gpa'] else None
                certifications = ", ".join(profile.get('certifications', []))
                
                resume_id = db.insert_resume(
                    filename=filename,
                    category=category,
                    file_path=pdf_path,
                    extracted_text=extracted_text[:50000],
                    skills=skills,
                    experience=experience,
                    education=education,
                    gpa=gpa,
                    certifications=certifications
                )
                
                if resume_id > 0:
                    loaded_count += 1
                    print(f"  - Successfully loaded to database (ID: {resume_id})")
                else:
                    error_count += 1
                    print(f"  - Failed to insert into database")
                        
            except Exception as e:
                error_count += 1
                print(f"  - Error processing {filename}: {e}")
                continue
    
    print(f"\n=== Loading Summary ===")
    print(f"Successfully loaded: {loaded_count} resumes")
    print(f"Errors: {error_count}")

def test_search(db: DatabaseManager):
    """Test basic search functionality"""
    print("\n=== Testing Search Functionality ===")

    stats = db.get_statistics()
    print(f"Total resumes in database: {stats.get('total_resumes', 0)}")
    
    if stats.get('total_resumes', 0) == 0:
        print("No data to test - skipping search tests")
        return
    # test
    print("\nTest 1: General search for 'experience'...")
    results = db.search_resumes_by_criteria("experience")
    print(f"Found {len(results)} resumes mentioning 'experience'")
    
    # test
    categories = db.get_all_categories()
    if categories:
        print(f"\nTest 2: Searching in {categories[0]} category...")
        results = db.search_resumes_by_criteria("", category=categories[0])
        print(f"Found {len(results)} resumes in {categories[0]} category")

    print(f"\nCategories in database:")
    for cat_stat in stats.get('resumes_by_category', []):
        print(f"  {cat_stat['category']}: {cat_stat['count']} resumes")

if __name__ == "__main__":
    setup_database()