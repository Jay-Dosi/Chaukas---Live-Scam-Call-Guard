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
        elif unicodedata.category(ch).startswith('L'):
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
    tokens: list[Token] = []
    in_token = False
    token_start = 0

    for i, ch in enumerate(cleaned):
        if ch == ' ':
            if in_token:
                # End current token
                while token_start < len(original) and original[token_start] == ' ':
                    token_start += 1
                orig_end = _find_orig_position(original, token_start, i)
                tokens.append(Token(text=cleaned[token_start:i], start=token_start, end=orig_end))
                in_token = False
            token_start = i + 1
        else:
            if not in_token:
                token_start = i
                in_token = True

    # Last token
    if in_token:
        orig_end = len(original)
        tokens.append(Token(text=cleaned[token_start:], start=token_start, end=orig_end))

    return tokens, [(t.start, t.end) for t in tokens]


def _find_orig_position(original: str, orig_pos: int, cleaned_pos: int) -> int:
    """Find where cleaned position maps back in the original string."""
    ci = cleaned_pos
    oi = orig_pos
    count = 0
    target_count = sum(1 for c in cleaned[:ci] if c != ' ')

    for oi_scan in range(orig_pos, min(orig_pos + 200, len(original))):
        ch = original[oi_scan]
        if ch in (' ', '\t', '\n', '\r'):
            continue
        count += 1
        if count >= target_count:
            return oi_scan + 1
    return len(original)


def _join_acronyms(tokens: list[Token], origs: list[tuple[int, int]]) -> tuple[list[Token], list[tuple[int, int]]]:
    """Rule 4: Join letter-spaced acronym tokens like 'o t p' -> 'otp'."""
    result_tokens: list[Token] = []
    result_origs: list[tuple[int, int]] = []

    buffer: list[str] = []
    buffer_origs: list[tuple[int, int]] = []

    def flush_buffer() -> None:
        if not buffer:
            return

        if len(buffer) == 1:
            result_tokens.append(tokens[len(result_tokens)])
            result_origs.append(origs[len(result_tokens) - 1])
        else:
            all_single = all(len(t) == 1 for t in buffer)
            if all_single and set(buffer).issubset(_acronym_chars):
                joined = ''.join(buffer)
                result_tokens.append(Token(text=joined, start=buffer_origs[0][0], end=buffer_origs[-1][1]))
                result_origs.append((buffer_origs[0][0], buffer_origs[-1][1]))
            else:
                for t, o in zip(buffer, buffer_origs):
                    result_tokens.append(t)
                    result_origs.append(o)

        buffer.clear()
        buffer_origs.clear()

    for tok in tokens:
        ch = tok.text
        if len(ch) <= 2 and ch in _acronym_chars:
            buffer.append(ch)
            buffer_origs.append(origs[len(result_tokens) + len(buffer) - 1])
            if len(buffer) >= 3:
                flush_buffer()
        else:
            flush_buffer()

    if buffer:
        flush_buffer()

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

    for tok, orig in zip(tokens, origs):
        lower = tok.text.lower()
        if lower in spelled:
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