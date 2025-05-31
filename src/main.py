import os
import time
import getpass
from core.extractor import extract_text_from_pdf, extract_profile_data, print_profile
from core.matcher import kmp_search, bm_search, fuzzy_search, ac_search
from db.db_connector import DatabaseManager

MYSQL_PASSWORD = None

def get_mysql_password():
    """Get MySQL password from user"""
    global MYSQL_PASSWORD
    if MYSQL_PASSWORD is None:
        MYSQL_PASSWORD = getpass.getpass("Enter MySQL root password: ") #123
    return MYSQL_PASSWORD

def read_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Gagal membaca file {file_path}: {e}")
        return ""

def database_search_demo(db: DatabaseManager):
    """Demo pencarian menggunakan database"""
    print("\n=== Database Search Demo ===")
    print("1. Search by keyword")
    print("2. Search by category")
    print("3. Search by skill")
    print("4. Advanced search")
    print("5. View statistics")
    
    choice = input("Pilih opsi (1-5): ")
    
    if choice == "1":
        keyword = input("Masukkan keyword: ")
        start_time = time.time()
        results = db.search_resumes_by_criteria(keyword)
        search_time = (time.time() - start_time) * 1000
        
        print(f"\nDitemukan {len(results)} hasil dalam {search_time:.2f} ms:")
        for i, resume in enumerate(results, 1):
            print(f"{i}. {resume['filename']} ({resume['category']})")
            if resume.get('relevance_score', 0) > 0:
                print(f"   Relevance: {resume['relevance_score']:.2f}")
    
    elif choice == "2":
        categories = db.get_all_categories()
        print("Available categories:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat}")
        
        try:
            cat_choice = int(input("Pilih kategori (nomor): ")) - 1
            if 0 <= cat_choice < len(categories):
                category = categories[cat_choice]
                results = db.search_resumes_by_criteria("", category=category)
                print(f"\nDitemukan {len(results)} resume dalam kategori {category}:")
                for i, resume in enumerate(results, 1):
                    print(f"{i}. {resume['filename']}")
        except (ValueError, IndexError):
            print("Pilihan tidak valid")
    
    elif choice == "3":
        skill = input("Masukkan skill yang dicari: ")
        results = db.search_resumes_by_criteria("", skill_filter=skill)
        print(f"\nDitemukan {len(results)} resume dengan skill '{skill}':")
        for i, resume in enumerate(results, 1):
            print(f"{i}. {resume['filename']} ({resume['category']})")
    
    elif choice == "4":
        keyword = input("Keyword (opsional): ") or None
        category = input("Category (opsional): ") or None
        skill = input("Skill (opsional): ") or None
        experience = input("Experience keyword (opsional): ") or None
        
        results = db.search_resumes_by_criteria(
            keyword, category=category, 
            skill_filter=skill, experience_filter=experience
        )
        print(f"\nDitemukan {len(results)} hasil:")
        for i, resume in enumerate(results, 1):
            print(f"{i}. {resume['filename']} ({resume['category']})")
    
    elif choice == "5":
        stats = db.get_statistics()
        print(f"\n=== Database Statistics ===")
        print(f"Total resumes: {stats.get('total_resumes', 0)}")
        print(f"Total searches: {stats.get('total_searches', 0)}")
        
        print(f"\nResumes by category:")
        for cat_stat in stats.get('resumes_by_category', []):
            print(f"  {cat_stat['category']}: {cat_stat['count']}")

