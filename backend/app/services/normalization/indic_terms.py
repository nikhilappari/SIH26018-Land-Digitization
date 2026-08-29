import re

REVENUE_TERM_TRANSLATIONS = {
    # Telugu terms
    "ఆంధ్రప్రదేశ్ ప్రభుత్వం": "Government of Andhra Pradesh",
    "భూ రెవెన్యూ విభాగం": "Land Revenue Department",
    "గ్రామ ఖాతా నంబరు": "Village Account Number",
    "అడంగల్ / పహానీ": "Adangal / Pahani",
    "అడంగల్": "Adangal",
    "పహానీ": "Pahani",
    "గ్రామం": "Village",
    "గ్రామము": "Village",
    "మండలం": "Mandal",
    "మండలము": "Mandal",
    "జిల్లా": "District",
    "ఖాతా సంఖ్య": "Khata Number",
    "ఖాతా నంబరు": "Khata Number",
    "ఖాతా నం": "Khata Number",
    "పట్టాదారు పేరు": "Owner Name",
    "యజమాని పేరు": "Owner Name",
    "తండ్రి పేరు": "Father Name",
    "సర్వే నంబరు": "Survey Number",
    "సర్వే నం": "Survey Number",
    "ఖస్రా నంబరు": "Khasra Number",
    "ప్లాట్ నంబరు": "Plot Number",
    "విస్తీర్ణం": "Area",
    "ఎకరాలు": "Acres",
    "గుంటలు": "Guntas",
    "భూమి వర్గీకరణ": "Land Classification",
    "భూమి రకం": "Land Classification",
    "మెట్ట": "Dry - Agricultural",
    "మెట్ట భూమి": "Dry - Agricultural",
    "మాగాణి": "Wet - Agricultural",
    "రిజిస్ట్రేషన్ సంఖ్య": "Registration Number",
    "రిజిస్ట్రేషన్ నంబరు": "Registration Number",
    "రిజిస్ట్రేషన్ తేదీ": "Registration Date",
    "పట్టా రకం": "Ownership Type",
    "పట్టాదారు": "Pattadar",
    "కొండ్రు రాము": "Kondru Ramu",
    "కొండ్రు సత్యం": "Kondru Satyam",
    "కొండ్రు సురేష్": "Kondru Suresh",
    "కృష్ణారావు ముడపల్లి": "Krishnarao Mudapalli",
    "కృష్ణపురం": "Krishnapuram",
    "పెద్దవెంకటాపురం": "Pedavenkatapuram",
    "పెదపాడు": "Pedapadu",
    "రాజమండ్రి గ్రామీణ": "Rajahmundry Rural",
    "రాజమండ్రి": "Rajahmundry",
    "పశ్చిమ గోదావరి": "West Godavari",
    "తూర్పుగోదావరి": "East Godavari",

    # Hindi / Devanagari terms
    "उत्तर प्रदेश सरकार": "Government of Uttar Pradesh",
    "भू-राजस्व विभाग": "Land Revenue Department",
    "ग्राम": "Village",
    "गांव": "Village",
    "तहसील": "Tehsil/Mandal",
    "जनपद": "District",
    "जिला": "District",
    "खाता खतौनी": "Khata Khatauni",
    "अधिकार अभिलेख": "Record of Rights",
    "खाता संख्या": "Khata Number",
    "खसरा संख्या": "Khasra Number",
    "खातेदार का नाम": "Owner Name",
    "पिता का नाम": "Father Name",
    "क्षेत्रफल": "Area",
    "एकड़": "Acres",
    "हेक्टेयर": "Hectares",
    "भूमि वर्गीकरण": "Land Classification",
    "कृषि भूमि": "Agricultural Land",
    "पंजीकरण संख्या": "Registration Number",
    "पंजीकरण दिनांक": "Registration Date",
    "पंजीकरण तिथि": "Registration Date",
    "नामांतरण": "Mutation",
    "दाखिल खारिज": "Mutation",
    "स्वामित्व प्रकार": "Ownership Type",
    "खुदकाश्त": "Self-Cultivated / Pattadar",
    "रामेश सिंह": "Ramesh Singh",
    "हरि सिंह": "Hari Singh",
    "रामपुर": "Rampur",
    "हापुड़": "Hapur",
    "मेरठ": "Meerut",

    # Tamil terms
    "தமிழ்நாடு அரசு": "Government of Tamil Nadu",
    "வருவாய்த் துறை": "Revenue Department",
    "பட்டா": "Patta / Ownership Record",
    "சிட்டா": "Chitta",
    "மாவட்டம்": "District",
    "வட்டம்": "Taluk/Mandal",
    "கிராமம்": "Village",
    "பட்டா எண்": "Patta Number",
    "புல எண்": "Survey Number",
    "உரிமையாளர் பெயர்": "Owner Name",
    "பரப்பளவு": "Area",
    "ஹெக்டேர்": "Hectares",
    "புஞ்சை": "Dry Land",
    "நஞ்சை": "Wet Land",
    "பதிவு எண்": "Registration Number",
    "பதிவு தேதி": "Registration Date",
    "கிருஷ்ணமூர்த்தி": "Krishnamurthy",
    "மதுரை": "Madurai",
    "சோழவந்தான்": "Sholavandan",

    # Kannada terms
    "ಕರ್ನಾಟಕ ಸರ್ಕಾರ": "Government of Karnataka",
    "ಕಂದಾಯ ಇಲಾಖೆ": "Revenue Department",
    "ಪಹಣಿ": "Pahani / RTC",
    "ಗ್ರಾಮ": "Village",
    "ತಾಲೂಕು": "Taluk/Mandal",
    "ಜಿಲ್ಲೆ": "District",
    "ಖಾತೆ ಸಂಖ್ಯೆ": "Khata Number",
    "ಸರ್ವೆ ನಂಬರ್": "Survey Number",
    "ಖಾತೇದಾರರ ಹೆಸರು": "Owner Name",
    "ವಿಸ್ತೀರ್ಣ": "Area",
    "ಗುಂಟೆ": "Guntas",
    "ಎಕರೆ": "Acres"
}

def translate_to_english(text: str, src_lang: str = "Telugu") -> str:
    """
    Translates Indic land revenue terms to standardized English terminology.
    """
    if not text:
        return ""
    if src_lang == "English":
        return text

    translated = text
    for regional_term, english_term in REVENUE_TERM_TRANSLATIONS.items():
        if regional_term in translated:
            translated = translated.replace(regional_term, english_term)

    return translated
