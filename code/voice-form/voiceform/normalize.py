"""Plain-code normalising: Devanagari digits, Marathi and Hindi number words, blood pressure, phone numbers, dates.

Speech engines write numbers both ways ("140" and "एकशे चाळीस"), and small models are unreliable with them, so this
is code, not a prompt. The model sees the normalised transcript, and the typed values it returns are parsed here.

The number-word tables were written from general knowledge, not taken from a reference list. Spelling variants are
common in speech-engine output; every miss found on real recordings becomes a test and a table entry.
"""

import datetime as _dt
import re
import unicodedata
from typing import List, Optional, Tuple

# ---------------------------------------------------------------- text folding

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_NUKTA = "़"
_ZW = dict.fromkeys(map(ord, "‌‍﻿"), None)


def fold(text: str) -> str:
    """Matching key: NFD, drop nukta, chandrabindu to anusvara, drop zero-width joiners, lower case, then NFC."""
    t = unicodedata.normalize("NFD", text or "").replace(_NUKTA, "").replace("ँ", "ं")
    t = t.translate(_ZW).lower()
    return unicodedata.normalize("NFC", t)


def tokens(text: str) -> List[str]:
    """Words and numbers; punctuation other than '/', '.', '-' and '+' splits tokens."""
    t = text.translate(_DEV_DIGITS)
    t = re.sub(r"[,;:!?\"'()\[\]{}।॥]", " ", t)  # includes the danda and double danda
    t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)  # a full stop ends a word; a decimal point between digits stays
    return t.split()


# ---------------------------------------------------------------- number words

_MR = """0 शून्य|1 एक|2 दोन|3 तीन|4 चार|5 पाच|6 सहा|7 सात|8 आठ|9 नऊ|10 दहा|11 अकरा|12 बारा|13 तेरा|14 चौदा|15 पंधरा
16 सोळा|17 सतरा|18 अठरा|19 एकोणीस|20 वीस|21 एकवीस|22 बावीस|23 तेवीस|24 चोवीस|25 पंचवीस|26 सव्वीस|27 सत्तावीस
28 अठ्ठावीस|29 एकोणतीस|30 तीस|31 एकतीस|32 बत्तीस|33 तेहेतीस|34 चौतीस|35 पस्तीस|36 छत्तीस|37 सदतीस|38 अडतीस
39 एकोणचाळीस|40 चाळीस|41 एक्केचाळीस|42 बेचाळीस|43 त्रेचाळीस|44 चव्वेचाळीस|45 पंचेचाळीस|46 सेहेचाळीस
47 सत्तेचाळीस|48 अठ्ठेचाळीस|49 एकोणपन्नास|50 पन्नास|51 एक्कावन्न|52 बावन्न|53 त्रेपन्न|54 चोपन्न|55 पंचावन्न
56 छप्पन्न|57 सत्तावन्न|58 अठ्ठावन्न|59 एकोणसाठ|60 साठ|61 एकसष्ट|62 बासष्ट|63 त्रेसष्ट|64 चौसष्ट|65 पासष्ट
66 सहासष्ट|67 सदुसष्ट|68 अडुसष्ट|69 एकोणसत्तर|70 सत्तर|71 एकाहत्तर|72 बाहत्तर|73 त्र्याहत्तर|74 चौऱ्याहत्तर
75 पंच्याहत्तर|76 शहात्तर|77 सत्याहत्तर|78 अठ्ठ्याहत्तर|79 एकोणऐंशी|80 ऐंशी|81 एक्याऐंशी|82 ब्याऐंशी|83 त्र्याऐंशी
84 चौऱ्याऐंशी|85 पंच्याऐंशी|86 शहाऐंशी|87 सत्त्याऐंशी|88 अठ्ठ्याऐंशी|89 एकोणनव्वद|90 नव्वद|91 एक्याण्णव
92 ब्याण्णव|93 त्र्याण्णव|94 चौऱ्याण्णव|95 पंच्याण्णव|96 शहाण्णव|97 सत्त्याण्णव|98 अठ्ठ्याण्णव|99 नव्व्याण्णव"""

