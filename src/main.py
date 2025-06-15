import os
import sys
import time
import getpass

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.extractor import extract_text_from_pdf, extract_profile_data, print_profile
from core.matcher import kmp_search, bm_search, fuzzy_search, ac_search
from db.db_connector import DatabaseManager

MYSQL_PASSWORD = None

def get_mysql_password():
    """Get MySQL password from user"""
    global MYSQL_PASSWORD
    if MYSQL_PASSWORD is None:
        MYSQL_PASSWORD = getpass.getpass("Enter MySQL root password: ")
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
        try:
            categories = db.get_all_categories()
            print("Available categories:")
            for i, cat in enumerate(categories, 1):
                print(f"{i}. {cat}")
            
            cat_choice = int(input("Pilih kategori (nomor): ")) - 1
            if 0 <= cat_choice < len(categories):
                category = categories[cat_choice]
                results = db.search_resumes_by_criteria("", category=category)
                print(f"\nDitemukan {len(results)} resume dalam kategori {category}:")
                for i, resume in enumerate(results, 1):
                    print(f"{i}. {resume['filename']}")
        except (ValueError, IndexError):
            print("Pilihan tidak valid")
        except AttributeError:
            print("Method get_all_categories not available")
    
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
        try:
            stats = db.get_statistics()
            print(f"\n=== Database Statistics ===")
            print(f"Total resumes: {stats.get('total_resumes', 0)}")
            print(f"Total searches: {stats.get('total_searches', 0)}")
            
            print(f"\nResumes by category:")
            for cat_stat in stats.get('resumes_by_category', []):
                print(f"  {cat_stat['category']}: {cat_stat['count']}")
        except AttributeError:
            print("Statistics method not available")

