from fuzzywuzzy import fuzz
import re
from typing import List, Tuple

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


def kmp_search(text_normal: str, pattern_normal: str) -> list[int]:
    text = text_normal.lower()
    pattern = pattern_normal.lower()
    
    lps = compute_lps(pattern)
    result = []
    i = 0 
    j = 0 

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
    table = {}
    for i, ch in enumerate(pattern):
        table[ch] = i
    return table


def good_suffix_table(pattern: str) -> list[int]:
    m = len(pattern)
    if m == 0:
        return []

    good_suffix = [0] * (m + 1) 
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
    for i in range(m):
        if good_suffix[i] == 0:
            good_suffix[i] = j
        if i == j:
            j = border_pos[j]

    return good_suffix[1:]


def bm_search(text_normal: str, pattern_normal: str) -> list[int]:
    text = text_normal.lower()
    pattern = pattern_normal.lower()
    
    if len(pattern) == 0:
        return []

    bad_char = bad_character_table(pattern)
    good_suffix = good_suffix_table(pattern)
    result = []

    s = 0 
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


def fuzzy_search(text: str, pattern: str, threshold: int = 60) -> list[tuple[int, str, int]]:
    results = []
    words = re.findall(r'\w+', text)
    
    for i, word in enumerate(words):
        score = fuzz.ratio(pattern.lower(), word.lower())
        if score >= threshold:
            pos = text.find(word)
            results.append((pos, word, score))
            
    return sorted(results, key=lambda x: x[2], reverse=True)


class AhoCorasickNode:
    def __init__(self):
        self.goto = {}
        self.out = []
        self.fail = None

def build_ac_automaton(patterns: list[str]) -> AhoCorasickNode:
    root = AhoCorasickNode()

    # Build trie
    for i, pattern in enumerate(patterns):
        node = root
        for c in pattern:
            if c not in node.goto:
                node.goto[c] = AhoCorasickNode()
            node = node.goto[c]
        node.out.append((i, pattern))

    queue = []
    for c, node in root.goto.items():
        queue.append(node)
        node.fail = root

    while queue:
        current = queue.pop(0)
        for c, node in current.goto.items():
            queue.append(node)
            failure = current.fail
            while failure and c not in failure.goto:
                failure = failure.fail
            node.fail = failure.goto[c] if failure else root
            node.out.extend(node.fail.out)

    return root

def ac_search(text_normal: str, patterns_normal: list[str]) -> list[tuple[int, str]]:
    text = text_normal.lower()
    patterns = [p.lower() for p in patterns_normal]
    
    if not patterns:
        return []

    root = build_ac_automaton(patterns)
    current = root
    results = []

    for i, c in enumerate(text):
        while current and c not in current.goto:
            current = current.fail
        if not current:
            current = root
            continue
        current = current.goto[c]
        for pattern_id, pattern in current.out:
            pos = i - len(pattern) + 1
            results.append((pos, pattern))

    return sorted(results)