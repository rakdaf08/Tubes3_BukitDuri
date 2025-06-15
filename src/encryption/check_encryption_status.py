# check_encryption_status.py
import sys
import os
sys.path.append('.')

from src.db.db_connector import DatabaseManager
from config import ENCRYPTION_SETTINGS

def check_current_encryption_status():
    print("=== CHECKING DATABASE ENCRYPTION STATUS ===")
    
    # Connect to database
    db = DatabaseManager()
    if not db.connect():
        print("❌ Failed to connect to database")
        return False
    
    try:
        cursor = db.connection.cursor(dictionary=True)
        
        # Get sample data
        query = """
        SELECT id, filename, first_name, last_name, address, phone_number 
        FROM resumes 
        WHERE first_name IS NOT NULL OR last_name IS NOT NULL 
        LIMIT 5
        """
        
        cursor.execute(query)
        resumes = cursor.fetchall()
        
        print(f"Encryption enabled in config: {ENCRYPTION_SETTINGS.get('enabled', False)}")
        print(f"Fields to encrypt: {ENCRYPTION_SETTINGS.get('encrypt_fields', [])}")
        print(f"Found {len(resumes)} resumes with name data\n")
        
        encrypted_count = 0
        plain_count = 0
        
        for resume in resumes:
            print(f"--- Resume ID: {resume['id']} ({resume['filename']}) ---")
            
            # Check sensitive fields
            fields_to_check = ['first_name', 'last_name', 'address', 'phone_number']
            
            for field in fields_to_check:
                value = resume.get(field)
                if value:
                    # Check if looks encrypted (hex string > 50 chars)
                    is_hex = all(c in '0123456789abcdefABCDEF' for c in str(value))
                    is_long = len(str(value)) > 50
                    
                    if is_hex and is_long:
                        print(f"  {field}: 🔒 ENCRYPTED ({len(value)} chars)")
                        encrypted_count += 1
                        
                        # Try decrypt for verification
                        try:
                            from encryption_engine import encryption_engine
                            decrypted = encryption_engine.decrypt(value)
                            print(f"  Decrypted: '{decrypted}'")
                        except Exception as e:
                            print(f"  ❌ Decrypt failed: {e}")
                    else:
                        print(f"  {field}: 🔓 PLAIN TEXT - '{value}'")
                        plain_count += 1
                else:
                    print(f"  {field}: None")
            print()
        
        print(f"Summary: {encrypted_count} encrypted fields, {plain_count} plain text fields")
        
        if encrypted_count > 0 and plain_count == 0:
            print("✅ Database is FULLY ENCRYPTED")
            return True
        elif encrypted_count == 0 and plain_count > 0:
            print("⚠️ Database is NOT ENCRYPTED")
            return False
        else:
            print("🔄 Database is PARTIALLY ENCRYPTED")
            return False
            
    finally:
        db.disconnect()

if __name__ == "__main__":
    check_current_encryption_status()