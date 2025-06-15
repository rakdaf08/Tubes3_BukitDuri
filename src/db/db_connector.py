import mysql.connector
from mysql.connector import Error
import logging
import sys, os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import DATABASE_CONFIG

class DatabaseManager:
    def __init__(self, host=None, user=None, password=None, database=None):
        """Initialize database manager with connection parameters"""
        # Use global config as default, allow override
        self.host = host or DATABASE_CONFIG['host']
        self.user = user or DATABASE_CONFIG['user'] 
        self.password = password or DATABASE_CONFIG['password'] 
        self.database = database or DATABASE_CONFIG['database']
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=True
            )
            print(f"Connected to MySQL database: {self.database}")
            return True
        except Error as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")
    
    def create_database_and_tables(self):
        """Create database and required tables"""
        try:
            temp_conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = temp_conn.cursor()
            
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.execute(f"USE {self.database}")            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resumes (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    file_path VARCHAR(500) NOT NULL,
                    extracted_text LONGTEXT,
                    skills TEXT,
                    experience TEXT,
                    education TEXT,
                    gpa DECIMAL(3,2),
                    certifications TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_category (category),
                    INDEX idx_filename (filename),
                    INDEX idx_skills (skills(255)),
                    FULLTEXT(extracted_text, skills, experience, education)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    resume_id INT,
                    search_pattern VARCHAR(500) NOT NULL,
                    algorithm_used VARCHAR(50) NOT NULL,
                    matches_found INT DEFAULT 0,
                    match_positions TEXT,
                    similarity_score DECIMAL(5,2),
                    search_time_ms DECIMAL(10,3),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
                    INDEX idx_pattern (search_pattern),
                    INDEX idx_algorithm (algorithm_used)
                )
            """)
            
            temp_conn.commit()
            temp_conn.close()
            print("Database and tables created successfully")
            return True
            
        except mysql.connector.Error as err:
            print(f"Error creating database/tables: {err}")
            return False
    
    def insert_resume(self, filename: str, category: str, file_path: str, 
                     extracted_text: str = "", skills: str = "", experience: str = "",
                     education: str = "", gpa: float = None, certifications: str = "") -> int:
        """Insert resume data into database"""
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO resumes (filename, category, file_path, extracted_text, 
                                   skills, experience, education, gpa, certifications)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (filename, category, file_path, extracted_text, skills, 
                     experience, education, gpa, certifications)
            
            cursor.execute(query, values)
            self.connection.commit()
            resume_id = cursor.lastrowid
            cursor.close()
            return resume_id
            
        except mysql.connector.Error as err:
            print(f"Error inserting resume: {err}")
            return -1
    
    def search_resumes_by_criteria(self, search_text: str, category: str = None, 
                                skill_filter: str = None, experience_filter: str = None) -> List[Dict]:
        """Enhanced search with multiple criteria"""
        try:
            cursor = self.connection.cursor(dictionary=True)            
            conditions = []
            values = []
            
            if search_text:
                conditions.append("""
                    (extracted_text LIKE %s OR 
                    skills LIKE %s OR 
                    experience LIKE %s OR 
                    education LIKE %s OR
                    filename LIKE %s)
                """)
                search_pattern = f"%{search_text}%"
                values.extend([search_pattern] * 5)
            
            if category:
                conditions.append("category = %s")
                values.append(category)
                
            if skill_filter:
                conditions.append("skills LIKE %s")
                values.append(f"%{skill_filter}%")
                
            if experience_filter:
                conditions.append("experience LIKE %s")
                values.append(f"%{experience_filter}%")
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            query = f"""
                SELECT *, 
                MATCH(extracted_text, skills, experience, education) 
                AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance_score
                FROM resumes 
                WHERE {where_clause}
                ORDER BY relevance_score DESC, created_at DESC
            """
            
            final_values = [search_text or ""] + values
            
            cursor.execute(query, final_values)
            results = cursor.fetchall()
            cursor.close()
            return results
            
        except mysql.connector.Error as err:
            print(f"Error searching resumes: {err}")
            return []
        
    def get_resume_by_id(self, resume_id: int) -> Optional[Dict]:
        """Get specific resume by ID"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM resumes WHERE id = %s"
            cursor.execute(query, (resume_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except mysql.connector.Error as err:
            print(f"Error fetching resume: {err}")
            return None
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        try:
            cursor = self.connection.cursor()
            query = "SELECT DISTINCT category FROM resumes ORDER BY category"
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return [row[0] for row in results]
        except mysql.connector.Error as err:
            print(f"Error fetching categories: {err}")
            return []
        
    def get_all_resumes(self) -> List[Dict]:
        """Get all resumes from database"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT id, filename, category, file_path, extracted_text as content, 
                    skills, experience, education, gpa, certifications, created_at 
                FROM resumes 
                ORDER BY created_at DESC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
        except mysql.connector.Error as err:
            print(f"Error fetching all resumes: {err}")
            return []
    
    def insert_search_result(self, resume_id: int, search_pattern: str, algorithm_used: str,
                           matches_found: int, match_positions: str = "", 
                           similarity_score: float = None, search_time_ms: float = 0) -> int:
        """Insert search result into database"""
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO search_results (resume_id, search_pattern, algorithm_used,
                                          matches_found, match_positions, similarity_score, search_time_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (resume_id, search_pattern, algorithm_used, matches_found, 
                     match_positions, similarity_score, search_time_ms)
            
            cursor.execute(query, values)
            self.connection.commit()
            result_id = cursor.lastrowid
            cursor.close()
            return result_id
            
        except mysql.connector.Error as err:
            print(f"Error inserting search result: {err}")
            return -1
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            stats = {}
            
            # total resume
            cursor.execute("SELECT COUNT(*) as total FROM resumes")
            stats['total_resumes'] = cursor.fetchone()['total']
            
            # category
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM resumes 
                GROUP BY category 
                ORDER BY count DESC
            """)
            stats['resumes_by_category'] = cursor.fetchall()
            
            # total search
            cursor.execute("SELECT COUNT(*) as total FROM search_results")
            stats['total_searches'] = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT search_pattern, COUNT(*) as count 
                FROM search_results 
                GROUP BY search_pattern 
                ORDER BY count DESC 
                LIMIT 10
            """)
            stats['popular_searches'] = cursor.fetchall()
            
            cursor.close()
            return stats
            
        except mysql.connector.Error as err:
            print(f"Error fetching statistics: {err}")
            return {}
        
    def insert_resume_with_profile(self, filename, category, file_path, extracted_text, 
                                skills=None, experience=None, education=None, 
                                gpa=None, certifications=None,
                                # Profile data
                                applicant_id=None, first_name=None, last_name=None,
                                date_of_birth=None, address=None, phone_number=None,
                                application_role=None):
        """Insert resume with complete profile information"""
        try:
            cursor = self.connection.cursor()
            
            insert_query = """
            INSERT INTO resumes (
                filename, category, file_path, extracted_text, skills, 
                experience, education, gpa, certifications,
                applicant_id, first_name, last_name, date_of_birth, 
                address, phone_number, application_role, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            cursor.execute(insert_query, (
                filename, category, file_path, extracted_text, skills,
                experience, education, gpa, certifications,
                applicant_id, first_name, last_name, date_of_birth,
                address, phone_number, application_role
            ))
            
            self.connection.commit()
            return cursor.lastrowid
            
        except Exception as e:
            print(f"Error inserting resume with profile: {e}")
            self.connection.rollback()
            return -1
    def search_resumes_with_profile(self, keyword="", category=None, skill_filter=None, 
                                experience_filter=None, limit=50):
        """Search resumes and return with profile information"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            base_query = """
            SELECT id, filename, category, first_name, last_name, date_of_birth,
                address, phone_number, application_role, skills, experience,
                education, gpa, certifications, created_at, extracted_text
            FROM resumes
            WHERE 1=1
            """
            
            params = []
            
            if keyword:
                base_query += " AND (extracted_text LIKE %s OR skills LIKE %s OR experience LIKE %s)"
                keyword_param = f"%{keyword}%"
                params.extend([keyword_param, keyword_param, keyword_param])
            
            if category:
                base_query += " AND category = %s"
                params.append(category)
                
            if skill_filter:
                base_query += " AND skills LIKE %s"
                params.append(f"%{skill_filter}%")
                
            if experience_filter:
                base_query += " AND experience LIKE %s"
                params.append(f"%{experience_filter}%")
            
            base_query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            cursor.execute(base_query, params)
            results = cursor.fetchall()
            
            return results
            
        except Exception as e:
            print(f"Error searching resumes with profile: {e}")
            return []

    def get_all_resumes(self):
        """Get all resumes with profile data from ApplicationDetail matching"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Join resumes with profile data through cv_path matching
            query = """
            SELECT r.*, 
                ap.first_name, ap.last_name, ap.date_of_birth, 
                ap.address, ap.phone_number,
                ad.application_role
            FROM resumes r
            LEFT JOIN ApplicationDetail ad ON (
                ad.cv_path LIKE CONCAT('%', r.filename) OR
                ad.cv_path LIKE CONCAT('%', r.category, '/', r.filename) OR
                SUBSTRING_INDEX(ad.cv_path, '/', -1) = r.filename
            )
            LEFT JOIN ApplicantProfile ap ON ad.applicant_id = ap.applicant_id
            ORDER BY r.id
            """
            
            cursor.execute(query)
            resumes = cursor.fetchall()
            
            print(f"DEBUG - Found {len(resumes)} resumes with profile matching")
            
            # Debug first few results
            for i, resume in enumerate(resumes[:3]):
                print(f"DEBUG - Resume {i+1}: {resume['filename']} -> {resume.get('first_name', 'No name')} {resume.get('last_name', '')}")
            
            return resumes
            
        except Exception as e:
            print(f"Error getting all resumes: {e}")
            return []

    def get_resume_by_id(self, resume_id):
        """Get resume by ID with profile data"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Join with profile data
            query = """
            SELECT r.*, 
                ap.first_name, ap.last_name, ap.date_of_birth, 
                ap.address, ap.phone_number,
                ad.application_role
            FROM resumes r
            LEFT JOIN ApplicationDetail ad ON (
                ad.cv_path LIKE CONCAT('%', r.filename) OR
                ad.cv_path LIKE CONCAT('%', r.category, '/', r.filename) OR
                SUBSTRING_INDEX(ad.cv_path, '/', -1) = r.filename
            )
            LEFT JOIN ApplicantProfile ap ON ad.applicant_id = ap.applicant_id
            WHERE r.id = %s
            """
            
            cursor.execute(query, (resume_id,))
            resume = cursor.fetchone()
            
            if resume:
                print(f"DEBUG - Resume {resume_id}: {resume['filename']} -> {resume.get('first_name', 'No name')} {resume.get('last_name', '')}")
            
            return resume
            
        except Exception as e:
            print(f"Error getting resume by ID {resume_id}: {e}")
            return None
    
def get_connection():
    """Legacy function - use DatabaseManager class instead"""
    db = DatabaseManager()
    if db.connect():
        return db.connection
    return None