"""Fixed text for PDF reports in English, Hindi and Marathi."""

LABELS = {
    "en": {
        "title": "Vedic Birth Chart Report", "match_title": "Marriage Matching Report",
        "birth_details": "Birth details", "name": "Name", "date": "Date", "time": "Time", "place": "Place",
        "coords": "Coordinates", "tz": "Time zone", "lagna": "Lagna (Ascendant)", "moon_sign": "Moon sign",
        "nakshatra": "Nakshatra", "settings": "Settings", "ayanamsa": "Ayanamsa", "chart": "Birth chart (D1)",
        "navamsa": "Navamsa (D9)", "planets": "Planet positions", "planet": "Planet", "sign": "Sign",
        "degree": "Degree", "pada": "Pada", "house": "House", "dignity": "Dignity", "status": "Status",
        "retro": "Retrograde", "combust": "Combust", "dasha": "Vimshottari Dasha", "mahadasha": "Mahadasha",
        "start": "Start", "end": "End", "antardasha": "Antardasha (current Mahadasha)", "readings": "Readings",
        "source": "Source", "footer": "Calculated with Swiss Ephemeris (sidereal, {ayanamsa}). Engine {engine}, rules {rules}. "
        "Readings are traditional interpretations, not professional, medical, legal or financial advice.",
        "time_note": "The birth time is marked as {acc}. The Lagna, houses and Dasha dates depend on it.",
        "score": "Ashtakoota score", "koota": "Koota", "points": "Points", "max": "Max", "manglik": "Manglik",
        "yes": "Yes", "no": "No", "boy": "Groom", "girl": "Bride", "prepared_by": "Prepared by",
        "verdict": {"excellent": "Excellent match", "good": "Good match", "not_recommended": "Below the usual threshold of 18"},
        "accuracy": {"approximate": "approximate", "unknown": "unknown"},
    },
    "hi": {
        "title": "वैदिक जन्म कुंडली रिपोर्ट", "match_title": "विवाह मिलान रिपोर्ट",
        "birth_details": "जन्म विवरण", "name": "नाम", "date": "तिथि", "time": "समय", "place": "स्थान",
        "coords": "निर्देशांक", "tz": "समय क्षेत्र", "lagna": "लग्न", "moon_sign": "चंद्र राशि",
        "nakshatra": "नक्षत्र", "settings": "सेटिंग्स", "ayanamsa": "अयनांश", "chart": "जन्म कुंडली (D1)",
        "navamsa": "नवांश (D9)", "planets": "ग्रह स्थिति", "planet": "ग्रह", "sign": "राशि",
        "degree": "अंश", "pada": "पद", "house": "भाव", "dignity": "बल", "status": "स्थिति",
        "retro": "वक्री", "combust": "अस्त", "dasha": "विंशोत्तरी दशा", "mahadasha": "महादशा",
        "start": "आरंभ", "end": "अंत", "antardasha": "अंतर्दशा (वर्तमान महादशा)", "readings": "फलादेश",
        "source": "स्रोत", "footer": "स्विस एफेमेरिस से गणना (निरयण, {ayanamsa})। इंजन {engine}, नियम {rules}। "
        "फलादेश पारंपरिक व्याख्याएँ हैं, पेशेवर, चिकित्सा, कानूनी या वित्तीय सलाह नहीं।",
        "time_note": "जन्म समय {acc} चिह्नित है। लग्न, भाव और दशा तिथियाँ इस पर निर्भर करती हैं।",
        "score": "अष्टकूट गुण", "koota": "कूट", "points": "गुण", "max": "अधिकतम", "manglik": "मांगलिक",
        "yes": "हाँ", "no": "नहीं", "boy": "वर", "girl": "वधू", "prepared_by": "द्वारा तैयार",
        "verdict": {"excellent": "उत्तम मिलान", "good": "अच्छा मिलान", "not_recommended": "सामान्य सीमा 18 से कम"},
        "accuracy": {"approximate": "अनुमानित", "unknown": "अज्ञात"},
    },
    "mr": {
        "title": "वैदिक जन्मकुंडली अहवाल", "match_title": "विवाह गुणमिलन अहवाल",
        "birth_details": "जन्म तपशील", "name": "नाव", "date": "तारीख", "time": "वेळ", "place": "ठिकाण",
        "coords": "निर्देशांक", "tz": "वेळ क्षेत्र", "lagna": "लग्न", "moon_sign": "चंद्र राशी",
        "nakshatra": "नक्षत्र", "settings": "सेटिंग्ज", "ayanamsa": "अयनांश", "chart": "जन्मकुंडली (D1)",
        "navamsa": "नवांश (D9)", "planets": "ग्रहस्थिती", "planet": "ग्रह", "sign": "राशी",
        "degree": "अंश", "pada": "चरण", "house": "स्थान", "dignity": "बल", "status": "स्थिती",
        "retro": "वक्री", "combust": "अस्त", "dasha": "विंशोत्तरी दशा", "mahadasha": "महादशा",
        "start": "आरंभ", "end": "अंत", "antardasha": "अंतर्दशा (चालू महादशा)", "readings": "फलादेश",
        "source": "स्रोत", "footer": "स्विस एफेमेरिसने गणना (निरयन, {ayanamsa}). इंजिन {engine}, नियम {rules}. "
        "फलादेश हे पारंपरिक अर्थ आहेत, व्यावसायिक, वैद्यकीय, कायदेशीर किंवा आर्थिक सल्ला नाही.",
        "time_note": "जन्मवेळ {acc} म्हणून नोंदवली आहे. लग्न, स्थाने आणि दशा तारखा तिच्यावर अवलंबून आहेत.",
        "score": "अष्टकूट गुण", "koota": "कूट", "points": "गुण", "max": "कमाल", "manglik": "मांगलिक",
        "yes": "होय", "no": "नाही", "boy": "वर", "girl": "वधू", "prepared_by": "तयार करणारे",
        "verdict": {"excellent": "उत्तम जुळणी", "good": "चांगली जुळणी", "not_recommended": "नेहमीच्या 18 च्या मर्यादेपेक्षा कमी"},
        "accuracy": {"approximate": "अंदाजे", "unknown": "अज्ञात"},
    },
}
ASC = {"en": "Asc", "hi": "लग्न", "mr": "लग्न"}
