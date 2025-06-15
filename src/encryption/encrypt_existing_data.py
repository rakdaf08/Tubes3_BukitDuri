# encrypt_existing_data.py
import sys
import os
sys.path.append('.')

from src.db.db_connector import DatabaseManager
from config import ENCRYPTION_SETTINGS
from encryption_engine import encryption_engine

def encrypt_existing_database():
    print("=== ENCRYPTING EXISTING DATABASE ===")
    
    if not ENCRYPTION_SETTINGS.get('enabled', False):
        print("❌ Encryption is disabled in config.py")
        print("Please set ENCRYPTION_SETTINGS['enabled'] = True first!")
        return False
    
    # Connect to database
    db = DatabaseManager()
    if not db.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = db.connection.cursor(dictionary=True)
        fields_to_encrypt = ENCRYPTION_SETTINGS.get('encrypt_fields', [])
        
        print(f"Fields to encrypt: {fields_to_encrypt}")
        total_encrypted = 0
        
        # 1. Encrypt ApplicantProfile table
        print("\n=== ENCRYPTING ApplicantProfile TABLE ===")
        cursor.execute("SELECT * FROM ApplicantProfile")
        profiles = cursor.fetchall()
        
        print(f"Found {len(profiles)} profiles to encrypt")
        
        for profile in profiles:
            applicant_id = profile['applicant_id']
            updates = []
            values = []
            
            print(f"Processing ApplicantProfile ID {applicant_id}...")
            
            for field in fields_to_encrypt:
                if field in profile and profile[field]:
                    original_value = profile[field]
                    
                    # Check if already encrypted
                    is_hex = all(c in '0123456789abcdefABCDEF' for c in str(original_value))
                    is_long = len(str(original_value)) > 50
                    
                    if not (is_hex and is_long):  # Not encrypted yet
                        # Encrypt the value
                        encrypted_value = encryption_engine.encrypt(str(original_value))
                        updates.append(f"{field} = %s")
                        values.append(encrypted_value)
                        
                        print(f"  {field}: '{original_value}' -> ENCRYPTED ({len(encrypted_value)} chars)")
                    else:
                        print(f"  {field}: Already encrypted")
            
            if updates:
                # Update the record
                update_query = f"UPDATE ApplicantProfile SET {', '.join(updates)} WHERE applicant_id = %s"
                values.append(applicant_id)
                
                cursor.execute(update_query, values)
                total_encrypted += 1
                print(f"  ✓ Updated ApplicantProfile {applicant_id}")
            else:
                print(f"  ✓ No updates needed for ApplicantProfile {applicant_id}")
        
        # 2. Encrypt resumes table
        print("\n=== ENCRYPTING RESUMES TABLE ===")
        cursor.execute("""
            SELECT id, first_name, last_name, address, phone_number 
            FROM resumes 
            WHERE (first_name IS NOT NULL OR last_name IS NOT NULL 
                   OR address IS NOT NULL OR phone_number IS NOT NULL)
        """)
        resumes = cursor.fetchall()
        
        print(f"Found {len(resumes)} resumes with profile data to encrypt")
        
        for resume in resumes:
            resume_id = resume['id']
            updates = []
            values = []
            
            print(f"Processing resume ID {resume_id}...")
            
            for field in fields_to_encrypt:
                if field in resume and resume[field]:
                    original_value = resume[field]
                    
                    # Check if already encrypted
                    is_hex = all(c in '0123456789abcdefABCDEF' for c in str(original_value))
                    is_long = len(str(original_value)) > 50
                    
                    if not (is_hex and is_long):  # Not encrypted yet
                        # Encrypt the value
                        encrypted_value = encryption_engine.encrypt(str(original_value))
                        updates.append(f"{field} = %s")
                        values.append(encrypted_value)
                        
                        print(f"  {field}: '{original_value}' -> ENCRYPTED ({len(encrypted_value)} chars)")
                    else:
                        print(f"  {field}: Already encrypted")
            
            if updates:
                # Update the record
                update_query = f"UPDATE resumes SET {', '.join(updates)} WHERE id = %s"
                values.append(resume_id)
                
                cursor.execute(update_query, values)
                total_encrypted += 1
                print(f"  ✓ Updated resume {resume_id}")
            else:
                print(f"  ✓ No updates needed for resume {resume_id}")
        
        # Commit all changes
        db.connection.commit()
        print(f"\n✅ Encryption completed! Updated {total_encrypted} records total")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during encryption: {e}")
        db.connection.rollback()
        return False
    finally:
        db.disconnect()

def verify_encryption():
    """Verify that encryption was successful"""
    print("\n=== VERIFYING ENCRYPTION ===")
    
    db = DatabaseManager()
    if not db.connect():
        print("❌ Failed to connect to database")
        return
    
    try:
        cursor = db.connection.cursor(dictionary=True)
        fields_to_check = ENCRYPTION_SETTINGS.get('encrypt_fields', [])
        
        # Check ApplicantProfile
        print("\n--- ApplicantProfile Table ---")
        cursor.execute("SELECT applicant_id, first_name, last_name, address, phone_number FROM ApplicantProfile LIMIT 3")
        profiles = cursor.fetchall()
        
        for profile in profiles:
            print(f"Profile {profile['applicant_id']}:")
            for field in fields_to_check:
                if field in profile and profile[field]:
                    value = profile[field]
                    is_encrypted = len(str(value)) > 50 and all(c in '0123456789abcdefABCDEF' for c in str(value))
                    status = "🔒 ENCRYPTED" if is_encrypted else "🔓 PLAIN"
                    print(f"  {field}: {status}")
                    
                    # Try to decrypt if encrypted
                    if is_encrypted:
                        try:
                            decrypted = encryption_engine.decrypt(value)
                            print(f"    Decrypted: '{decrypted}'")
                        except:
                            print(f"    Decryption failed")
        
        # Check resumes
        print("\n--- Resumes Table ---")
        cursor.execute("SELECT id, first_name, last_name, address, phone_number FROM resumes WHERE first_name IS NOT NULL LIMIT 3")
        resumes = cursor.fetchall()
        
        for resume in resumes:
            print(f"Resume {resume['id']}:")
            for field in fields_to_check:
                if field in resume and resume[field]:
                    value = resume[field]
                    is_encrypted = len(str(value)) > 50 and all(c in '0123456789abcdefABCDEF' for c in str(value))
                    status = "🔒 ENCRYPTED" if is_encrypted else "🔓 PLAIN"
                    print(f"  {field}: {status}")
                    
                    # Try to decrypt if encrypted
                    if is_encrypted:
                        try:
                            decrypted = encryption_engine.decrypt(value)
                            print(f"    Decrypted: '{decrypted}'")
                        except:
                            print(f"    Decryption failed")
        
    finally:
        db.disconnect()

if __name__ == "__main__":
    # Confirm before proceeding
    response = input("This will encrypt all existing profile data in ALL tables. Continue? (y/N): ")
    if response.lower() == 'y':
        success = encrypt_existing_database()
        if success:
            verify_encryption()
    else:
        print("Encryption cancelled.")