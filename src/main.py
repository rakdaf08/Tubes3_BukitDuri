import os
import time
from core.extractor import extract_text_from_pdf, extract_profile_data, print_profile
from core.matcher import kmp_search, bm_search, fuzzy_search, ac_search


def read_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Gagal membaca file {file_path}: {e}")
        return ""


def get_all_pdf_files(pdf_dir: str) -> list:
    pdf_files = []
    for root, _, files in os.walk(pdf_dir):
        for file in files:
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def main():
    # Get base data directory path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_dir = os.path.join(base_dir, "data", "pdf")
    
    # Create data directories if they don't exist
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "data", "string"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "data", "regex"), exist_ok=True)
    
    # Get all PDF files recursively
    pdf_files = get_all_pdf_files(pdf_dir)
    
    if not pdf_files:
        print("[ERROR] No PDF files found in data/pdf directory")
        return

    # Process each PDF file
    processed_files = []
    for pdf_path in pdf_files:
        text = extract_text_from_pdf(pdf_path)
        if text:
            # Get relative path + filename without extension
            rel_path = os.path.relpath(pdf_path, pdf_dir)
            rel_path_no_ext = os.path.splitext(rel_path)[0]
            processed_files.append(rel_path_no_ext)

    # String matching demo
    if processed_files:
        print("=== String Matching Demo ===")
        pattern = input("Masukkan kata yang ingin dicari:\n> ")
        method = int(input("Pilih metode (1: KMP, 2: Boyer-Moore, 3: Aho-Corasick):\n> "))
        much = int(input("Jumlah hasil yang ingin ditampilkan:\n> "))
        count = 0
        total_time = 0  # Track total search time
        
        for rel_path in processed_files:
            if count >= much:
                break
            string_path = os.path.join(base_dir, "data", "string", f"{rel_path}_string.txt")
            string_text = read_file(string_path)
            if string_text:
                # Cari menggunakan KMP
                if method == 1:
                    start_time = time.time()
                    kmp_results = kmp_search(string_text, pattern)
                    search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                    total_time += search_time
                    
                    if len(kmp_results) != 0:
                        print(f"\nKMP Search results in {rel_path}:")
                        print(f"Pattern ditemukan di posisi: {kmp_results}")
                        print(f"Total kemunculan: {len(kmp_results)}")
                        count += 1

                # Cari menggunakan Boyer-Moore
                elif method == 2:
                    start_time = time.time()
                    bm_results = bm_search(string_text, pattern)
                    search_time = (time.time() - start_time) * 1000
                    total_time += search_time
                    
                    if len(bm_results) != 0:
                        print(f"\nBoyer-Moore Search results in {rel_path}:")
                        print(f"Pattern ditemukan di posisi: {bm_results}")
                        print(f"Total kemunculan: {len(bm_results)}")
                        count += 1
                        
                elif method == 3:  
                    start_time = time.time()
                    patterns = pattern.split(',')
                    patterns = [p.strip() for p in patterns]
                    ac_results = ac_search(string_text, patterns)
                    search_time = (time.time() - start_time) * 1000
                    total_time += search_time
                    
                    if ac_results:
                        print(f"\nAho-Corasick Search results in {rel_path}:")
                        # Group results by pattern
                        pattern_results = {}
                        for pos, pat in ac_results:
                            if pat not in pattern_results:
                                pattern_results[pat] = []
                            pattern_results[pat].append(pos)
                        
                        # Print results for each pattern
                        for pattern, positions in pattern_results.items():
                            print(f"Pattern '{pattern}' ditemukan di posisi: {positions}")
                        print(f"Total kemunculan: {len(ac_results)}")
                        count += 1
                
        if count == 0:
            fuzzy = input("Kata tidak ditemukan, apakah kamu ingin menggunakan fuzzy search? (y/n)\n> ")
            if fuzzy.lower() == "y":
                fuzzy_count = 0
                for rel_path in processed_files:
                    if fuzzy_count >= much:
                        break
                    string_path = os.path.join(base_dir, "data", "string", f"{rel_path}_string.txt")
                    string_text = read_file(string_path)
                    if string_text:
                        start_time = time.time()
                        fuzzy_results = fuzzy_search(string_text, pattern)
                        search_time = (time.time() - start_time) * 1000
                        total_time += search_time
                        
                        if fuzzy_results:
                            print(f"\nFuzzy Search results in {rel_path}:")
                            for pos, word, score in fuzzy_results:
                                print(f"Match: '{word}' at position {pos} (similarity: {score}%)")
                            fuzzy_count += 1
                if fuzzy_count == 0:
                    print("Tidak ditemukan hasil dengan fuzzy search.")
            else:
                print("Oke selamat tinggal!")
        
        # Print total search time at the end
        print(f"\nTotal waktu pencarian: {total_time:.2f} ms")

                
if __name__ == "__main__":
    main()