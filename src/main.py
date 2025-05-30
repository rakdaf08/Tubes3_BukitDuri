import os
import fitz 
from core.extractor import extract_text_from_pdf, extract_profile_data, print_profile
from core.matcher import kmp_search, bm_search


def read_file(file_path: str) -> str:
    """Baca file teks dan return isinya"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Gagal membaca file {file_path}: {e}")
        return ""


def get_all_pdf_files(pdf_dir: str) -> list:
    """Recursively get all PDF files from directory and subdirectories"""
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
        print("\n=== String Matching Demo ===")
        pattern = input("Masukkan kata yang ingin dicari:\n> ")

        for rel_path in processed_files:
            string_path = os.path.join(base_dir, "data", "string", f"{rel_path}_string.txt")
            string_text = read_file(string_path)
            
            if string_text:
                print(f"\nSearching in {rel_path}:")
                
                # Cari menggunakan KMP
                kmp_results = kmp_search(string_text, pattern)
                print(f"\nKMP Search results:")
                print(f"Pattern ditemukan di posisi: {kmp_results}")
                print(f"Total kemunculan: {len(kmp_results)}")

                # Cari menggunakan Boyer-Moore
                bm_results = bm_search(string_text, pattern)
                print(f"\nBoyer-Moore Search results:")
                print(f"Pattern ditemukan di posisi: {bm_results}")
                print(f"Total kemunculan: {len(bm_results)}")
                
if __name__ == "__main__":
    main()