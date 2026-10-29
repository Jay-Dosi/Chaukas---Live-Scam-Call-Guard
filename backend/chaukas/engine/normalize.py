"""Text normalisation with offset maps.

Normalises text for matching against the lexicon while preserving character offsets
back into the original string so highlights map correctly.

PRD §6.2 rules:
1. Unicode NFC; lowercase Latin; collapse whitespace.
2. Strip punctuation except ₹, %, digits.
3. Map Devanagari digits to ASCII; convert spelled-out digit runs to digits.
4. Letter-spaced acronyms: join "o t p", "ओ टी पी", etc. into one token.
5. Produce token array with character offsets back into the original string.
6. Keep two views: original text (for display) and normalised text (for matching).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Devanagari digit mapping
DEV_DIGIT_START = ord('०')  # 0
ASCII_DIGIT_START = ord('0')


def _to_ascii_digit(ch: str) -> str:
    """Convert a Devanagari digit to ASCII."""
    code = ord(ch)
    if DEV_DIGIT_START <= code < DEV_DIGIT_START + 10:
        return str(code - DEV_DIGIT_START)
    return ch


# Spelled-out digits (English, Hindi, Hinglish)
_spelled_digits_en: dict[str, str] = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
}
_spelled_digits_hi: dict[str, str] = {
    'शून्य': '0', 'एक': '1', 'दो': '2', 'तीन': '3', 'चार': '4',
    'पाँच': '5', 'पंच': '5', 'पांच': '5', 'छह': '6', 'सात': '7',
    'आठ': '8', 'नौ': '9',
}
_spelled_digits_hinglish: dict[str, str] = {
    'ek': '1', 'do': '2', 'teen': '3', 'char': '4', 'chaar': '4',
    'paanch': '5', 'panch': '5', 'chahe': '6', 'sat': '7', 'aath': '8',
    'nao': '9',
}

_spelled_digits: dict[str, dict[str, str]] = {
    'en': _spelled_digits_en,
    'hi': _spelled_digits_hi,
    'hinglish': _spelled_digits_hinglish,
}

# Common acronym character sets
_acronym_chars = frozenset('otpincvupyhkadm')


@dataclass(frozen=True)
class Token:
    """A single normalised token with its span in the original text."""
    text: str          # normalised form
    start: int         # start offset in original text
    end: int           # end offset in original text (exclusive)


def normalise(text: str, lang: str | None = None) -> tuple[str, list[Token]]:
    """Normalise text according to PRD §6.2 rules.

    Returns:
        (normalised_text, token_list) where token_list[i].text matches
        normalised_text segment i and token_list[i].start/end reference the
        original input string.
    """
    if not text or not text.strip():
        return '', []

    # Rule 1: NFC normalise, lowercase Latin
    raw = unicodedata.normalize('NFC', text)
    lowered = ''
    for ch in raw:
        cat = unicodedata.category(ch)
        if cat.startswith('L'):
            lowered += ch.lower()
        else:
            lowered += ch

    # Rule 2: Strip punctuation except ₹, %, digits
    cleaned = ''
    for ch in lowered:
        if ch in ('₹', '%'):
            cleaned += ch
        elif ch.isdigit() or _is_devanagari_digit(ch):
            cleaned += ch
        elif unicodedata.category(ch).startswith(('L', 'M')):
            cleaned += ch
        elif ch in (' ', '\t', '\n', '\r'):
            cleaned += ' '
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Rule 3: Convert Devanagari digits to ASCII
    no_dev_digits = ''.join(_to_ascii_digit(ch) if _is_devanagari_digit(ch) else ch for ch in cleaned)

    # Build tokens from cleaned string, tracking positions in the original
    tokens, origs = _build_tokens_with_offsets(raw, no_dev_digits, lang)

    # Rule 4: Join letter-spaced acronyms
    tokens, origs = _join_acronyms(tokens, origs)

    # Rule 3b: Replace spelled-out digits with numerals (only 0–9)
    tokens, origs = _replace_spelled_digits(tokens, origs, lang)

    norm_text = ' '.join(t.text for t in tokens)
    return norm_text, tokens


def _is_devanagari_digit(ch: str) -> bool:
    code = ord(ch)
    return DEV_DIGIT_START <= code < DEV_DIGIT_START + 10


def _build_tokens_with_offsets(
    original: str, cleaned: str, lang: str | None = None
) -> tuple[list[Token], list[tuple[int, int]]]:
    """Build tokens from cleaned text, tracking char-offsets in the original."""
    clean_chars: list[str] = []
    clean_to_orig: list[int] = []

    for orig_idx, ch in enumerate(original):
        # Fast path for ASCII alphanumeric and space
        if ch.isascii():
            if 'a' <= ch <= 'z' or '0' <= ch <= '9':
                clean_chars.append(ch)
                clean_to_orig.append(orig_idx)
                continue
            if 'A' <= ch <= 'Z':
                clean_chars.append(ch.lower())
                clean_to_orig.append(orig_idx)
                continue
            if ch in (' ', '\t', '\n', '\r') or ch in ('-', '/', '_', ':', ';', ',', '.', '!', '?', '(', ')', '[', ']', '"', "'", '“', '”'):
                if clean_chars and clean_chars[-1] != ' ':
                    clean_chars.append(' ')
                    clean_to_orig.append(orig_idx)
                continue
            if ch == '%':
                clean_chars.append('%')
                clean_to_orig.append(orig_idx)
                continue
            continue

        # Non-ASCII path (Indic scripts, Devanagari digits, ₹)
        if ch == '₹':
            clean_chars.append('₹')
            clean_to_orig.append(orig_idx)
            continue

        if _is_devanagari_digit(ch):
            clean_chars.append(_to_ascii_digit(ch))
            clean_to_orig.append(orig_idx)
            continue

        cat = unicodedata.category(ch)
        if cat.startswith(('L', 'M')):
            clean_chars.append(ch.lower())
            clean_to_orig.append(orig_idx)

    while clean_chars and clean_chars[-1] == ' ':
        clean_chars.pop()
        clean_to_orig.pop()

    tokens: list[Token] = []
    i = 0
    n = len(clean_chars)
    while i < n:
        if clean_chars[i] == ' ':
            i += 1
            continue
        start_idx = i
        while i < n and clean_chars[i] != ' ':
            i += 1
        end_idx = i
        tok_text = ''.join(clean_chars[start_idx:end_idx])
        orig_start = clean_to_orig[start_idx]
        orig_end = clean_to_orig[end_idx - 1] + 1
        tokens.append(Token(text=tok_text, start=orig_start, end=orig_end))

    return tokens, [(t.start, t.end) for t in tokens]


def _join_acronyms(tokens: list[Token], origs: list[tuple[int, int]]) -> tuple[list[Token], list[tuple[int, int]]]:
    """Rule 4: Join letter-spaced acronym tokens like 'o t p' -> 'otp'."""
    if not tokens:
        return [], []

    result_tokens: list[Token] = []
    result_origs: list[tuple[int, int]] = []

    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if (len(tok.text) == 1 and tok.text.isalpha()) or tok.text in _acronym_chars:
            j = i
            while j < n and ((len(tokens[j].text) == 1 and tokens[j].text.isalpha()) or tokens[j].text in _acronym_chars):
                j += 1
            if j - i >= 2:
                joined_text = "".join(t.text for t in tokens[i:j])
                joined_tok = Token(text=joined_text, start=tokens[i].start, end=tokens[j - 1].end)
                result_tokens.append(joined_tok)
                result_origs.append((joined_tok.start, joined_tok.end))
                i = j
                continue

        result_tokens.append(tok)
        result_origs.append((tok.start, tok.end))
        i += 1

    return result_tokens, result_origs


def _replace_spelled_digits(
    tokens: list[Token], origs: list[tuple[int, int]], lang: str | None
) -> tuple[list[Token], list[tuple[int, int]]]:
    """Replace spelled-out digits with their numeric equivalents."""
    if not lang:
        lang = 'en'

    spelled = _spelled_digits.get(lang, {})
    if not spelled:
        return tokens, origs

    result: list[Token] = []
    result_origs: list[tuple[int, int]] = []

    n = len(tokens)
    for idx, (tok, orig) in enumerate(zip(tokens, origs)):
        lower = tok.text.lower()
        if lower in spelled:
            # 'do' in Hinglish is ambiguous with English 'do' (e.g. 'do not')
            if lower == 'do':
                prev_tok = tokens[idx - 1].text.lower() if idx > 0 else ''
                next_tok = tokens[idx + 1].text.lower() if idx + 1 < n else ''
                is_digit_run = (
                    prev_tok in spelled or prev_tok.isdigit() or
                    next_tok in spelled or next_tok.isdigit()
                )
                if not is_digit_run:
                    result.append(tok)
                    result_origs.append(orig)
                    continue

            num = spelled[lower]
            result.append(Token(text=num, start=orig[0], end=orig[1]))
            result_origs.append(orig)
        else:
            result.append(tok)
            result_origs.append(orig)

    return result, result_origs


def get_offset_map(tokens: list[Token]) -> list[tuple[int, int]]:
    """Return [(start, end) pairs into the original text for each normalised token]."""
    return [(t.start, t.end) for t in tokens]


def reconstruct_original(normalised: str, tokens: list[Token], original: str) -> str:
    """Reconstruct the original text snippet for a given normalised span."""
    parts: list[str] = []
    for token in tokens:
        parts.append(original[token.start:token.end])
    return ''.join(parts)