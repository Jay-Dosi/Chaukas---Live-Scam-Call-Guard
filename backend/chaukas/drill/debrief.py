"""Fire-Drill debrief generation — PRD §7.3, §7.4.

Always breaks character. Plain language, kind tone, never shames.
"""

from __future__ import annotations

from typing import Literal

Outcome = Literal["safe", "unsafe"]


DEBRIEF_TEMPLATES = {
    "en": {
        "good_hangup": {
            "what_happened": "You ended the call when things got suspicious. That was the right move.",
            "what_you_did_well": "You trusted your instincts and hung up before any harm was done.",
            "what_put_you_at_risk": "Nothing — you didn't share anything or agree to anything.",
            "one_thing": "No real police officer, bank, or government agency will ask for money, OTPs, or tell you to stay on a video call. If they do, hang up.",
        },
        "verified_independently": {
            "what_happened": "You said you'd check with your bank / call 1930 / contact family before acting. That's exactly right.",
            "what_you_did_well": "You chose to verify independently instead of believing the caller.",
            "what_put_you_at_risk": "The caller tried to pressure you, but you didn't fall for it.",
            "one_thing": "Always verify independently — call your bank on the number on your card, call 1930, or talk to family. Never use numbers the caller gives you.",
        },
        "agreed_transfer": {
            "what_happened": "You agreed to transfer money to a 'safe account' or pay a fine. This is how scammers steal money.",
            "what_you_did_well": "You engaged with the caller and asked questions, which shows you were trying to understand.",
            "what_put_you_at_risk": "You agreed to send money. No legitimate agency ever asks you to transfer money to 'prove innocence' or 'secure your account'.",
            "one_thing": "Never transfer money to anyone claiming to be from the police, bank, or government. Call 1930 immediately if this happens on a real call.",
        },
        "gave_credential": {
            "what_happened": "You shared an OTP, PIN, or other credential. This gives scammers access to your accounts.",
            "what_you_did_well": "You were polite and cooperative, which is natural — scammers exploit that.",
            "what_put_you_at_risk": "You shared a code or password. No real bank or government officer will ever ask for your OTP, PIN, or password.",
            "one_thing": "OTPs and PINs are yours alone. Never share them with anyone, no matter who they claim to be.",
        },
    },
    "hi": {
        "good_hangup": {
            "what_happened": "आपने शक होने पर कॉल काट दी। यह बिल्कुल सही फैसला था।",
            "what_you_did_well": "आपने अपनी समझ पर भरोसा किया और कोई नुकसान होने से पहले ही कॉल काट दी।",
            "what_put_you_at_risk": "कुछ भी नहीं — आपने न कुछ साझा किया, न किसी बात से सहमत हुए।",
            "one_thing": "कोई असली पुलिस अधिकारी, बैंक, या सरकारी एजेंसी कभी पैसे, OTP नहीं मांगती, या वीडियो कॉल पर रहने को नहीं कहती। अगर ऐसा हो तो कॉल काट दें।",
        },
        "verified_independently": {
            "what_happened": "आपने कहा कि आप बैंक से चेक करेंगे, 1930 कॉल करेंगे, या परिवार से बात करेंगे। यही सही तरीका है।",
            "what_you_did_well": "आपने कॉलर की बात मानने के बजाय खुद चेक करना चुना।",
            "what_put_you_at_risk": "कॉलर ने दबाव डाला, लेकिन आप नहीं माने।",
            "one_thing": "हमेशा खुद चेक करें — अपने कार्ड पर लिखे नंबर पर बैंक को कॉल करें, 1930 पर कॉल करें, या परिवार से बात करें। कॉलर जो नंबर दे, उस पर कभी कॉल न करें।",
        },
        "agreed_transfer": {
            "what_happened": "आप 'सुरक्षित खाते' में पैसा ट्रांसफर करने या जुर्माना देने को राजी हो गए। यही तरीका है जिससे स्कैमर पैसे चुराते हैं।",
            "what_you_did_well": "आपने कॉलर से सवाल पूछे, जो दिखाता है कि आप समझने की कोशिश कर रहे थे।",
            "what_put_you_at_risk": "आप पैसे भेजने को तैयार हो गए। कोई असली एजेंसी कभी नहीं कहती कि 'बेगुनाही साबित करने के लिए पैसे ट्रांसफर करो' या 'खाता सुरक्षित करने के लिए पैसे भेजो'।",
            "one_thing": "कभी भी किसी को पैसा ट्रांसफर न करें जो खुद को पुलिस, बैंक, या सरकारी अधिकारी बताता हो। असली कॉल पर ऐसा हो तो तुरंत 1930 कॉल करें।",
        },
        "gave_credential": {
            "what_happened": "आपने OTP, PIN, या कोई और कोड बता दिया। इससे स्कैमर को आपके खातों का एक्सेस मिल जाता है।",
            "what_you_did_well": "आप विनम्र और सहयोगी थे, जो स्वाभाविक है — स्कैमर इसी का फायदा उठाते हैं।",
            "what_put_you_at_risk": "आपने कोड या पासवर्ड साझा किया। कोई असली बैंक या सरकारी अधिकारी कभी आपका OTP, PIN, या पासवर्ड नहीं मांगेगा।",
            "one_thing": "OTP और PIN सिर्फ आपके हैं। इन्हें किसी से भी शेयर न करें, चाहे वो कोई भी होने का दावा करे।",
        },
    },
    "hinglish": {
        "good_hangup": {
            "what_happened": "Aapne shak hone pe call kaat di. Yeh bilkul sahi decision tha.",
            "what_you_did_well": "Aapne apni samajh pe bharosa kiya aur koi nuksan hone se pehle hi call kaat di.",
            "what_put_you_at_risk": "Kuch bhi nahi — aapne na kuch share kiya, na kisi baat se agree hue.",
            "one_thing": "Koi asli police officer, bank, ya sarkari agency kabhi paise, OTP nahi maangti, ya video call pe rehne ko nahi kehti. Agar aisa ho to call kaat dein.",
        },
        "verified_independently": {
            "what_happened": "Aapne kaha ki aap bank se check karenge, 1930 call karenge, ya family se baat karenge. Yeh sahi tareeka hai.",
            "what_you_did_well": "Aapne caller ki baat maan'ne ke bajay khud check karna chuna.",
            "what_put_you_at_risk": "Caller ne dabaav daala, lekin aap nahi mane.",
            "one_thing": "Hamesha khud check karein — apne card pe likhe number pe bank ko call karein, 1930 pe call karein, ya family se baat karein. Caller jo number de, us pe kabhi call na karein.",
        },
        "agreed_transfer": {
            "what_happened": "Aap 'safe account' mein paisa transfer karne ya jurmana dene ko raazi ho gaye. Yeh tarika hai jisse scammer paise churate hain.",
            "what_you_did_well": "Aapne caller se sawaal puche, jo dikhata hai ki aap samajhne ki koshish kar rahe the.",
            "what_put_you_at_risk": "Aap paise bhejne ko taiyaar ho gaye. Koi asli agency kabhi nahi kehti ki 'begunahi sabit karne ke liye paise transfer karo' ya 'account secure karne ke liye paise bhejo'.",
            "one_thing": "Kabhi bhi kisi ko paisa transfer na karein jo khud ko police, bank, ya sarkari adhikari batata ho. Asli call pe aisa ho to turant 1930 call karein.",
        },
        "gave_credential": {
            "what_happened": "Aapne OTP, PIN, ya koi aur code bata diya. Isse scammer ko aapke accounts ka access mil jata hai.",
            "what_you_did_well": "Aap vinamr aur sahyogi the, jo swabhavik hai — scammer isi ka fayda uthate hain.",
            "what_put_you_at_risk": "Aapne code ya password share kiya. Koi asli bank ya sarkari adhikari kabhi aapka OTP, PIN, ya password nahi maangega.",
            "one_thing": "OTP aur PIN sirf aapke hain. Inhe kisi se bhi share na karein, chahe wo koi bhi hone ka daawa kare.",
        },
    },
}