def string_matching_demo():
    """Demo algoritma string matching pada file"""
    print("\n=== String Matching Demo ===")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    string_dir = os.path.join(base_dir, "data", "string")
    if not os.path.exists(string_dir):
        print("Data string directory not found. Please run setup first.")
        return
    
    string_files = []
    for root, dirs, files in os.walk(string_dir):
        for file in files:
            if file.endswith('_string.txt'):
                rel_path = os.path.relpath(os.path.join(root, file), string_dir)
                string_files.append(rel_path)
    
    if not string_files:
        print("No processed string files found.")
        return
    
    pattern = input("Masukkan kata yang ingin dicari: ")
    print("Pilih algoritma:")
    print("1. KMP")
    print("2. Boyer-Moore") 
    print("3. Aho-Corasick (multiple patterns)")
    print("4. Fuzzy Search")
    
    method = int(input("Pilih metode (1-4): "))
    much = int(input("Jumlah hasil yang ingin ditampilkan: "))
    
    count = 0
    total_time = 0
    
    for string_file in string_files[:much*2]:  
        if count >= much:
            break
            
        file_path = os.path.join(string_dir, string_file)
        text = read_file(file_path)
        if not text:
            continue
            
        display_name = string_file.replace('_string.txt', '')
        
        if method == 1:  # KMP
            start_time = time.time()
            results = kmp_search(text, pattern)
            search_time = (time.time() - start_time) * 1000
            total_time += search_time
            
            if results:
                print(f"\nKMP Search results in {display_name}:")
                print(f"Pattern ditemukan di posisi: {results}")
                print(f"Total kemunculan: {len(results)}")
                count += 1
                
        elif method == 2:  # Boyer-Moore
            start_time = time.time()
            results = bm_search(text, pattern)
            search_time = (time.time() - start_time) * 1000
            total_time += search_time
            
            if results:
                print(f"\nBoyer-Moore Search results in {display_name}:")
                print(f"Pattern ditemukan di posisi: {results}")
                print(f"Total kemunculan: {len(results)}")
                count += 1
                
        elif method == 3:  # Aho-Corasick
            patterns = pattern.split(',')
            patterns = [p.strip() for p in patterns]
            
            start_time = time.time()
            results = ac_search(text, patterns)
            search_time = (time.time() - start_time) * 1000
            total_time += search_time
            
            if results:
                print(f"\nAho-Corasick Search results in {display_name}:")
                pattern_results = {}
                for pos, pat in results:
                    if pat not in pattern_results:
                        pattern_results[pat] = []
                    pattern_results[pat].append(pos)
                
                for pat, positions in pattern_results.items():
                    print(f"Pattern '{pat}' ditemukan di posisi: {positions}")
                print(f"Total kemunculan: {len(results)}")
                count += 1
                
        elif method == 4:  # Fuzzy Search
            start_time = time.time()
            results = fuzzy_search(text, pattern)
            search_time = (time.time() - start_time) * 1000
            total_time += search_time
            
            if results:
                print(f"\nFuzzy Search results in {display_name}:")
                for pos, word, score in results:
                    print(f"Match: '{word}' at position {pos} (similarity: {score}%)")
                count += 1
    
    if count == 0:
        print("Tidak ada hasil ditemukan dengan algoritma yang dipilih.")
    
    print(f"\nTotal waktu pencarian: {total_time:.2f} ms")
    if count > 0:
        print(f"Rata-rata waktu per file: {total_time/count:.2f} ms")

def main():
    print("=== Resume Search System ===")
    print("1. Database Search (Recommended)")
    print("2. String Matching Demo")
    print("3. Setup Database")
    print("4. Exit")
    
    while True:
        choice = input("\nPilih opsi (1-4): ")
        
        if choice == "1":
            # Database search
            password = get_mysql_password()
            db = DatabaseManager(password=password)
            if db.connect():
                database_search_demo(db)
                db.disconnect()
            else:
                print("Gagal koneksi database. Periksa password atau jalankan setup terlebih dahulu.")
                # Reset password untuk retry
                global MYSQL_PASSWORD
                MYSQL_PASSWORD = None
                
        elif choice == "2":
            # String matching demo
            string_matching_demo()
            
        elif choice == "3":
            # Setup database
            print("Running database setup...")
            os.system("python setup_database.py")
            
        elif choice == "4":
            print("Terima kasih!")
            break
            
        else:
            print("Pilihan tidak valid!")

if __name__ == "__main__":
    main()