_HI = """0 शून्य|1 एक|2 दो|3 तीन|4 चार|5 पांच|6 छह|7 सात|8 आठ|9 नौ|10 दस|11 ग्यारह|12 बारह|13 तेरह|14 चौदह|15 पंद्रह
16 सोलह|17 सत्रह|18 अठारह|19 उन्नीस|20 बीस|21 इक्कीस|22 बाईस|23 तेईस|24 चौबीस|25 पच्चीस|26 छब्बीस|27 सत्ताईस
28 अट्ठाईस|29 उनतीस|30 तीस|31 इकतीस|32 बत्तीस|33 तैंतीस|34 चौंतीस|35 पैंतीस|36 छत्तीस|37 सैंतीस|38 अड़तीस
39 उनतालीस|40 चालीस|41 इकतालीस|42 बयालीस|43 तैंतालीस|44 चवालीस|45 पैंतालीस|46 छियालीस|47 सैंतालीस
48 अड़तालीस|49 उनचास|50 पचास|51 इक्यावन|52 बावन|53 तिरेपन|54 चौवन|55 पचपन|56 छप्पन|57 सत्तावन|58 अट्ठावन
59 उनसठ|60 साठ|61 इकसठ|62 बासठ|63 तिरेसठ|64 चौंसठ|65 पैंसठ|66 छियासठ|67 सड़सठ|68 अड़सठ|69 उनहत्तर|70 सत्तर
71 इकहत्तर|72 बहत्तर|73 तिहत्तर|74 चौहत्तर|75 पचहत्तर|76 छिहत्तर|77 सतहत्तर|78 अठहत्तर|79 उनासी|80 अस्सी
81 इक्यासी|82 बयासी|83 तिरासी|84 चौरासी|85 पचासी|86 छियासी|87 सत्तासी|88 अट्ठासी|89 नवासी|90 नब्बे|91 इक्यानबे
92 बानबे|93 तिरानबे|94 चौरानबे|95 पंचानबे|96 छियानबे|97 सत्तानबे|98 अट्ठानबे|99 निन्यानबे"""

# Common spelling variants seen in speech-engine output, and English words for the digits a speaker may switch to.
_VARIANTS = """5 पांच|5 पाँच|6 छः|6 छे|6 छै|9 नव|19 एकोणवीस|33 तेहतीस|34 चौंतीस|39 उनचालीस|50 पचास|100 शंभर|100 सौ
0 zero|0 झिरो|1 one|2 two|3 three|4 four|5 five|6 six|7 seven|8 eight|9 nine|10 ten"""


def _table(*blocks: str) -> dict:
    out = {}
    for block in blocks:
        for item in block.replace("\n", "|").split("|"):
            item = item.strip()
            if item:
                num, word = item.split(" ", 1)
                out.setdefault(fold(word), float(num))
    return out


WORDS = _table(_MR, _HI, _VARIANTS)
HUNDRED = {fold(w) for w in ("शे", "सौ", "hundred")}
THOUSAND = {fold(w): 1000 for w in ("हजार", "हज़ार", "thousand")}
THOUSAND.update({fold(w): 100000 for w in ("लाख", "lakh")})
HALF_PLUS = {fold(w) for w in ("साडे", "साढ़े", "साढे")}
QUARTER_PLUS = {fold(w) for w in ("सव्वा",)}
QUARTER_MINUS = {fold(w) for w in ("पावणे", "पौने")}
WHOLE = {fold("दीड"): 1.5, fold("डेढ़"): 1.5, fold("अडीच"): 2.5, fold("ढाई"): 2.5}
POINT = {fold(w) for w in ("point", "पॉइंट", "पॉईंट", "पोइंट", "दशांश", "दशमलव")}
# Words that are also ordinary words; converted only when a number word or a digit is next to them.
AMBIGUOUS = {fold("एक"), fold("दो")}


def _atom(tok: str) -> Optional[Tuple[float, bool]]:
    """(value, is_hundreds) for one token, or None. Handles 'एकशे', 'दीडशे', 'साडेतीनशे' written as one word."""
    k = fold(tok)
    if re.fullmatch(r"\d+(\.\d+)?", k):
        return float(k), False
    if k in WORDS:
        return WORDS[k], False
    if k in WHOLE:
        return WHOLE[k], False
    for pre in HALF_PLUS:
        if k.startswith(pre) and k != pre:
            inner = _atom(k[len(pre):])
            if inner:
                return inner[0] + 0.5, inner[1]
    for suf in ("शे",):
        s = fold(suf)
        if k.endswith(s) and k != s:
            head = k[: -len(s)]
            inner = WORDS.get(head, WHOLE.get(head))
            if inner is not None:
                return inner * 100, True
    return None


