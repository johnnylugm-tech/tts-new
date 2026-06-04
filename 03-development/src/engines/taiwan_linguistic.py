"""FR-01 — Taiwan-Chinese vocabulary mapping (Bopomofo-aware lexicon).

[FR-01]
The static ``LEXICON`` table transforms Mainland-leaning or ambiguous CJK
tokens to their Taiwan-Chinese equivalents (or to space-separated Bopomofo
transcriptions) before SSML parsing and chunking.

Citations:
  - SPEC.md L32-L51  : FR-01 functional requirements + canonical 12 mappings
  - SPEC.md L128     : LEXICON_MIN_SIZE = 50
  - SPEC.md L191-L195: mapping is applied BEFORE SSML parsing and BEFORE
                       chunking, so downstream stages see normalized text
  - SPEC.md L41, L47 : Bopomofo emitted as space-separated syllables with
                       tone diacritics (e.g. ``ㄌㄜˋ ㄙㄜˋ``, ``ㄏㄢˋ``)

The substitution uses a single compiled ``re`` pass with keys sorted by
length descending, which is the canonical longest-match-first algorithm
required by AC4.
"""
from __future__ import annotations

import re
from typing import Final

# --- Constants ----------------------------------------------------------------

#: Minimum required size of the LEXICON table (SPEC.md L128).
LEXICON_MIN_SIZE: Final[int] = 50

#: Static Mainland-leaning → Taiwan-Chinese mapping table.
#: Must include the 12 canonical entries from SPEC.md L37-L50.
#: Bopomofo values are space-separated syllables (SPEC.md L41, L47).
LEXICON: Final[dict[str, str]] = {
    # --- 12 canonical mappings (SPEC.md L37-L50 / TEST_SPEC.md L91-L102) ---
    "視頻": "影片",
    "地鐵": "捷運",
    "垃圾": "ㄌㄜˋ ㄙㄜˋ",
    "菠蘿": "鳳梨",
    "程序員": "工程師",
    "軟件": "軟體",
    "硬件": "硬體",
    "和": "ㄏㄢˋ",          # conjunction, per SPEC.md L46
    "吧": "啦",             # sentence-final particle, per SPEC.md L47
    "互聯網": "網際網路",
    "博客": "部落格",
    "網名": "暱稱",
    # --- Computing / IT terms ---
    "鼠標": "滑鼠",
    "打印": "列印",
    "打印機": "印表機",
    "信息": "訊息",
    "數據": "資料",
    "數據庫": "資料庫",
    "網絡": "網路",
    "默認": "預設",
    "文件": "檔案",
    "文件夾": "資料夾",
    "內存": "記憶體",
    "計算機": "電腦",
    "服務器": "伺服器",
    "客戶端": "用戶端",
    "接口": "介面",
    "數組": "陣列",
    "對像": "物件",
    "線程": "執行緒",
    "調試": "除錯",
    "操作系統": "作業系統",
    "算法": "演算法",
    "程序": "程式",
    "黑客": "駭客",
    "鏈接": "連結",
    "字體": "字型",
    "在線": "線上",
    "離線": "離線",
    "人工智能": "人工智慧",
    "視頻通話": "視訊通話",
    "短信": "簡訊",
    "卡通": "卡通",          # already Taiwan-form
    "二維碼": "QR Code",
    # --- Transport ---
    "出租車": "計程車",
    "公共汽車": "公車",
    "自行車": "腳踏車",
    "摩托車": "機車",
    # --- Food / lifestyle ---
    "桑拿": "三溫暖",
    "激光": "雷射",
    "比薩": "披薩",
    "三文魚": "鮭魚",
    "曲奇": "餅乾",
    "方便麵": "泡麵",
    "快餐": "速食",
    # --- Education / culture ---
    "幼兒園": "幼稚園",
    "衛生間": "洗手間",
    # --- Internet / mobile ---
    "智能手機": "智慧型手機",
    "平板電腦": "平板電腦",
}

# --- Pre-compiled longest-match-first regex (built once at import time) -------
# Sorting by length DESC ensures multi-character tokens match before any of
# their single-character sub-tokens (e.g. ``程序員`` before ``程序``).
_PATTERN: Final[re.Pattern[str]] = re.compile(
    "|".join(re.escape(token) for token in sorted(LEXICON, key=len, reverse=True))
)


def apply_lexicon(text: str) -> str:
    """Apply the Taiwan-Chinese vocabulary mapping to ``text``.

    Behaviour (per SPEC.md L191-L195 + TEST_SPEC.md FR-01 sub-cases):
      * Empty / no-match / punctuation-only input is returned unchanged.
      * Substitutions are performed longest-match-first so multi-character
        tokens win against their single-character prefixes.
      * Bopomofo entries are emitted as space-separated syllables with tone
        diacritics (SPEC.md L41, L47).
    """
    if not text:
        return text
    return _PATTERN.sub(lambda m: LEXICON[m.group(0)], text)


__all__ = ["LEXICON", "LEXICON_MIN_SIZE", "apply_lexicon"]