def string_matching_demo():
    """Demo algoritma string matching pada file"""
    print("\n=== String Matching Demo ===")
    
    # Get the project root directory (go up from src)
    project_root = os.path.dirname(current_dir)
    
    # Change from "string" to "regex" folder
    regex_dir = os.path.join(project_root, "data", "regex")
    if not os.path.exists(regex_dir):
        print(f"Data regex directory not found at: {regex_dir}")
        print("Please run setup first or check if the data directory exists.")
        return
    
    # Scan all subdirectories in regex folder
    regex_files = []
    categories = []
    
    for root, dirs, files in os.walk(regex_dir):
        relative_path = os.path.relpath(root, regex_dir)
        if relative_path != ".":  # Not the root regex folder
            category = relative_path.split(os.sep)[0]  # Get first level subfolder
            if category not in categories:
                categories.append(category)
        
        for file in files:
            if file.endswith('.txt'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, regex_dir)
                regex_files.append(rel_path)
    
    if not regex_files:
        print("No text files found in regex directory.")
        return
    
    pattern = input("Masukkan kata yang ingin dicari: ")
    print("Pilih algoritma:")
    print("1. KMP")
    print("2. Boyer-Moore") 
    print("3. Aho-Corasick (multiple patterns)")
    print("4. Fuzzy Search")
    
    try:
        method = int(input("Pilih metode (1-4): "))
        much = int(input("Jumlah hasil yang ingin ditampilkan: "))
    except ValueError:
        print("Input tidak valid!")
        return
    
    count = 0
    total_time = 0
    found_files = []
    
    for regex_file in regex_files:
        if count >= much:
            break
            
        file_path = os.path.join(regex_dir, regex_file)
        text = read_file(file_path)
        if not text:
            continue
            
        # Extract category and filename for display
        path_parts = regex_file.split(os.sep)
        if len(path_parts) > 1:
            category = path_parts[0]
            filename = path_parts[-1]
            display_name = f"{category}/{filename.replace('.txt', '')}"
        else:
            display_name = regex_file.replace('.txt', '')
        
        results_found = False
        
        if method == 1:  # KMP
            start_time = time.time()
            results = kmp_search(text, pattern)
            search_time = (time.time() - start_time) * 1000
            total_time += search_time
            
            if results:
                print(f"\n[KMP] Results in {display_name}:")
                print(f"  Pattern ditemukan di posisi: {results}")
                print(f"  Total kemunculan: {len(results)}")
                print(f"  Waktu pencarian: {search_time:.2f} ms")
                results_found = True
                
        elif method == 2:  # Boyer-Moore
            start_time = time.time()
            results = bm_search(text, pattern)
            search_time = (time.time() - start_time) * 1000
            total_time += search_time
            
            if results:
                print(f"\n[Boyer-Moore] Results in {display_name}:")
                print(f"  Pattern ditemukan di posisi: {results}")
                print(f"  Total kemunculan: {len(results)}")
                print(f"  Waktu pencarian: {search_time:.2f} ms")
                results_found = True
                
        elif method == 3:  # Aho-Corasick
            patterns = pattern.split(',')
            patterns = [p.strip() for p in patterns if p.strip()]
            
            if not patterns:
                print("No valid patterns provided")
                continue
            
            start_time = time.time()
            results = ac_search(text, patterns)
            search_time = (time.time() - start_time) * 1000
            total_time += search_time
            
            if results:
                print(f"\n[Aho-Corasick] Results in {display_name}:")
                pattern_results = {}
                for pos, pat in results:
                    if pat not in pattern_results:
                        pattern_results[pat] = []
                    pattern_results[pat].append(pos)
                
                for pat, positions in pattern_results.items():
                    print(f"  Pattern '{pat}' ditemukan di posisi: {positions}")
                print(f"  Total kemunculan: {len(results)}")
                print(f"  Waktu pencarian: {search_time:.2f} ms")
                results_found = True
                
        elif method == 4:  # Fuzzy Search
            start_time = time.time()
            results = fuzzy_search(text, pattern)
            search_time = (time.time() - start_time) * 1000
            total_time += search_time
            
            if results:
                print(f"\n[Fuzzy Search] Results in {display_name}:")
                for pos, word, score in results[:5]:  # Show top 5 matches
                    print(f"  Match: '{word}' at position {pos} (similarity: {score}%)")
                print(f"  Waktu pencarian: {search_time:.2f} ms")
                results_found = True
        else:
            print("Metode tidak valid!")
            return
        
        if results_found:
            found_files.append(display_name)
            count += 1
    
    if count == 0:
        print("Tidak ada hasil ditemukan dengan algoritma yang dipilih.")
    else:
        print(f"\n=== SUMMARY ===")
        print(f"Files dengan hasil: {count}")
        print(f"Total waktu pencarian: {total_time:.2f} ms")
        print(f"Rata-rata waktu per file: {total_time/count:.2f} ms")
        print(f"Files yang ditemukan: {', '.join(found_files)}")

def launch_gui():
    """Launch the GUI application"""
    try:
        from main_gui import IntegratedLandingPage
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        window = IntegratedLandingPage()
        window.show()
        sys.exit(app.exec_())
    except ImportError as e:
        print(f"Error importing GUI components: {e}")
        print("Please make sure PyQt5 is installed: pip install PyQt5")

def main():
    print("=== Resume Search System ===")
    print("1. GUI Application (Recommended)")
    print("2. Database Search (Console)")
    print("3. String Matching Demo")
    print("4. Setup Database")
    print("5. Exit")
    
    while True:
        choice = input("\nPilih opsi (1-5): ")
        
        if choice == "1":
            # Launch GUI
            launch_gui()
            
        elif choice == "2":
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
                
        elif choice == "3":
            # String matching demo
            string_matching_demo()
            
        elif choice == "4":
            # Setup database
            print("Running database setup...")
            setup_script = os.path.join(current_dir, "setup_database.py")
            if os.path.exists(setup_script):
                os.system(f"python {setup_script}")
            else:
                print("Setup script not found. Please create setup_database.py")
            
        elif choice == "5":
            print("Terima kasih!")
            break
            
        else:
            print("Pilihan tidak valid!")

if __name__ == "__main__":
    main()