def _fmt(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else ("%.2f" % v).rstrip("0").rstrip(".")


def numbers_to_digits(text: str) -> str:
    """Replace spoken numbers with digits. 'एकशे चाळीस बाय नव्वद' -> '140 बाय 90'; 'साडे दहा' -> '10.5'."""
    toks = tokens(text)
    out: List[str] = []
    i = 0
    n = len(toks)

    def is_num(j: int) -> bool:
        if not 0 <= j < n:
            return False
        k = fold(toks[j])
        return _atom(toks[j]) is not None or k in HALF_PLUS | QUARTER_PLUS | QUARTER_MINUS | HUNDRED or k in THOUSAND

    while i < n:
        k = fold(toks[i])
        start = i
        cur: Optional[float] = None
        total = 0.0
        adjust = 0.0
        if k in HALF_PLUS | QUARTER_PLUS | QUARTER_MINUS and i + 1 < n and _atom(toks[i + 1]):
            adjust = 0.5 if k in HALF_PLUS else (0.25 if k in QUARTER_PLUS else -0.25)
            i += 1
        atom = _atom(toks[i]) if i < n else None
        if atom is None or (fold(toks[i]) in AMBIGUOUS and not adjust and not (is_num(i + 1) or is_num(i - 1))):
            out.append(toks[start])
            i = start + 1
            continue
        cur = atom[0] + adjust
        hundreds_done = atom[1]
        i += 1
        while i < n:
            k = fold(toks[i])
            if k in HUNDRED and not hundreds_done:
                cur = (cur or 1) * 100
                hundreds_done = True
                i += 1
                continue
            if k in THOUSAND:
                total += (cur or 1) * THOUSAND[k]
                cur, hundreds_done = 0.0, False
                i += 1
                continue
            if k in POINT and i + 1 < n:
                digits = []
                j = i + 1
                while j < n and _atom(toks[j]) and _atom(toks[j])[0] < 10 and float(_atom(toks[j])[0]).is_integer():
                    digits.append(_fmt(_atom(toks[j])[0]))
                    j += 1
                if digits:
                    cur = float(_fmt(cur or 0) + "." + "".join(digits))
                    i = j
                break
            nxt = _atom(toks[i])
            # A smaller number may follow a round hundred or thousand ("एकशे चाळीस", "दो हज़ार पांच").
            if nxt and not nxt[1] and nxt[0] < 100 and ((cur and cur % 100 == 0 and cur >= 100) or (total and not cur)):
                cur = (cur or 0) + nxt[0]
                i += 1
                break
            break
        out.append(_fmt(total + (cur or 0)))
    return " ".join(out)


def normalize_text(text: str) -> str:
    """The text the model sees: NFC, Devanagari digits as ASCII, spoken numbers as digits, single spaces."""
    t = unicodedata.normalize("NFC", text or "")
    return numbers_to_digits(t)


# ---------------------------------------------------------------- typed parsers

_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_BP_SEP = {fold(w) for w in ("/", "by", "बाय", "over", "ओव्हर", "ओवर", "पर", "on")}


def first_number(value) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = _NUM_RE.search(normalize_text(str(value)).replace(",", ""))
    return float(m.group(0)) if m else None


def parse_bp(value) -> Optional[Tuple[int, int]]:
    """'140/90', '140 by 90', '140 बाय 90', {'systolic': 140, 'diastolic': 90} -> (140, 90)."""
    if isinstance(value, dict):
        try:
            return int(value["systolic"]), int(value["diastolic"])
        except (KeyError, TypeError, ValueError):
            return None
    t = normalize_text(str(value)).replace("/", " / ")
    toks = t.split()
    for i in range(len(toks) - 2):
        if _NUM_RE.fullmatch(toks[i]) and fold(toks[i + 1]) in _BP_SEP and _NUM_RE.fullmatch(toks[i + 2]):
            return int(float(toks[i])), int(float(toks[i + 2]))
    nums = _NUM_RE.findall(t)
    if len(nums) == 2:
        return int(float(nums[0])), int(float(nums[1]))
    return None


def parse_phone(value) -> Optional[str]:
    """Ten-digit Indian mobile number from digits, spoken digits or '+91 ...'. None if it is not ten digits 6-9xxx."""
    digits = re.sub(r"\D", "", normalize_text(str(value)))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits if re.fullmatch(r"[6-9]\d{9}", digits) else None


_MONTHS = {}
for _i, _names in enumerate([
    "january jan जानेवारी जनवरी", "february feb फेब्रुवारी फरवरी", "march mar मार्च",
    "april apr एप्रिल अप्रैल", "may मे मई", "june jun जून", "july jul जुलै जुलाई",
    "august aug ऑगस्ट अगस्त ओगस्ट", "september sep sept सप्टेंबर सितंबर सितम्बर",
    "october oct ऑक्टोबर अक्टूबर अक्तूबर", "november nov नोव्हेंबर नवंबर नवम्बर",
    "december dec डिसेंबर दिसंबर दिसम्बर"], start=1):
    for _n in _names.split():
        _MONTHS[fold(_n)] = _i

_RELATIVE = {fold("आज"): 0, fold("today"): 0, fold("उद्या"): 1, fold("tomorrow"): 1, fold("परवा"): 2}
_AMBIGUOUS_DAYS = {fold("कल"), fold("परसों")}  # Hindi: yesterday or tomorrow, depending on context


class DateAmbiguous(ValueError):
    pass


def parse_date(value, today: Optional[_dt.date] = None) -> Optional[_dt.date]:
    """ISO, dd/mm/yyyy, '12 नोव्हेंबर', '12 November 2026', 'उद्या'. No year: this year, or next year if already past.

    Raises DateAmbiguous for Hindi 'कल' and 'परसों', which can mean the past or the future.
    """
    today = today or _dt.date.today()
    if isinstance(value, _dt.date):
        return value
    raw = str(value).strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", raw)
    if m:
        return _dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    t = normalize_text(raw)
    m = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b", t)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return _dt.date(y + 2000 if y < 100 else y, mo, d)
    words = [fold(w) for w in t.split()]
    for w in words:
        if w in _AMBIGUOUS_DAYS:
            raise DateAmbiguous(w)
        if w in _RELATIVE:
            return today + _dt.timedelta(days=_RELATIVE[w])
    day = month = year = None
    for w in words:
        # Marathi and Hindi attach case endings to the month: 'नोव्हेंबरला', 'नवंबर को' is already split.
        m_key = w if w in _MONTHS else next((k for k in _MONTHS if len(k) >= 4 and w.startswith(k)), None)
        if m_key and month is None:
            month = _MONTHS[m_key]
        elif re.fullmatch(r"\d{4}", w):
            year = int(w)
        elif re.fullmatch(r"\d{1,2}", w) and day is None:
            day = int(w)
    if day and month:
        cand = _dt.date(year or today.year, month, day)
        if year is None and cand < today:
            cand = _dt.date(today.year + 1, month, day)
        return cand
    return None


_YES = {fold(w) for w in ("yes", "true", "हो", "होय", "आहे", "हां", "हाँ", "है", "जी हां")}
_NO = {fold(w) for w in ("no", "false", "नाही", "नाहीं", "नहीं", "नही", "ना")}


def parse_bool(value) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    words = [fold(w) for w in tokens(str(value))]
    if any(w in _NO for w in words):  # "आहे का? नाही" style answers: a negation wins
        return False
    if any(w in _YES for w in words):
        return True
    return None


def match_option(value, options: dict) -> Optional[str]:
    """Canonical option for a spoken or written value, by exact key or synonym (folded, substring both ways)."""
    v = fold(str(value)).replace("_", " ").strip()
    if not v:
        return None
    for key in options:
        if v == fold(key).replace("_", " "):
            return key
    # Longest matching synonym wins: 'फवारणी पंप' (sprayer) must beat 'पंप' (water pump),
    # and 'जल्दी नहीं' (low) must beat 'जल्दी' (high).
    pairs = [(key, fold(s)) for key, synonyms in options.items() for s in synonyms if fold(s)]
    for key, fs in pairs:                      # 1. the whole value is a synonym
        if fs == v:
            return key
    best, best_len = None, 0
    for key, fs in pairs:                      # 2. the longest synonym inside the value
        if fs in v and len(fs) > best_len:
            best, best_len = key, len(fs)
    if best:
        return best
    for key, fs in pairs:                      # 3. the value is part of a synonym ('लाइट' of 'सोलर लाइट')
        if len(v) >= 3 and v in fs:
            return key
    return None
