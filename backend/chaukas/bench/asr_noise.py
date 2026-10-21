"""ASR noise simulation — PRD §9.3.

Seeded RNG perturbations: deletion, phonetic substitution, splitting/joining, truncation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


# Phonetic confusion pairs for Hindi/English/Hinglish
CONFUSION_TABLE = {
    # OTP variants
    "otp": ["o t p", "o.t.p", "oh tea pee", "ओ टी पी", "ओटीपी"],
    "o t p": ["otp", "ओटीपी"],
    "ओ टी पी": ["otp", "ओटीपी"],

    # PIN
    "pin": ["p i n", "पिन", "पी आई एन"],
    "पिन": ["pin"],

    # CVV
    "cvv": ["c v v", "सीवीवी", "सी वी वी"],
    "सीवीवी": ["cvv"],

    # OTP/verification
    "verification": ["verification code", "verify code", "वेरिफिकेशन", "वेरिफिकेशन कोड"],
    "code": ["कोड", "कॉड"],

    # Bank/account
    "bank": ["बैंक", "बेंक"],
    "account": ["अकाउंट", "खाता", "account number"],
    "account number": ["account no", "अकाउंट नंबर", "खाता नंबर"],

    # Transfer
    "transfer": ["ट्रांसफर", "ट्रान्सफर", "पैसे भेजो", "पैसा ट्रांसफर"],
    "send money": ["पैसे भेजो", "पैसा भेजो", "पैसे भिजवाओ"],

    # Arrest/police
    "arrest": ["अरेस्ट", "अरेस्टेड", "गिरफ्तारी"],
    "police": ["पुलिस", "पोलिस"],
    "digital arrest": ["डिजिटल अरेस्ट", "डिजिटल अरेस्ट हो गया"],

    # Urgency
    "immediately": ["तुरंत", "अभी", "abhi ke abhi"],
    "right now": ["abhi ke abhi", "turant", "अभी के अभी"],

    # Secrecy
    "don't tell": ["मत बताना", "किसी को मत बताना", "किसी को ना बताना"],
    "do not tell": ["किसी को ना बताएं", "किसी को मत बताइए"],

    # Common words
    "the": ["da", "tha"],
    "you": ["u", "you"],
    "your": ["ur", "apka", "aapka"],
    "please": ["pls", "plz"],
}


@dataclass
class ASRNoiseConfig:
    wer: float  # word error rate 0.0-0.4
    seed: int = 42


def apply_asr_noise(text: str, config: ASRNoiseConfig) -> str:
    """Apply ASR noise perturbations to text."""
    if config.wer <= 0:
        return text

    rng = random.Random(config.seed)
    words = text.split()
    if not words:
        return text

    result = []
    i = 0
    while i < len(words):
        word = words[i]
        r = rng.random()

        # Deletion
        if r < config.wer * 0.3:
            i += 1
            continue

        # Substitution
        elif r < config.wer * 0.5:
            lower = word.lower()
            if lower in CONFUSION_TABLE:
                result.append(rng.choice(CONFUSION_TABLE[lower]))
            else:
                result.append(word)
            i += 1
            continue

        # Splitting (for acronyms)
        elif r < config.wer * 0.6 and len(word) > 3 and word.isalpha():
            # Split into characters
            result.extend(list(word))
            i += 1
            continue

        # Joining (merge with next word)
        elif r < config.wer * 0.7 and i + 1 < len(words):
            result.append(word + words[i + 1])
            i += 2
            continue

        # Keep original
        else:
            result.append(word)
            i += 1

    # Truncate last 30% of words (simulate early cutoff)
    if rng.random() < 0.1:
        cutoff = max(1, int(len(result) * 0.7))
        result = result[:cutoff]

    return " ".join(result)


def apply_asr_noise_to_segments(segments: list[dict], config: ASRNoiseConfig) -> list[dict]:
    """Apply noise to a list of transcript segments."""
    rng = random.Random(config.seed)
    noisy = []
    for i, seg in enumerate(segments):
        seg_config = ASRNoiseConfig(wer=config.wer, seed=config.seed + i)
        noisy.append({
            **seg,
            "text": apply_asr_noise(seg["text"], seg_config),
        })
    return noisy