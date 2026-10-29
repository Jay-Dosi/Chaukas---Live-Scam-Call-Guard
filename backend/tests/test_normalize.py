"""Unit tests for text normalization — PRD §6.2."""

import pytest
from chaukas.engine.normalize import normalise, Token


def test_unicode_nfc_and_devanagari_digits():
    raw = "फोन नंबर ९८७६५४३२१० पर कॉल करें"
    norm, tokens = normalise(raw, "hi")
    assert "9876543210" in norm
    assert any(t.text == "9876543210" for t in tokens)


def test_indic_matra_preservation():
    raw = "पुलिस अधिकारी डिजिटल अरेस्ट"
    norm, tokens = normalise(raw, "hi")
    token_texts = [t.text for t in tokens]
    # Matras (u matra ु, i matra ि) must be preserved, not stripped into consonant-only stems
    assert "पुलिस" in token_texts
    assert "अधिकारी" in token_texts
    assert "डिजिटल" in token_texts
    assert "अरेस्ट" in token_texts


def test_acronym_joining():
    raw = "Please enter your o t p and k y c details"
    norm, tokens = normalise(raw, "en")
    token_texts = [t.text for t in tokens]
    assert "otp" in token_texts
    assert "kyc" in token_texts
    assert "o" not in token_texts
    assert "t" not in token_texts
    assert "p" not in token_texts


def test_cbi_joining():
    raw = "Calling from c b i headquarters"
    norm, tokens = normalise(raw, "hinglish")
    token_texts = [t.text for t in tokens]
    assert "cbi" in token_texts


def test_character_offset_mapping():
    raw = "Your parcel at Mumbai customs has narcotics."
    norm, tokens = normalise(raw, "en")
    for t in tokens:
        orig_slice = raw[t.start:t.end]
        # Orig slice (lowercased) should match token text
        assert orig_slice.lower() == t.text.lower()


def test_acronym_offset_mapping():
    raw = "Share your o t p now"
    norm, tokens = normalise(raw, "en")
    otp_tok = next(t for t in tokens if t.text == "otp")
    orig_slice = raw[otp_tok.start:otp_tok.end]
    assert orig_slice == "o t p"
