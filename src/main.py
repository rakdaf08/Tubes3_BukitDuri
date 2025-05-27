import os
from core.extractor import extract_text_from_pdf, extract_profile_data

# Path ke PDF
pdf_path = "../data/69532425.pdf"
output_text_path = "../data/69532425.txt"

# 1. Ekstraksi teks dari PDF
text = extract_text_from_pdf(pdf_path)

# 2. Ekstraksi data dengan regex
profile = extract_profile_data(text)
print("\n[INFO] Data yang berhasil diekstrak:\n")
for key, value in profile.items():
    print(f"{key}: {value}")
