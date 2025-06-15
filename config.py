DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Ganti password di sini saja
    'database': 'Tubes3Stima'
}

SEARCH_SETTINGS = {
    'default_top_matches': 3,
    'fuzzy_threshold': 60,
    'high_similarity_threshold': 70,
    'items_per_page': 4
}

ENCRYPTION_SETTINGS = {
    'enabled': True, 
    'encrypt_fields': [
        'first_name', 
        'last_name', 
        'address', 
        'phone_number'
    ],
    'master_key': 'BukitDuri_SecureKey_CV_Analyzer'
}