KIND_MESSAGE = {
    "en": "That should never be said on a real call. Don't worry, this was practice.",
    "hi": "यह असली कॉल पर कभी नहीं बोलना चाहिए। चिंता न करें, यह अभ्यास था।",
    "hinglish": "Yeh asli call par kabhi nahi bolna chahiye. Chinta na karein, yeh practice tha.",
}


def generate_debrief(
    outcome: Outcome,
    debrief_key: str,
    lang: str,
    history: list[dict],
    scorecard: dict,
) -> dict:
    """Generate full debrief structure for the UI."""
    templates = DEBRIEF_TEMPLATES.get(lang, DEBRIEF_TEMPLATES["en"])
    template = templates.get(debrief_key, templates["good_hangup"])

    # Build turn-by-turn description
    turn_by_turn = []
    for entry in history:
        turn_by_turn.append({
            "turn": entry["turn"],
            "caller_line": "",  # filled by caller from machine
            "tactic": "",  # filled by caller
            "user_action": entry["user_act"],
            "result": "continued",
        })

    return {
        "what_happened": template["what_happened"],
        "turn_by_turn": turn_by_turn,
        "what_you_did_well": template["what_you_did_well"],
        "what_put_you_at_risk": template["what_put_you_at_risk"],
        "one_thing_to_remember": template["one_thing"],
        "scorecard": scorecard,
        "kind_message": KIND_MESSAGE.get(lang, KIND_MESSAGE["en"]),
    }