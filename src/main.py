import os
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


def main():
    # Path ke PDF (sekarang di folder pdf)
    pdf_path = "../data/pdf/69532425.pdf"

    # 1. Ekstraksi teks dari PDF
    text = extract_text_from_pdf(pdf_path)

    # 2. Ekstraksi data dengan regex
    profile = extract_profile_data(text)
    print_profile(profile)

    # 3. Demonstrasi string matching
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    string_path = f"../data/string/{filename}_string.txt"
    string_text = read_file(string_path)

    # Pattern yang ingin dicari
    pattern = input("Masukkan kata yang ingin dicari:\n> ")

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
