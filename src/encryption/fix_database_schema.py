# fix_database_schema.py
import sys
import os
sys.path.append('.')

from src.db.db_connector import DatabaseManager

def fix_database_schema():
    print("=== FIXING DATABASE SCHEMA FOR ENCRYPTION ===")
    
    db = DatabaseManager()
    if not db.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = db.connection.cursor()
        
        # Alter ApplicantProfile table - perbesar kolom untuk encrypted data
        alter_queries = [
            "ALTER TABLE ApplicantProfile MODIFY first_name VARCHAR(1000)",
            "ALTER TABLE ApplicantProfile MODIFY last_name VARCHAR(1000)", 
            "ALTER TABLE ApplicantProfile MODIFY address TEXT",
            "ALTER TABLE ApplicantProfile MODIFY phone_number VARCHAR(500)",
            
            # Alter resumes table juga
            "ALTER TABLE resumes MODIFY first_name VARCHAR(1000)",
            "ALTER TABLE resumes MODIFY last_name VARCHAR(1000)",
            "ALTER TABLE resumes MODIFY address TEXT", 
            "ALTER TABLE resumes MODIFY phone_number VARCHAR(500)"
        ]
        
        print("Modifying database schema...")
        for query in alter_queries:
            print(f"Executing: {query}")
            cursor.execute(query)
        
        db.connection.commit()
        print("✅ Database schema updated successfully!")
        
        # Show new schema
        cursor.execute("DESCRIBE ApplicantProfile")
        print("\nApplicantProfile schema:")
        for row in cursor.fetchall():
            if row[0] in ['first_name', 'last_name', 'address', 'phone_number']:
                print(f"  {row[0]}: {row[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")
        return False
    finally:
        db.disconnect()

if __name__ == "__main__":
    fix_database_schema()