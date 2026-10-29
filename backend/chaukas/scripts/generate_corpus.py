"""Generate 90+ labelled corpus cases — PRD §9.1.

Composition:
- 50 Scam cases: Digital Arrest, KYC/OTP, Courier/Customs, Investment/Task,
  Emergency Relative, Remote Access, Electricity/SIM/Lottery.
  Variants across Hindi (Devanagari), English, and Hinglish.
- 40 Genuine cases: Bank OTP warnings, Delivery coordination, Family casual
  money chat, Customer service, Appointments, Fraud awareness broadcasts.
"""

from __future__ import annotations

import json
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"


def write_case(case_data: dict) -> None:
    path = CORPUS_DIR / f"{case_data['id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(case_data, f, indent=2, ensure_ascii=False)


def generate_all_cases() -> None:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # SCAM CASES (s-001 to s-050)
    # -------------------------------------------------------------
    scam_cases = [
        # Existing s-001 to s-005 preserved with exact same content
        {
            "id": "s-001",
            "label": "scam",
            "lang": "en",
            "tactics": ["authority_claim", "digital_arrest", "accusation", "urgency_threat", "secrecy_isolation", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello, this is Inspector Sharma from Cyber Crime Branch. I'm calling about a serious matter."},
                {"tMs": 3000, "speaker": "caller", "text": "A parcel in your name was intercepted at Mumbai airport containing illegal substances. An FIR has been registered."},
                {"tMs": 7000, "speaker": "caller", "text": "You are under digital arrest. Do not disconnect this call. Do not tell anyone, not even your family."},
                {"tMs": 11000, "speaker": "caller", "text": "Your Aadhaar was used for money laundering. The court order is being processed as we speak."},
                {"tMs": 15000, "speaker": "caller", "text": "To clear your name, you must transfer the verification amount to the safe RBI account immediately. Within 30 minutes."},
                {"tMs": 19000, "speaker": "caller", "text": "If you don't comply, you will be arrested today. This is your last warning."}
            ],
            "firstHardAskTurn": 4
        },
        {
            "id": "s-002",
            "label": "scam",
            "lang": "en",
            "tactics": ["authority_claim", "kyc_expiry", "credential_request", "urgency_threat", "secrecy_isolation"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Good morning, this is Rajesh from your bank's KYC compliance department."},
                {"tMs": 3000, "speaker": "caller", "text": "Your KYC has expired and your account will be suspended permanently if not updated today."},
                {"tMs": 6000, "speaker": "caller", "text": "For security verification, I need you to read out the OTP sent to your registered mobile number."},
                {"tMs": 9000, "speaker": "caller", "text": "Do not share this OTP with anyone else. This is a confidential bank process."},
                {"tMs": 12000, "speaker": "caller", "text": "If you don't provide the OTP within 15 minutes, your account will be frozen and you'll lose access to your funds."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-003",
            "label": "scam",
            "lang": "en",
            "tactics": ["courier_customs", "authority_claim", "accusation", "transfer_demand", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "This is FedEx customer service. Your international parcel has been held at customs."},
                {"tMs": 3000, "speaker": "caller", "text": "The parcel contains prohibited items and you need to pay customs duty of 45,000 rupees immediately."},
                {"tMs": 6000, "speaker": "caller", "text": "If not paid within 2 hours, the parcel will be seized and legal action will be taken against you."},
                {"tMs": 9000, "speaker": "caller", "text": "Please transfer the amount to this account to release your parcel. This is a government account."},
                {"tMs": 12000, "speaker": "caller", "text": "Do not discuss this with anyone. It's a confidential customs matter."}
            ],
            "firstHardAskTurn": 3
        },
        {
            "id": "s-004",
            "label": "scam",
            "lang": "en",
            "tactics": ["reward_task", "transfer_demand", "urgency_threat", "authority_claim"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Congratulations! You've been selected for a part-time job opportunity with guaranteed daily returns."},
                {"tMs": 3000, "speaker": "caller", "text": "All you need to do is like and share posts. You'll earn 5000 rupees daily with zero risk."},
                {"tMs": 6000, "speaker": "caller", "text": "To activate your account, you need to deposit a verification amount of 10,000 rupees."},
                {"tMs": 9000, "speaker": "caller", "text": "This is refundable after your first task. The offer expires in 1 hour."},
                {"tMs": 12000, "speaker": "caller", "text": "Send the money via UPI to this number right now to secure your spot."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-005",
            "label": "scam",
            "lang": "en",
            "tactics": ["emergency_relative", "urgency_threat", "transfer_demand", "secrecy_isolation"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Uncle, it's me, your nephew Rahul. I'm in big trouble."},
                {"tMs": 3000, "speaker": "caller", "text": "I had an accident and I'm at the hospital. They need 50,000 rupees for surgery right now."},
                {"tMs": 6000, "speaker": "caller", "text": "Please don't tell papa. He has a heart condition and this will kill him."},
                {"tMs": 9000, "speaker": "caller", "text": "Send the money to this UPI ID immediately. My phone is about to die."},
                {"tMs": 12000, "speaker": "caller", "text": "Please hurry, I'm scared. This is between you and me only."}
            ],
            "firstHardAskTurn": 3
        },
        # Digital Arrest in Hindi & Hinglish
        {
            "id": "s-006",
            "label": "scam",
            "lang": "hi",
            "tactics": ["authority_claim", "digital_arrest", "accusation", "secrecy_isolation", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्ते, मैं दिल्ली पुलिस क्राइम ब्रांच से सब-इंस्पेक्टर मिश्रा बोल रहा हूँ।"},
                {"tMs": 3000, "speaker": "caller", "text": "आपके आधार कार्ड से 24 फर्जी बैंक खाते खोले गए हैं और मनी लॉन्ड्रिंग हुई है।"},
                {"tMs": 6000, "speaker": "caller", "text": "सुप्रीम कोर्ट से आपके खिलाफ गैर-जमानती वारंट जारी हुआ है। आप डिजिटल अरेस्ट में हैं।"},
                {"tMs": 9000, "speaker": "caller", "text": "कॉल मत काटिए और अलग कमरे में जाइए। किसी को मत बताइए।"},
                {"tMs": 12000, "speaker": "caller", "text": "मामले की जांच के लिए तुरंत सुरक्षा राशि सरकारी सुरक्षित खाते में ट्रांसफर कीजिए।"},
                {"tMs": 15000, "speaker": "caller", "text": "अगर अभी पैसे नहीं भेजे तो तुरंत पुलिस टीम आपको अरेस्ट करने पहुंचेगी।"}
            ],
            "firstHardAskTurn": 4
        },
        {
            "id": "s-007",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["authority_claim", "digital_arrest", "accusation", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello, main CBI headquarters New Delhi se officer Verma bol raha hoon."},
                {"tMs": 3000, "speaker": "caller", "text": "Aapke naam se ek parcel Taiwan bheja gaya tha jisme narcotics aur fake passports mile hain."},
                {"tMs": 6000, "speaker": "caller", "text": "Aapke khilaf FIR lodge ho gayi hai aur aap digital arrest par hain."},
                {"tMs": 9000, "speaker": "caller", "text": "Phone disconnect mat karna varna local police station se team bhej kar lockup me daal denge."},
                {"tMs": 12000, "speaker": "caller", "text": "Apna account verify karane ke liye verification amount RBI safe account me transfer karein right now."}
            ],
            "firstHardAskTurn": 4
        },
        {
            "id": "s-008",
            "label": "scam",
            "lang": "hi",
            "tactics": ["authority_claim", "digital_arrest", "accusation", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "यह ट्राई और मुंबई पुलिस का आपातकालीन कॉल है।"},
                {"tMs": 3000, "speaker": "caller", "text": "आपके मोबाइल नंबर से गैरकानूनी संदेश भेजे गए हैं। आपके खिलाफ केस दर्ज हुआ है।"},
                {"tMs": 6000, "speaker": "caller", "text": "आप अभी इसी वक्त डिजिटल अरेस्ट के तहत हैं। वीडियो कॉल पर रहिए।"},
                {"tMs": 9000, "speaker": "caller", "text": "आपको जुर्माना भरना होगा। अपने खाते से सरकारी खाते में तुरंत ट्रांसफर करें।"}
            ],
            "firstHardAskTurn": 3
        },
        {
            "id": "s-009",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["authority_claim", "digital_arrest", "secrecy_isolation", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Attention please, this is Enforcement Directorate ED Mumbai branch."},
                {"tMs": 3000, "speaker": "caller", "text": "Aapka naam 50 crore ke hawala scam me aaya hai. Court arrest warrant ready hai."},
                {"tMs": 6000, "speaker": "caller", "text": "Ghar walon ko mat batana, this is high level confidential case. Do not disconnect."},
                {"tMs": 9000, "speaker": "caller", "text": "Agar arrest se bachna hai to security deposit paise bhejiye is government verification account me."}
            ],
            "firstHardAskTurn": 3
        },
        {
            "id": "s-010",
            "label": "scam",
            "lang": "en",
            "tactics": ["authority_claim", "digital_arrest", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "This is Officer Rathore from National Cyber Security Cell."},
                {"tMs": 3000, "speaker": "caller", "text": "Your national ID has been linked to severe cyber fraud activities."},
                {"tMs": 6000, "speaker": "caller", "text": "A digital arrest order is active on you right now. Stay on this line."},
                {"tMs": 9000, "speaker": "caller", "text": "To stop immediate police dispatch, transfer the bail bond amount to RBI clearing portal."}
            ],
            "firstHardAskTurn": 3
        },
        {
            "id": "s-011",
            "label": "scam",
            "lang": "hi",
            "tactics": ["authority_claim", "digital_arrest", "secrecy_isolation", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "साइबर सेल हेडक्वार्टर से डीएसपी यादव बोल रहा हूँ।"},
                {"tMs": 3000, "speaker": "caller", "text": "आपके पैन कार्ड से गैरकानूनी फंड्स ट्रांसफर हुए हैं। आप अरेस्ट हैं।"},
                {"tMs": 6000, "speaker": "caller", "text": "किसी को मत बताइए, कमरे का दरवाजा बंद कर लीजिए और कॉल चालू रखिए।"},
                {"tMs": 9000, "speaker": "caller", "text": "सरकारी खाते में तुरंत पैसे भेजिए अपनी बेगुनाही साबित करने के लिए।"}
            ],
            "firstHardAskTurn": 3
        },
        {
            "id": "s-012",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["authority_claim", "digital_arrest", "accusation", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Main Telecom Authority TRAI aur Crime Branch se bol raha hoon."},
                {"tMs": 3000, "speaker": "caller", "text": "Aapke Aadhaar se illegal SIM issue hui hai aur blackmailing ho rahi hai."},
                {"tMs": 6000, "speaker": "caller", "text": "Aap digital arrest me hain. 15 minute ke andar arrest warrant execute ho jayega."},
                {"tMs": 9000, "speaker": "caller", "text": "Penal fine pay kijiye safe RBI account me urgently."}
            ],
            "firstHardAskTurn": 3
        },
        # KYC / OTP Scams
        {
            "id": "s-013",
            "label": "scam",
            "lang": "hi",
            "tactics": ["authority_claim", "kyc_expiry", "credential_request", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्कार, भारतीय स्टेट बैंक कस्टमर सर्विस से बोल रहा हूँ।"},
                {"tMs": 3000, "speaker": "caller", "text": "आपका बैंक खाता केवाईसी अपडेट न होने के कारण आज बंद हो जाएगा।"},
                {"tMs": 6000, "speaker": "caller", "text": "केवाईसी रिन्यू करने के लिए आपके फोन पर 6 अंकों का ओटीपी भेजा गया है।"},
                {"tMs": 9000, "speaker": "caller", "text": "तुरंत वह ओटीपी बताइए वरना एटीएम और नेटबैंकिंग ब्लॉक हो जाएगी।"}
            ],
            "firstHardAskTurn": 3
        },
        {
            "id": "s-014",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["authority_claim", "kyc_expiry", "credential_request", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Sir main PayTM KYC verification desk se bol raha hoon."},
                {"tMs": 3000, "speaker": "caller", "text": "Aapka wallet aur UPI KYC expire ho chuka hai. Account block ho jayega."},
                {"tMs": 6000, "caller": "caller", "text": "Abhi aapke mobile par verification code aayega, turant OTP batao."},
                {"tMs": 9000, "caller": "caller", "text": "Code nahi doge to sara balance freeze ho jayega within 10 minutes."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-015",
            "label": "scam",
            "lang": "en",
            "tactics": ["kyc_expiry", "credential_request", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Dear customer, this is an urgent call regarding your credit card renewal."},
                {"tMs": 3000, "speaker": "caller", "text": "Your card has been flagged for mandatory KYC update or it will be deactivated today."},
                {"tMs": 6000, "speaker": "caller", "text": "Please read out your 16-digit card number and the CVV on the back."},
                {"tMs": 9000, "speaker": "caller", "text": "Now tell me the one time password received on SMS to complete the process."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-016",
            "label": "scam",
            "lang": "hi",
            "tactics": ["authority_claim", "kyc_expiry", "credential_request", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "बैंक मैनेजर शर्मा बात कर रहा हूँ बैंक ऑफ बड़ौदा से।"},
                {"tMs": 3000, "speaker": "caller", "text": "आरबीआई गाइडलाइन के तहत आपका पैन कार्ड लिंक नहीं है। बैंक खाता बंद होने वाला है।"},
                {"tMs": 6000, "speaker": "caller", "text": "अभी मैसेज में आया ओटीपी दीजिए ताकि खाता चालू रखा जा सके।"}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-017",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["kyc_expiry", "credential_request", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Sir aapke Airtel SIM card ka KYC pending hai."},
                {"tMs": 3000, "speaker": "caller", "text": "TRAI regulations ke according 24 ghante me SIM block ho jayegi."},
                {"tMs": 6000, "speaker": "caller", "text": "Verification ke liye message me aaya hua OTP share kijiye right now."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-018",
            "label": "scam",
            "lang": "en",
            "tactics": ["kyc_expiry", "credential_request", "secrecy_isolation"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello, ICICI Bank risk department calling."},
                {"tMs": 3000, "speaker": "caller", "text": "Suspicious login attempts detected from another device. Your net banking is locked."},
                {"tMs": 6000, "speaker": "caller", "text": "To secure your account, state your secret UPI PIN and verification code."},
                {"tMs": 9000, "speaker": "caller", "text": "Keep this call strictly confidential and do not disconnect."}
            ],
            "firstHardAskTurn": 2
        },
        # Courier / Customs Scams
        {
            "id": "s-019",
            "label": "scam",
            "lang": "hi",
            "tactics": ["courier_customs", "accusation", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "डीएचएल कूरियर मुंबई हेड ऑफिस से कॉल है।"},
                {"tMs": 3000, "speaker": "caller", "text": "आपके नाम पर विदेश से पार्सल आया है जो कस्टम ड्यूटी न भरने के कारण एयरपोर्ट पर रोक लिया गया है।"},
                {"tMs": 6000, "speaker": "caller", "text": "कस्टम ड्यूटी तुरंत भरिए, जुर्माना 25,000 रुपये है।"},
                {"tMs": 9000, "speaker": "caller", "text": "अगर 1 घंटे में पैसे ट्रांसफर नहीं किए तो कानूनी कार्रवाई होगी।"}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-020",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["courier_customs", "authority_claim", "accusation", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Customs clearance department Delhi airport se officer bol raha hoon."},
                {"tMs": 3000, "speaker": "caller", "text": "Aapke parcel me contraband gold aur foreign currency mili hai."},
                {"tMs": 6000, "speaker": "caller", "text": "Customs clearance fee pay karni hogi government clearing account me transfer karke."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-021",
            "label": "scam",
            "lang": "en",
            "tactics": ["courier_customs", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "This is SpeedPost international delivery center."},
                {"tMs": 3000, "speaker": "caller", "text": "A high value parcel sent to your address is held for unpaid clearance duties."},
                {"tMs": 6000, "speaker": "caller", "text": "You must pay the fine and clearance fee immediately via online transfer or it will be confiscated."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-022",
            "label": "scam",
            "lang": "hi",
            "tactics": ["courier_customs", "authority_claim", "accusation", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "कस्टम अधिकारी बोल रहा हूँ। आपके पार्सल में गैरकानूनी दवाएं पाई गई हैं।"},
                {"tMs": 3000, "speaker": "caller", "text": "एफआईआर से बचने के लिए तुरंत पेनल्टी राशि ट्रांसफर कीजिए।"}
            ],
            "firstHardAskTurn": 1
        },
        # Investment / Task Scams
        {
            "id": "s-023",
            "label": "scam",
            "lang": "hi",
            "tactics": ["reward_task", "transfer_demand", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्ते, क्या आप घर बैठे पार्ट-टाइम जॉब करके रोजाना 3000 से 8000 रुपये कमाना चाहते हैं?"},
                {"tMs": 3000, "speaker": "caller", "text": "बस होटल और वीडियो को लाइक करना है। गारंटेड रिटर्न और तुरंत कमीशन मिलेगा।"},
                {"tMs": 6000, "speaker": "caller", "text": "अगला वीआईपी टास्क अनलॉक करने के लिए 15,000 रुपये डिपॉजिट करने होंगे।"},
                {"tMs": 9000, "speaker": "caller", "text": "यह पैसा डबल होकर आधे घंटे में वापस मिल जाएगा। तुरंत यूपीआई करिए।"}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-024",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["reward_task", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello ma'am, global crypto investment platform se baat kar raha hoon."},
                {"tMs": 3000, "speaker": "caller", "text": "Hamare task based trading me 200% guaranteed profit milta hai within 24 hours."},
                {"tMs": 6000, "speaker": "caller", "text": "Start karne ke liye minimum investment transfer kijiye hamare designated account me."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-025",
            "label": "scam",
            "lang": "en",
            "tactics": ["reward_task", "transfer_demand", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Special hiring team from Amazon reviews project calling."},
                {"tMs": 3000, "speaker": "caller", "text": "You earned 1200 rupees on level 1 tasks. Level 2 has 20,000 rupees payout."},
                {"tMs": 6000, "speaker": "caller", "text": "To claim your earnings you must deposit a security deposit of 8,000 rupees right now."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-026",
            "label": "scam",
            "lang": "hi",
            "tactics": ["reward_task", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "टेलीग्राम टास्क ग्रुप में आपका स्वागत है।"},
                {"tMs": 3000, "speaker": "caller", "text": "टास्क पूरा करके भारी प्रॉफिट कमाएं। लकी ड्रा और डबल मनी ऑफर है।"},
                {"tMs": 6000, "speaker": "caller", "text": "प्रीमियम टास्क के लिए पैसे भेजिए और तुरंत विड्रॉल लीजिए।"}
            ],
            "firstHardAskTurn": 2
        },
        # Emergency Relative Scams
        {
            "id": "s-027",
            "label": "scam",
            "lang": "hi",
            "tactics": ["emergency_relative", "urgency_threat", "transfer_demand", "secrecy_isolation"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "चाचाजी, मैं रोहित बोल रहा हूँ। बहुत बड़ी मुसीबत में फँस गया हूँ।"},
                {"tMs": 3000, "speaker": "caller", "text": "मेरी गाड़ी से एक्सीडेंट हो गया है और पुलिस ने पकड़ लिया है।"},
                {"tMs": 6000, "speaker": "caller", "text": "पापा को मत बताइएगा नहीं तो उनकी तबीयत खराब हो जाएगी।"},
                {"tMs": 9000, "speaker": "caller", "text": "वकील को देने के लिए तुरंत 35,000 रुपये इस नंबर पर ट्रांसफर कर दीजिए प्लीज।"}
            ],
            "firstHardAskTurn": 3
        },
        {
            "id": "s-028",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["emergency_relative", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Bhaiya main phas gaya hoon police case me college ke bahar."},
                {"tMs": 3000, "speaker": "caller", "text": "Hospital aur settlement ke liye urgent paise chahiye, phone confiscate hone wala hai."},
                {"tMs": 6000, "speaker": "caller", "text": "Ghar pe mat batana, send money urgently to this UPI ID right now."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-029",
            "label": "scam",
            "lang": "en",
            "tactics": ["emergency_relative", "urgency_threat", "transfer_demand", "secrecy_isolation"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Auntie, this is your nephew Amit. I lost my wallet abroad and I'm detained at the precinct."},
                {"tMs": 3000, "speaker": "caller", "text": "Please don't inform my parents, they will panic."},
                {"tMs": 6000, "speaker": "caller", "text": "I urgently need 40,000 rupees for bail. Please transfer immediately to my friend's account."}
            ],
            "firstHardAskTurn": 2
        },
        # Remote Access Scams
        {
            "id": "s-030",
            "label": "scam",
            "lang": "en",
            "tactics": ["remote_access", "authority_claim", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "This is technical support from Microsoft and your bank's IT cell."},
                {"tMs": 3000, "speaker": "caller", "text": "A severe malware is draining funds from your device right now."},
                {"tMs": 6000, "speaker": "caller", "text": "Go to Play Store immediately and install AnyDesk or QuickSupport application."},
                {"tMs": 9000, "speaker": "caller", "text": "Share your 9-digit screen share code so our technician can remove the virus."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-031",
            "label": "scam",
            "lang": "hi",
            "tactics": ["remote_access", "authority_claim", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "एसबीआई बैंक टेक्निकल डिपार्टमेंट से बोल रहा हूँ।"},
                {"tMs": 3000, "speaker": "caller", "text": "आपका योनो ऐप हैक हो गया है। इसे ठीक करने के लिए स्क्रीन शेयर करना पड़ेगा।"},
                {"tMs": 6000, "speaker": "caller", "text": "हम आपको एक लिंक भेज रहे हैं, उस लिंक पर क्लिक करके एपीके ऐप इंस्टॉल कीजिए।"},
                {"tMs": 9000, "speaker": "caller", "text": "फिर टीमव्यूअर या एनीडेस्क कोड बताइए ताकि रिमोट एक्सेस हो सके।"}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-032",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["remote_access", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Aapka router aur banking app compromised hai."},
                {"tMs": 3000, "speaker": "caller", "text": "Screen share chalu kijiye aur AnyDesk download karo turant."},
                {"tMs": 6000, "speaker": "caller", "text": "Apna remote access code provide karo to secure your mobile."}
            ],
            "firstHardAskTurn": 1
        },
        # Electricity Bill / Utility Cut Scams
        {
            "id": "s-033",
            "label": "scam",
            "lang": "hi",
            "tactics": ["kyc_expiry", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "बिजली विभाग हेड ऑफिस से सूचना।"},
                {"tMs": 3000, "speaker": "caller", "text": "आपका पिछला बिजली बिल अपडेट नहीं हुआ है। आज रात 9 बजे बिजली काट दी जाएगी।"},
                {"tMs": 6000, "speaker": "caller", "text": "कनेक्शन कटने से बचाने के लिए अभी इसी नंबर पर बिल की बकाया राशि तुरंत ट्रांसफर करें।"}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-034",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["kyc_expiry", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Electricity board official calling."},
                {"tMs": 3000, "speaker": "caller", "text": "Your bill payment failed and electricity will be cut within 30 minutes."},
                {"tMs": 6000, "speaker": "caller", "text": "Disconnection avoid karne ke liye paise bhejiye abhi ke abhi is UPI par."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-035",
            "label": "scam",
            "lang": "en",
            "tactics": ["kyc_expiry", "urgency_threat", "credential_request"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Water and power utility department notice."},
                {"tMs": 3000, "speaker": "caller", "text": "Immediate disconnection scheduled for your meter."},
                {"tMs": 6000, "speaker": "caller", "text": "To stop disconnection officer, share your banking OTP to process emergency payment."}
            ],
            "firstHardAskTurn": 2
        },
        # Lottery / Reward Scams
        {
            "id": "s-036",
            "label": "scam",
            "lang": "hi",
            "tactics": ["reward_task", "transfer_demand", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "बधाई हो! केबीसी और कौन बनेगा करोड़पति लकी ड्रा में आपकी 25 लाख रुपये की लॉटरी लगी है।"},
                {"tMs": 3000, "speaker": "caller", "text": "इनाम की राशि आपके खाते में भेजने के लिए केवल सरकारी टैक्स और प्रोसेसिंग फीस 12,500 रुपये ट्रांसफर करें।"},
                {"tMs": 6000, "speaker": "caller", "text": "यह ऑफर आज ही तक है, तुरंत पैसे भेजकर अपना चेक प्राप्त करें।"}
            ],
            "firstHardAskTurn": 1
        },
        {
            "id": "s-037",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["reward_task", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Sir aapne online contest me Tata Safari car ya 15 lakh cash prize jeeta hai."},
                {"tMs": 3000, "speaker": "caller", "text": "Prize release karane ke liye GST amount transfer kijiye is account me today."}
            ],
            "firstHardAskTurn": 1
        },
        # Adversarial Variants (Euphemisms, subtle wording, code-mixing)
        {
            "id": "s-038",
            "label": "scam",
            "lang": "en",
            "tactics": ["authority_claim", "credential_request"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Good afternoon, I am calling on behalf of the banking ombudsman security committee."},
                {"tMs": 3000, "speaker": "caller", "text": "We are conducting a routine verification of active account credentials."},
                {"tMs": 6000, "speaker": "caller", "text": "Could you kindly read out the six-digit verification code you just received on your handset?"}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-039",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["authority_claim", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Namaste ji, main Reserve Bank verification cell se consultant bol raha hoon."},
                {"tMs": 3000, "speaker": "caller", "text": "Aapke account security score audit ke liye mandatory balance validation required hai."},
                {"tMs": 6000, "speaker": "caller", "text": "Aap ek temporary refundable verification amount transfer kijiye central holding account me."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-040",
            "label": "scam",
            "lang": "hi",
            "tactics": ["authority_claim", "digital_arrest", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "मैं विशेष जांच अधिकारी हूँ। आपके विरुद्ध जांच आयोग ने नोटिस भेजा है।"},
                {"tMs": 3000, "speaker": "caller", "text": "आपकी डिजिटल उपस्थिति अनिवार्य है। आप हिरासत में समझे जाएंगे।"},
                {"tMs": 6000, "speaker": "caller", "text": "सुरक्षा गारंटी राशि जमा करने के लिए तुरंत खाते में पैसे ट्रांसफर कीजिए।"}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-041",
            "label": "scam",
            "lang": "en",
            "tactics": ["authority_claim", "accusation", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Internal Revenue and Income Tax Department automated legal notice."},
                {"tMs": 3000, "speaker": "caller", "text": "Tax evasion case registered. Warrant issued under your Aadhaar number."},
                {"tMs": 6000, "speaker": "caller", "text": "Pay the fine immediately to avoid same-day arrest and property confiscation."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-042",
            "label": "scam",
            "lang": "hi",
            "tactics": ["kyc_expiry", "credential_request"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्ते, आपका आधार कार्ड बैंक खाते से अनलिंक हो गया है।"},
                {"tMs": 3000, "speaker": "caller", "text": "प्रमाणीकरण कोड जो आपके फोन पर आया है वह ओटीपी बताइए।"}
            ],
            "firstHardAskTurn": 1
        },
        {
            "id": "s-043",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["reward_task", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Work from home part time job. Earn 2000 rupees daily liking YouTube videos."},
                {"tMs": 3000, "speaker": "caller", "text": "Enrollment complete karne ke liye registration fee transfer kijiye is number par."}
            ],
            "firstHardAskTurn": 1
        },
        {
            "id": "s-044",
            "label": "scam",
            "lang": "en",
            "tactics": ["courier_customs", "accusation", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Customs inspection desk Mumbai cargo terminal."},
                {"tMs": 3000, "speaker": "caller", "text": "Parcel held containing undeclared jewelry and electronic gadgets."},
                {"tMs": 6000, "speaker": "caller", "text": "Release fine must be transferred to the customs duty account within 1 hour."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-045",
            "label": "scam",
            "lang": "hi",
            "tactics": ["emergency_relative", "transfer_demand", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "भैया, मैं अस्पताल में हूँ, बहुत तेज चोट लगी है।"},
                {"tMs": 3000, "speaker": "caller", "text": "डॉक्टर ऑपरेशन शुरू नहीं कर रहे। तुरंत 20,000 रुपये भेज दीजिए अभी के अभी।"}
            ],
            "firstHardAskTurn": 1
        },
        {
            "id": "s-046",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["authority_claim", "secrecy_isolation", "credential_request"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Police cyber crime investigation department se officer बोल रहा हूँ."},
                {"tMs": 3000, "speaker": "caller", "text": "Call mat katiye, this matter is gopniya. Kisi ko mat batana."},
                {"tMs": 6000, "speaker": "caller", "text": "Security clearance ke liye phone par aaya hua verification code OTP bataiye."}
            ],
            "firstHardAskTurn": 2
        },
        {
            "id": "s-047",
            "label": "scam",
            "lang": "en",
            "tactics": ["remote_access", "credential_request"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "This is bank online security cell. We noticed unauthorized login."},
                {"tMs": 3000, "speaker": "caller", "text": "Please open screen share and install the APK link we sent."},
                {"tMs": 6000, "speaker": "caller", "text": "Now type your card PIN to verify your identity on the app."}
            ],
            "firstHardAskTurn": 1
        },
        {
            "id": "s-048",
            "label": "scam",
            "lang": "hi",
            "tactics": ["authority_claim", "digital_arrest", "urgency_threat", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "सीबीआई हेडक्वार्टर। आपके खिलाफ अरेस्ट वारंट जारी हुआ है।"},
                {"tMs": 3000, "speaker": "caller", "text": "डिजिटल अरेस्ट लागू है। तुरंत 50,000 रुपये सरकारी सुरक्षित खाते में ट्रांसफर करें।"}
            ],
            "firstHardAskTurn": 1
        },
        {
            "id": "s-049",
            "label": "scam",
            "lang": "hinglish",
            "tactics": ["kyc_expiry", "credential_request", "urgency_threat"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Aapka bank khata band hone wala hai. KYC update mandatory hai."},
                {"tMs": 3000, "speaker": "caller", "text": "Turant SMS wala OTP batao varna account will be blocked today."}
            ],
            "firstHardAskTurn": 1
        },
        {
            "id": "s-050",
            "label": "scam",
            "lang": "en",
            "tactics": ["reward_task", "transfer_demand"],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Congratulations, you won a cash reward in our lucky draw anniversary."},
                {"tMs": 3000, "speaker": "caller", "text": "Pay the processing fee of 5,000 rupees to our official account to claim your reward."}
            ],
            "firstHardAskTurn": 1
        },
    ]

    # -------------------------------------------------------------
    # GENUINE CASES (g-001 to g-040)
    # -------------------------------------------------------------
    genuine_cases = [
        # Preserved existing g-001 to g-004
        {
            "id": "g-001",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello, this is a courtesy call from HDFC Bank. We're informing you about a recent transaction on your credit card."},
                {"tMs": 3000, "speaker": "caller", "text": "A transaction of 12,500 rupees was made at Amazon yesterday. If this wasn't you, please call the number on the back of your card."},
                {"tMs": 6000, "speaker": "caller", "text": "Remember, we will never ask for your OTP, PIN, or password. Never share these with anyone."},
                {"tMs": 9000, "speaker": "caller", "text": "Thank you for banking with HDFC. Have a nice day."}
            ]
        },
        {
            "id": "g-002",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello, this is Blue Dart courier. Your package is out for delivery today."},
                {"tMs": 3000, "speaker": "caller", "text": "Could you please confirm the landmark near your address for easier delivery?"},
                {"tMs": 6000, "speaker": "caller", "text": "The tracking number is BD123456789. You can track it on our website."},
                {"tMs": 9000, "speaker": "caller", "text": "Thank you, have a great day!"}
            ]
        },
        {
            "id": "g-003",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hi mom, it's me. Just calling to ask what's for dinner tonight."},
                {"tMs": 3000, "speaker": "caller", "text": "Oh, and I'm sending 5000 rupees for your birthday gift. Should reach by tomorrow."},
                {"tMs": 6000, "speaker": "caller", "text": "No rush, just wanted to let you know. Love you, bye!"}
            ]
        },
        {
            "id": "g-004",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "This is a fraud awareness message from the National Cyber Crime Helpline."},
                {"tMs": 3000, "speaker": "caller", "text": "Scammers may claim to be police, CBI, or bank officials and ask for OTP or money transfers."},
                {"tMs": 6000, "speaker": "caller", "text": "Remember, no real officer will ask for OTP, PIN, or tell you to stay on a video call."},
                {"tMs": 9000, "speaker": "caller", "text": "If you receive such a call, hang up and call 1930 immediately."}
            ]
        },
        # Genuine Bank Calls with Warning Framing (Hindi, English, Hinglish)
        {
            "id": "g-005",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्कार, भारतीय स्टेट बैंक सुरक्षा प्रकोष्ठ से यह एक सतर्कता कॉल है।"},
                {"tMs": 3000, "speaker": "caller", "text": "हम आपको सूचित करना चाहते हैं कि बैंक कभी भी आपका ओटीपी, पिन या पासवर्ड फोन पर नहीं मांगता।"},
                {"tMs": 6000, "speaker": "caller", "text": "अपना ओटीपी किसी को न बताएं, सावधान रहें। किसी भी समस्या के लिए शाखा से संपर्क करें।"}
            ]
        },
        {
            "id": "g-006",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "ICICI Bank customer service se call hai. Aapke account me auto-debit set hua hai."},
                {"tMs": 3000, "speaker": "caller", "text": "Remember bank officials will never ask for your confidential details. OTP kisi ko share mat karna."},
                {"tMs": 6000, "speaker": "caller", "text": "If you did not initiate this, please call the number on your passbook."}
            ]
        },
        {
            "id": "g-007",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Good morning, Axis Bank credit card division calling regarding your reward points balance."},
                {"tMs": 3000, "speaker": "caller", "text": "You have 4,000 points expiring next month. You can redeem them through our official mobile app."},
                {"tMs": 6000, "speaker": "caller", "text": "Please note we do not ask for card details or one time passwords over the phone."}
            ]
        },
        {
            "id": "g-008",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "पंजाब नेशनल बैंक से नमस्कार। आपकी फिक्स्ड डिपॉजिट मैच्योर हो गई है।"},
                {"tMs": 3000, "speaker": "caller", "text": "रिन्यू कराने के लिए कृपया अपनी निकटतम बैंक शाखा में पधारें।"},
                {"tMs": 6000, "speaker": "caller", "text": "कृपया ध्यान दें कि फोन पर कोई व्यक्तिगत जानकारी या पासवर्ड किसी को न दें।"}
            ]
        },
        {
            "id": "g-009",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello, Kotak Bank security alert. We noticed a new device login to your mobile app."},
                {"tMs": 3000, "speaker": "caller", "text": "If this was you, no action needed. Agar aap nahi the to apna card block kijiye via app."},
                {"tMs": 6000, "speaker": "caller", "text": "Never share your net banking password or OTP with anyone."}
            ]
        },
        {
            "id": "g-010",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Standard Chartered security advisory. Beware of fake calls pretending to be police or customs."},
                {"tMs": 3000, "speaker": "caller", "text": "Never transfer money to any unknown account. Police never conducts digital arrest over phone."},
                {"tMs": 6000, "speaker": "caller", "text": "Stay vigilant and report suspicious calls to cyber helpline 1930."}
            ]
        },
        # Genuine Delivery / Logistics Calls
        {
            "id": "g-011",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "भैया, मैं स्विगी जोमैटो डिलीवरी से बोल रहा हूँ, आपकी सोसाइटी के गेट पर खड़ा हूँ।"},
                {"tMs": 3000, "speaker": "caller", "text": "गार्ड साहब एंट्री नहीं दे रहे, कृपया इंटरकॉम पर बात कर लीजिए।"},
                {"tMs": 6000, "speaker": "caller", "text": "धन्यवाद, मैं पार्सल ऊपर लेकर आ रहा हूँ।"}
            ]
        },
        {
            "id": "g-012",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello sir, Amazon delivery agent bol raha hoon. Aap ghar par hain?"},
                {"tMs": 3000, "speaker": "caller", "text": "Aapka package deliver karna hai. Gate par rakh doon ya neighbour ko de doon?"},
                {"tMs": 6000, "speaker": "caller", "text": "Okay sir, thank you so much."}
            ]
        },
        {
            "id": "g-013",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Good afternoon, Delhivery courier representative here."},
                {"tMs": 3000, "speaker": "caller", "text": "Your shipment arrives between 2 PM and 5 PM today."},
                {"tMs": 6000, "speaker": "caller", "text": "Please keep exact change ready if it is a cash on delivery order."}
            ]
        },
        {
            "id": "g-014",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्कार, फ्लिपकार्ट से डिलीवरी बॉय बोल रहा हूँ। आपके फ्लैट नंबर 302 का रास्ता किधर से है?"},
                {"tMs": 3000, "speaker": "caller", "text": "हाँ जी, पार्क के सामने वाला ब्लॉक। धन्यवाद, मैं पहुंच रहा हूँ।"}
            ]
        },
        {
            "id": "g-015",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Sir main Blinkit se bol raha hoon, 5 minute me aapka grocery order deliver ho jayega."},
                {"tMs": 3000, "speaker": "caller", "text": "Gate open kar dijiye please."}
            ]
        },
        {
            "id": "g-016",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello, Uber driver here. I have arrived at your pickup location near the metro station."},
                {"tMs": 3000, "speaker": "caller", "text": "Waiting right outside pillar number 42."}
            ]
        },
        # Genuine Family & Friends (Mentions Money casually in normal context)
        {
            "id": "g-017",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्ते दीदी, कैसी हो? सब ठीक-ठाक है घर पर?"},
                {"tMs": 3000, "speaker": "caller", "text": "मैं बाजार गया था तो बच्चों के लिए कुछ कपड़े और मिठाई ले ली है।"},
                {"tMs": 6000, "speaker": "caller", "text": "अगले हफ्ते जब घर आऊंगा तो साथ ले आऊंगा। चलो बाद में आराम से बात करते हैं।"}
            ]
        },
        {
            "id": "g-018",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Arre yaar Sunil, kal dinner ka kya plan hai?"},
                {"tMs": 3000, "speaker": "caller", "text": "Maine movie ticket book kar di hai, total 800 rupees hua tha. Kal milkar hisaab kar lenge."},
                {"tMs": 6000, "speaker": "caller", "text": "Shaam ko 7 baje milte hain mall me."}
            ]
        },
        {
            "id": "g-019",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hey dad, just checking in. Hope your doctor appointment went smoothly today."},
                {"tMs": 3000, "speaker": "caller", "text": "I will transfer my share of the house maintenance fee over the weekend."},
                {"tMs": 6000, "speaker": "caller", "text": "Take care and tell mom I said hi!"}
            ]
        },
        {
            "id": "g-020",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "अरे भाई, स्कूल की फीस जमा कर दी क्या? मुझे बताना कितना खर्चा आया।"},
                {"tMs": 3000, "speaker": "caller", "text": "शाम को चाय पर बात करते हैं।"}
            ]
        },
        {
            "id": "g-021",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hi Pooja, kal trip ke liye packing shuru ki?"},
                {"tMs": 3000, "speaker": "caller", "text": "Hotel advance pay kar diya tha maine, no worries. Kal subah flight hai."}
            ]
        },
        {
            "id": "g-022",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello grandma, happy anniversary to you and grandpa!"},
                {"tMs": 3000, "speaker": "caller", "text": "We ordered some sweets for you that should arrive this evening. Have a wonderful celebration!"}
            ]
        },
        {
            "id": "g-023",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "बेटा, ट्रेन में बैठ गए क्या? टिकट संभाल कर रखना।"},
                {"tMs": 3000, "speaker": "caller", "text": "स्टेशन पहुंचकर फोन कर देना।"}
            ]
        },
        {
            "id": "g-024",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Bhai groceries le aaya main, bill receipt table par rakh di hai."},
                {"tMs": 3000, "speaker": "caller", "text": "Shaam ko chai banate hain."}
            ]
        },
        # Genuine Customer Care & Service
        {
            "id": "g-025",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Good day, calling from ACT Fibernet customer support regarding ticket number 98432."},
                {"tMs": 3000, "speaker": "caller", "text": "Our field engineer has repaired the optical fiber in your sector. Can you verify your internet light?"},
                {"tMs": 6000, "speaker": "caller", "text": "Great, the connection is restored. We will close this ticket now. Thank you."}
            ]
        },
        {
            "id": "g-026",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्कार, इंडेन गैस बुकिंग सेवा से कॉल है।"},
                {"tMs": 3000, "speaker": "caller", "text": "आपका एलपीजी सिलेंडर कल दोपहर तक डिलीवर हो जाएगा।"},
                {"tMs": 6000, "speaker": "caller", "text": "कृपया डिलीवरी के समय खाली सिलेंडर तैयार रखें। धन्यवाद।"}
            ]
        },
        {
            "id": "g-027",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "IndiGo airlines customer care se call hai regarding flight 6E-204."},
                {"tMs": 3000, "speaker": "caller", "text": "Due to weather conditions, departure time is rescheduled to 4 PM."},
                {"tMs": 6000, "speaker": "caller", "text": "Updated boarding pass aapke email par bhej diya gaya hai."}
            ]
        },
        {
            "id": "g-028",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Urban Company appliance repair technician here. Confirming our visit for AC servicing at 11 AM today."},
                {"tMs": 3000, "speaker": "caller", "text": "Please ensure the unit is accessible. See you shortly."}
            ]
        },
        {
            "id": "g-029",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्कार, टाटा स्काई डीटीएच सर्विस। आपका मासिक रिचार्ज सफलतापूर्वक हो गया है।"},
                {"tMs": 3000, "speaker": "caller", "text": "सभी चैनल सक्रिय हैं। किसी भी सहायता के लिए हमारी वेबसाइट पर जाएं।"}
            ]
        },
        {
            "id": "g-030",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Maruti Suzuki service station se baat kar raha hoon sir."},
                {"tMs": 3000, "speaker": "caller", "text": "Aapki car ki periodic maintenance complete ho gayi hai aur car ready hai pickup ke liye."}
            ]
        },
        # Genuine Business & Appointments
        {
            "id": "g-031",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Good morning, this is Apollo Clinic front desk."},
                {"tMs": 3000, "speaker": "caller", "text": "Confirming your consultation with Dr. Mehta for tomorrow at 10:30 AM."},
                {"tMs": 6000, "speaker": "caller", "text": "Please bring your previous medical records and arrive 10 minutes early."}
            ]
        },
        {
            "id": "g-032",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्कार, दंत चिकित्सालय से कॉल है। कल दोपहर 3 बजे आपकी रूट कैनाल सिटिंग है।"},
                {"tMs": 3000, "speaker": "caller", "text": "कृपया समय पर पहुंचने का कष्ट करें।"}
            ]
        },
        {
            "id": "g-033",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Hello, HR department se calling for tomorrow's video interview."},
                {"tMs": 3000, "speaker": "caller", "text": "Google Meet link has been sent to your registered email address."}
            ]
        },
        {
            "id": "g-034",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "This is City Library desk calling to notify that the reserved textbook is available for pickup."},
                {"tMs": 3000, "speaker": "caller", "text": "It will be held for you until Friday."}
            ]
        },
        {
            "id": "g-035",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "नमस्ते, सोसाइटी आरडब्ल्यूए से सूचना। रविवार सुबह 10 बजे आम सभा होगी।"},
                {"tMs": 3000, "speaker": "caller", "text": "पार्किंग व्यवस्था पर चर्चा की जाएगी।"}
            ]
        },
        # Genuine Fraud Awareness Announcements (Hard cases with police/OTP in warning context)
        {
            "id": "g-036",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "यह गृह मंत्रालय और राष्ट्रीय साइबर सुरक्षा सेल का जनहित में जारी संदेश है।"},
                {"tMs": 3000, "speaker": "caller", "text": "सावधान रहें! साइबर ठग खुद को पुलिस, सीबीआई, कस्टम या बैंक अधिकारी बताकर डराते हैं।"},
                {"tMs": 6000, "speaker": "caller", "text": "डिजिटल अरेस्ट जैसी कोई कानूनी प्रक्रिया नहीं होती। कोई भी असली पुलिस अधिकारी वीडियो कॉल पर पैसे या ओटीपी नहीं मांगता।"},
                {"tMs": 9000, "speaker": "caller", "text": "यदि ऐसा कॉल आए तो तुरंत फोन काटें और साइबर हेल्पलाइन 1930 पर शिकायत दर्ज करें।"}
            ]
        },
        {
            "id": "g-037",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Public interest announcement by RBI and National Cyber Crime Portal."},
                {"tMs": 3000, "speaker": "caller", "text": "Beware of fraudsters threatening digital arrest or courier customs duty fines."},
                {"tMs": 6000, "speaker": "caller", "text": "Real law enforcement agencies never ask you to transfer funds to any safe account."},
                {"tMs": 9000, "speaker": "caller", "text": "Never share OTP, PIN or remote screen access with anyone. Dial 1930 immediately."}
            ]
        },
        {
            "id": "g-038",
            "label": "genuine",
            "lang": "en",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Official telecom and law enforcement awareness advisory."},
                {"tMs": 3000, "speaker": "caller", "text": "Fraudsters are impersonating police officers and customs authorities regarding intercepted parcels."},
                {"tMs": 6000, "speaker": "caller", "text": "Please be advised that police never demands money over video calls or threatens digital arrest."},
                {"tMs": 9000, "speaker": "caller", "text": "Do not share verification codes. Report suspicious incidents at cybercrime.gov.in or 1930."}
            ]
        },
        {
            "id": "g-039",
            "label": "genuine",
            "lang": "hi",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "साइबर जागरूकता संदेश: फर्जी बैंक कॉल से सावधान रहें।"},
                {"tMs": 3000, "speaker": "caller", "text": "केवाईसी अपडेट के नाम पर आने वाले लिंक पर क्लिक न करें।"},
                {"tMs": 6000, "speaker": "caller", "text": "अपना ओटीपी और पासवर्ड किसी को न बताएं। बैंक कभी फोन पर ओटीपी नहीं मांगता।"}
            ]
        },
        {
            "id": "g-040",
            "label": "genuine",
            "lang": "hinglish",
            "tactics": [],
            "turns": [
                {"tMs": 0, "speaker": "caller", "text": "Cyber security alert: Scammers are using fake job and investment offers promising guaranteed double returns."},
                {"tMs": 3000, "speaker": "caller", "text": "Do not deposit money to unknown UPI accounts or install AnyDesk on stranger's advice."},
                {"tMs": 6000, "speaker": "caller", "text": "Report fraud immediately to national helpline 1930."}
            ]
        },
    ]

    for case in scam_cases:
        write_case(case)

    for case in genuine_cases:
        write_case(case)

    print(f"Successfully generated {len(scam_cases)} scam cases and {len(genuine_cases)} genuine cases (total: {len(scam_cases) + len(genuine_cases)})")


if __name__ == "__main__":
    generate_all_cases()

