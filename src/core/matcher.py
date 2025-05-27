def compute_lps(pattern: str) -> list[int]:
    """
    Membuat tabel lps (longest prefix suffix) untuk KMP.
    lps[i] = panjang prefix terbesar yang juga suffix untuk pattern[:i+1]
    """
    lps = [0] * len(pattern)
    length = 0  # panjang prefix yang sama dengan suffix
    i = 1
    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps


def kmp_search(text: str, pattern: str) -> list[int]:
    """
    Cari pattern dalam text menggunakan KMP.
    Return list indeks posisi pattern ditemukan.
    """
    lps = compute_lps(pattern)
    result = []
    i = 0  # index text
    j = 0  # index pattern

    while i < len(text):
        if text[i] == pattern[j]:
            i += 1
            j += 1

            if j == len(pattern):
                result.append(i - j)
                j = lps[j - 1]
        else:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return result


def bad_character_table(pattern: str) -> dict:
    """
    Membuat tabel bad character heuristic untuk BM.
    Menyimpan posisi kanan terakhir setiap karakter dalam pattern.
    """
    table = {}
    for i, ch in enumerate(pattern):
        table[ch] = i
    return table


def good_suffix_table(pattern: str) -> list[int]:
    """
    Membuat tabel good suffix heuristic untuk BM.
    """
    m = len(pattern)
    good_suffix = [0] * m
    border_pos = [0] * (m + 1)

    i = m
    j = m + 1
    border_pos[i] = j

    while i > 0:
        while j <= m and pattern[i - 1] != pattern[j - 1]:
            if good_suffix[j] == 0:
                good_suffix[j] = j - i
            j = border_pos[j]
        i -= 1
        j -= 1
        border_pos[i] = j

    j = border_pos[0]
    for i in range(m + 1):
        if good_suffix[i] == 0:
            good_suffix[i] = j
        if i == j:
            j = border_pos[j]

    return good_suffix[1:]


def bm_search(text: str, pattern: str) -> list[int]:
    """
    Cari pattern dalam text menggunakan Boyer-Moore.
    Return list indeks posisi pattern ditemukan.
    """
    if len(pattern) == 0:
        return []

    bad_char = bad_character_table(pattern)
    good_suffix = good_suffix_table(pattern)
    result = []

    s = 0  # posisi shift pattern terhadap text
    while s <= len(text) - len(pattern):
        j = len(pattern) - 1

        while j >= 0 and pattern[j] == text[s + j]:
            j -= 1

        if j < 0:
            result.append(s)
            s += good_suffix[0] if len(pattern) > 1 else 1
        else:
            bc_shift = j - bad_char.get(text[s + j], -1)
            gs_shift = good_suffix[j] if j < len(good_suffix) else 1
            s += max(bc_shift, gs_shift)

    return result


if __name__ == "__main__":
    # Contoh test sederhana
    text = "ABABDABACDABABCABAB"
    pattern = "ABABCABAB"

    print("=== KMP Search ===")
    print(kmp_search(text, pattern))  # Output: [10]

    print("=== Boyer-Moore Search ===")
    print(bm_search(text, pattern))  # Output: [10]
