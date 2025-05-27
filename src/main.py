import os
from core.extractor import extract_text_from_pdf, extract_profile_data
from core.matcher import kmp_search, bm_search


def read_file(file_path: str) -> str:
    """Baca file teks dan return isinya"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Gagal membaca file {file_path}: {e}")
        return ""


def main():
    # Path ke PDF
    pdf_path = "../data/69532425.pdf"

    # 1. Ekstraksi teks dari PDF (akan menghasilkan 2 file: _regex.txt dan _string.txt)
    text = extract_text_from_pdf(pdf_path)

    # 2. Ekstraksi data dengan regex
    profile = extract_profile_data(text)
    print("\n[INFO] Data yang berhasil diekstrak:\n")
    for key, value in profile.items():
        print(f"{key}: {value}")

    # 3. Demonstrasi string matching
    base_path = os.path.splitext(pdf_path)[0]
    string_text = read_file(f"{base_path}_string.txt")

    # Pattern yang ingin dicari
    pattern = "math"  # Contoh pattern

    print("\n=== String Matching Demo ===")
    print(f"Mencari pattern: '{pattern}'")

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
