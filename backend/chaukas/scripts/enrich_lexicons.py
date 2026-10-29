"""Enrich en.yaml and hinglish.yaml with all PRD §6.3 tokens and phrases."""

from __future__ import annotations

import yaml
from pathlib import Path

LEXICON_DIR = Path(__file__).resolve().parent.parent / "engine" / "lexicon"

EN_ADDITIONS = {
    "credential_request": [
        "OTP", "PIN", "CVV", "password", "UPI PIN", "Aadhaar number", "card number",
        "verification code", "six digit code", "6 digit code", "security code",
        "read out the OTP", "share the OTP", "provide the OTP", "send the OTP",
        "tell me the OTP", "secret code", "one time password"
    ],
    "transfer_demand": [
        "transfer", "safe account", "RBI account", "verification amount", "security deposit",
        "pay the fine", "pay customs duty", "send the money", "transfer the amount",
        "transfer immediately", "UPI to this number", "deposit amount", "online transfer",
        "bail bond", "processing fee", "send the money via UPI", "refundable deposit",
        "pay fine"
    ],
    "authority_claim": [
        "police", "cyber crime", "cyber crime branch", "CBI", "ED", "TRAI", "RBI",
        "customs", "narcotics", "income tax", "inspector", "officer", "calling from",
        "this is inspector", "police department", "cyber cell", "security cell",
        "telecom authority", "customs officer", "sub-inspector"
    ],
    "digital_arrest": [
        "digital arrest", "under arrest", "warrant", "FIR", "case registered",
        "court order", "arrest warrant", "arrest order", "FIR registered",
        "digital arrest order", "non-bailable warrant"
    ],
    "accusation": [
        "money laundering", "drugs in parcel", "illegal substances", "Aadhaar misuse",
        "SIM used for illegal", "trafficking", "hawala", "illegal activity",
        "contraband", "cyber fraud", "unauthorized login", "prohibited items"
    ],
    "urgency_threat": [
        "immediately", "right now", "within 30 minutes", "within 15 minutes",
        "within 1 hour", "within 2 hours", "account will be blocked",
        "account will be suspended", "SIM block", "last warning", "otherwise arrest",
        "arrested today", "confiscated", "frozen", "today itself", "within 24 hours"
    ],
    "secrecy_isolation": [
        "don't tell anyone", "do not disconnect", "stay on video call",
        "don't tell your family", "this is confidential", "go to a separate room",
        "strictly confidential", "between you and me", "do not tell anyone",
        "not even your family", "confidential case", "keep this call strictly confidential"
    ],
    "reward_task": [
        "part-time job", "part time job", "like and share", "like and earn",
        "task", "commission", "double your money", "guaranteed returns",
        "guaranteed daily returns", "daily returns", "lucky draw", "lottery",
        "cash reward", "task commissions", "zero risk", "daily profit"
    ],
    "kyc_expiry": [
        "KYC update", "KYC expired", "KYC compliance", "KYC verification",
        "PAN update", "account will be suspended", "account will be blocked",
        "account will be deactivated", "electricity will be cut", "utility department",
        "card renewal", "mandatory KYC"
    ],
    "courier_customs": [
        "FedEx", "DHL", "courier", "parcel", "customs duty", "held at airport",
        "held at customs", "clearance fee", "clearance duties", "international parcel",
        "SpeedPost", "cargo terminal", "unpaid clearance"
    ],
    "emergency_relative": [
        "nephew", "hospital", "accident", "send money urgently", "in big trouble",
        "detained", "surgery", "urgent money", "emergency", "auntie", "uncle"
    ],
    "remote_access": [
        "AnyDesk", "TeamViewer", "QuickSupport", "screen share", "install this app",
        "APK", "click the link", "remote access", "install AnyDesk", "install"
    ],
}

HINGLISH_ADDITIONS = {
    "credential_request": [
        "OTP", "PIN", "UPI PIN", "card number", "CVV", "password", "OTP batao",
        "OTP share kijiye", "OTP dijiye", "verification code", "6 digit code",
        "code batao", "OTP send karo", "verification amount", "Aadhaar number"
    ],
    "transfer_demand": [
        "transfer", "paise bhejiye", "safe account", "RBI account", "verification amount",
        "security deposit", "fine pay kijiye", "UPI number", "advance pay",
        "transfer karein", "money transfer", "paise send karo", "account me transfer",
        "penal fine", "customs fee"
    ],
    "authority_claim": [
        "police", "cyber crime", "crime branch", "CBI", "ED", "TRAI", "RBI",
        "customs", "inspector", "officer", "se bol raha hoon", "DSP", "SP",
        "thana", "cyber cell", "telecom authority"
    ],
    "digital_arrest": [
        "digital arrest", "arrest warrant", "FIR lodge", "court order",
        "arrest ho jaoge", "non bailable warrant", "custody", "digital arrest par"
    ],
    "accusation": [
        "money laundering", "parcel me drugs", "hawala scam", "illegal SIM",
        "illegal consignment", "fake passport", "Aadhaar misuse", "blackmailing"
    ],
    "urgency_threat": [
        "turant", "abhi ke abhi", "15 minute ke andar", "30 minute ke andar",
        "account block ho jayega", "SIM block ho jayegi", "last warning",
        "aaj hi", "varna arrest", "electricity cut", "freeze ho jayega",
        "within 10 minutes", "right now", "within 1 hour"
    ],
    "secrecy_isolation": [
        "kisi ko mat batana", "ghar walon ko mat batana", "call mat kaatna",
        "video call par rahiye", "confidential case", "do not disconnect",
        "gopniya", "phone mat kaatna", "strictly confidential"
    ],
    "reward_task": [
        "part time job", "like aur share", "like karke", "task", "commission",
        "daily earnings", "profit", "lottery", "contest", "lucky draw",
        "guaranteed profit", "double returns", "cash prize"
    ],
    "kyc_expiry": [
        "KYC update", "KYC expire", "PAN update", "account block", "SIM block",
        "khata band", "electricity cut", "bill update", "KYC pending"
    ],
    "courier_customs": [
        "courier", "parcel", "customs duty", "airport par", "customs clearance",
        "parcel hold", "FedEx", "DHL", "foreign parcel"
    ],
    "emergency_relative": [
        "phas gaya", "accident", "hospital", "operation", "uncle", "bhaiya",
        "urgent paise", "papa ko mat batana", "police case", "trouble me"
    ],
    "remote_access": [
        "screen share", "AnyDesk", "QuickSupport", "TeamViewer", "APK",
        "link par click", "app download", "remote access", "download AnyDesk"
    ],
}


def enrich_file(filename: str, additions: dict, lang: str):
    path = LEXICON_DIR / filename
    with open(path, encoding="utf-8") as f:
        existing = yaml.safe_load(f)

    seen = {(e["signal"], e["value"].lower().strip()) for e in existing}

    added = 0
    for signal_id, words in additions.items():
        for val in words:
            v_clean = val.strip()
            key = (signal_id, v_clean.lower())
            if key not in seen:
                seen.add(key)
                existing.append({
                    "signal": signal_id,
                    "kind": "phrase",
                    "value": v_clean,
                    "lang": lang,
                })
                added += 1

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(existing, f, allow_unicode=True, sort_keys=False)

    print(f"Added {added} patterns to {filename} (total: {len(existing)})")


def main():
    enrich_file("en.yaml", EN_ADDITIONS, "en")
    enrich_file("hinglish.yaml", HINGLISH_ADDITIONS, "hinglish")


if __name__ == "__main__":
    main()

