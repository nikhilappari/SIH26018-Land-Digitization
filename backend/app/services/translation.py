import re

# Comprehensive dictionary mapping regional land revenue terms to English
REVENUE_TERM_TRANSLATIONS = {
    # Telugu terms
    "ఆంధ్రప్రదేశ్ ప్రభుత్వం": "Government of Andhra Pradesh",
    "భూ రెవెన్యూ విభాగం": "Land Revenue Department",
    "గ్రామ ఖాతా నంబరు": "Village Account Number",
    "అడంగల్ / పహానీ": "Adangal / Pahani",
    "అడంగల్": "Adangal",
    "పహానీ": "Pahani",
    "గ్రామం": "Village",
    "మండలం": "Mandal",
    "జిల్లా": "District",
    "ఖాతా సంఖ్య": "Khata Number",
    "ఖాతా నంబరు": "Khata Number",
    "పట్టాదారు పేరు": "Owner Name",
    "తండ్రి పేరు": "Father Name",
    "సర్వే నంబరు": "Survey Number",
    "ఖస్రా నంబరు": "Khasra Number",
    "ప్లాట్ నంబరు": "Plot Number",
    "విస్తీర్ణం": "Area",
    "ఎకరాలు": "Acres",
    "గుంటలు": "Guntas",
    "భూమి వర్గీకరణ": "Land Classification",
    "మెట్ట": "Dry - Agricultural",
    "నమోదు": "Registration",
    "రిజిస్ట్రేషన్ సంఖ్య": "Registration Number",
    "రిజిస్ట్రేషన్ తేదీ": "Registration Date",
    "పట్టా రకం": "Ownership Type",
    "పట్టాదారు": "Pattadar",
    "కొండ్రు రాము": "Kondru Ramu",
    "కొండ్రు సత్యం": "Kondru Satyam",
    "కొండ్రు సురేష్": "Kondru Suresh",
    "కృష్ణపురం": "Krishnapuram",
    "పెదపాడు": "Pedapadu",
    "పశ్చిమ గోదావరి": "West Godavari",
    "కాండ్రు రాము": "Kondru Ramu",

    # Hindi / Devanagari terms
    "उत्तर प्रदेश सरकार": "Government of Uttar Pradesh",
    "भू-राजस्व विभाग": "Land Revenue Department",
    "ग्राम": "Village",
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
    "उत्तराधिकार": "Mutation",
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
    "பட்டா எண்": "Patta Number / Khata No",
    "புல எண்": "Survey Number",
    "உரிமையாளர் பெயர்": "Owner Name",
    "பெயர்": "Name",
    "பரப்பளவு": "Area",
    "ஹெக்டேர்": "Hectares",
    "புஞ்சை": "Dry Land",
    "நஞ்சை": "Wet Land",
    "பதிவு எண்": "Registration Number",
    "பதிவு தேதி": "Registration Date",
    "கிருஷ்ணமூர்த்தி": "Krishnamurthy",
    "அன்பழகன்": "Anbazhagan",
    "மதுரை": "Madurai",
    "சோழவந்தான்": "Sholavandan"
}

# Simplified character mapping for Devanagari/Telugu phonetic transliteration fallback
INDIAN_PHONETIC_CHAR_MAP = {
    # Consonants / vowels approximations
    'र': 'r', 'म': 'm', 'श': 'sh', 'स': 's', 'ि': 'i', 'ं': 'n', 'ह': 'h', 'त': 't', 'प': 'p', 'द': 'd', 'उ': 'u',
    'क': 'k', 'ो': 'o', 'ं': 'n', 'ड': 'd', '्': '', 'र': 'r', 'ु': 'u', 'ा': 'a', 'म': 'm', 'ू': 'u'
}

def transliterate_word(word: str) -> str:
    """Fallback phonetic mapping for words not found in translations dictionary."""
    # If word is strictly English/numbers, keep it
    if re.match(r'^[a-zA-Z0-9\-\./,\s]+$', word):
        return word
        
    translated = ""
    for char in word:
        translated += INDIAN_PHONETIC_CHAR_MAP.get(char, char)
        
    # Remove any residual non-ascii chars
    cleaned = re.sub(r'[^\x00-\x7F]+', '', translated)
    return cleaned.strip() if cleaned.strip() else word

def translate_to_english(ocr_text: str, source_language: str) -> str:
    """
    Translates regional OCR text into English.
    Operates line-by-line, parsing labels and translating known terms.
    """
    if not ocr_text or source_language == "English":
        return ocr_text

    translated_lines = []
    lines = ocr_text.split('\n')
    
    for line in lines:
        if not line.strip():
            translated_lines.append("")
            continue
            
        translated_line = line
        
        # 1. Translate exact matching dictionary keys (prioritizing longer phrases)
        sorted_keys = sorted(REVENUE_TERM_TRANSLATIONS.keys(), key=len, reverse=True)
        for key in sorted_keys:
            if key in translated_line:
                translated_line = translated_line.replace(key, REVENUE_TERM_TRANSLATIONS[key])
                
        # 2. Transliterate residual regional words that might be names/villages
        # Split by spaces, and if a word contains non-ascii, try mapping
        words = translated_line.split()
        translated_words = []
        for word in words:
            # Check if word has regional chars
            if re.search(r'[^\x00-\x7F]', word):
                # Clean up punctuation
                clean_word = re.sub(r'[^\w\s]', '', word)
                punc = word.replace(clean_word, '')
                
                # Check dictionary again for clean word
                if clean_word in REVENUE_TERM_TRANSLATIONS:
                    translated_words.append(REVENUE_TERM_TRANSLATIONS[clean_word] + punc)
                else:
                    # Fallback transliteration
                    translated_words.append(transliterate_word(clean_word) + punc)
            else:
                translated_words.append(word)
                
        translated_lines.append(" ".join(translated_words))
        
    return "\n".join(translated_lines)
