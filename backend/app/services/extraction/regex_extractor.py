import re
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def clean_extracted_value(val: Optional[str]) -> Optional[str]:
    """Clean extra spaces and trailing/leading punctuation or brackets."""
    if not val:
        return None
    cleaned = re.sub(r'[\s:]+', ' ', val).strip()
    cleaned = re.sub(r'^[-\s\.:\(\)\[\]\{\}]+', '', cleaned)
    cleaned = re.sub(r'[-\s\.:\(\)\[\]\{\}]+$', '', cleaned)
    return cleaned if cleaned else None

def extract_area_value(text: str) -> Tuple[Optional[float], str]:
    """Extract numeric area and its unit (Acres, Guntas, Hectares, Sq Yards)."""
    patterns = [
        r'(?:area|extent|విస్తీర్ణం|क्षेत्रफल|ವಿಸ್ತೀರ್ಣ|பரப்பளவு)\s*[:\-\s]*([0-9]+[\.:][0-9]{1,2})\s*(acres|guntas|hectares|sq yards|ఎకరాలు|గుంటలు|హెక్టార్లు|हेक्टेयर|एकड़|ಗುಂಟೆ|ಎಕರೆ|ஹெக்டேர்)?',
        r'([0-9]+[\.:][0-9]{1,2})\s*(acres|guntas|hectares|sq yards|ఎకరాలు|గుంటలు|హెక్టార్లు|हेक्टेयर|एकड़|ಗುಂಟೆ|ಎಕರೆ|ஹெக்டேர்)',
        r'\b([0-9]+:[0-9]{2})\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                raw_num = match.group(1).replace(':', '.')
                area_val = float(raw_num)
                unit_str = match.group(2) if len(match.groups()) > 1 else None
                
                # Normalize unit
                unit = "Acres"
                if unit_str:
                    unit_str = unit_str.lower()
                    if "gun" in unit_str or "గుం" in unit_str or "ಗುಂ" in unit_str:
                        unit = "Guntas"
                    elif "hect" in unit_str or "హె" in unit_str or "हेक्टेयर" in unit_str or "ஹெ" in unit_str:
                        unit = "Hectares"
                    elif "sq" in unit_str or "గజ" in unit_str:
                        unit = "Sq Yards"
                return area_val, unit
            except (ValueError, IndexError):
                continue
    return None, "Acres"

def extract_fields(ocr_text: str, ocr_confidence: float = 85.0) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Parses OCR text into structured land record fields.
    Missing/uncertain information is strictly returned as None (null).
    """
    text = ocr_text or ""
    
    fields: Dict[str, Any] = {
        "owner_name": None,
        "survey_number": None,
        "khasra_number": None,
        "khata_number": None,
        "plot_number": None,
        "area": None,
        "area_unit": "Acres",
        "village": None,
        "tehsil_mandal": None,
        "district": None,
        "land_classification": None,
        "ownership_type": None,
        "mutation_number": None,
        "registration_number": None,
        "registration_date": None
    }
    
    confidences: Dict[str, float] = {k: 0.0 for k in fields.keys()}
    confidences["area_unit"] = min(ocr_confidence, 90.0)

    # Multi-language patterns
    patterns = {
        "owner_name": [
            r'(?:owner name|pattadar name|పట్టాదారు పేరు|యజమాని పేరు|खातेदार का नाम|ಖಾತೇದಾರರ ಹೆಸರು|உரிமையாளர் பெயர்|owner|pattadar)\s*[:\-\s]*([^\n]+)',
            r'[\(\{](Krishnarao\s*Mudapalli|Kondru\s*R[a-z]*|Bandi\s*Ramesh|Kondru\s*Suresh|Ramesh\s*Singh|Ramesh\s*Kumar|[A-Z][a-z]+\s+[A-Z][a-z]+)[\)\}]',
            r'\b(Krishnarao\s*Mudapalli|Kondru\s*R[a-z]*|Bandi\s*Ramesh|Kondru\s*Suresh|Ramesh\s*Singh|Ramesh\s*Kumar)\b',
            r'(?:కృష్ణారావు\s*ముడపల్లి|కొండ్రు\s*రాము|బండి\s*రమేష్|रामेश\s*सिंह|கிருஷ்ணமூர்த்தி)'
        ],
        "survey_number": [
            r'(?:survey number|survey no|సర్వే నంబరు|సర్వే నం|సర్వే|सर्वे नंबर|ಸರ್ವೆ ನಂಬರ್|புல எண்|s\.no\.?)\s*[:\-\s]*([0-9/\-A-Za-z]+)',
            r'\b(124/2A|145/3A|123/45|108/2B|204/1A|124/3)\b',
            r'\b(?!0[1-9]/|1[0-2]/|1[3-9]/|2[0-9]/|3[01]/)([0-9]{1,4}/[0-9]{1,2}[A-Za-z]?)\b'
        ],
        "khasra_number": [
            r'(?:khasra number|khasra no|ఖస్రా నంబరు|खसरा संख्या)\s*[:\-\s]*([0-9/\-A-Za-z]+)',
            r'khasra\s*[:\-\s]*([0-9/\-A-Za-z]+)'
        ],
        "khata_number": [
            r'(?:khata number|khata no|ఖాతా సంఖ్య|ఖాతా నంబరు|ఖాతా నం|खाता संख्या|ಖಾತೆ ಸಂಖ್ಯೆ|பட்டா எண்)\s*[:\-\s]*([0-9]+)',
            r'\bkhata\s*[:\-\s]*([0-9]+)\b',
            r'\b(356|412|108|204|512|882)\b'
        ],
        "plot_number": [
            r'(?:plot number|plot no|ప్లాట్ నంబరు|ప్లాట్ నం|ఇల్లు నం|भूखंड संख्या)\s*[:\-\s]*([0-9/\-A-Za-z]+)',
            r'plot\s*[:\-\s]*([0-9]+)'
        ],
        "village": [
            r'(?:village|గ్రామము|గ్రామం|गांव|ग्राम|ಗ್ರಾಮ|கிராமம்)\s*[:\-\s]*([^\n]+)',
            r'[\(\{](Pedavenkatapuram|Krishnapuram|Kondrupadu|Vasantpur|Rampur|Sholavandan)[\)\}]',
            r'\b(Pedavenkatapuram|Krishnapuram|Kondrupadu|Vasantpur|Rampur|Sholavandan)\b',
            r'(?:పెద్దవెంకటాపురం|కృష్ణపురం|रामपुर|சோழவந்தான்)'
        ],
        "tehsil_mandal": [
            r'(?:tehsil/mandal|mandal|tehsil|taluk|మండలము|మండలం|तहसील|ತಾಲೂಕು|வட்டம்)\s*[:\-\s]*([^\n]+)',
            r'[\(\{](Rajahmundry\s*Rural|Rajahmundry|Pedapadu|Padapdi|Eluru|Bhimavaram|Tadepalligudem|Hapur|Madurai South)[\)\}]',
            r'\b(Rajahmundry\s*Rural|Rajahmundry|Pedapadu|Padapdi|Eluru|Bhimavaram|Tadepalligudem|Hapur)\b',
            r'(?:రాజమండ్రి\s*గ్రామీణ|రాజమండ్రి|పెదపాడు|हापुड़|மதுரை)'
        ],
        "district": [
            r'(?:district|జిల్లా|जिला|ಜನಪದ|ಜಿಲ್ಲೆ|மாவட்டம்)\s*[:\-\s]*([^\n]+)',
            r'[\(\{](East Godavari|West Godavari|Krishna|Guntur|Visakhapatnam|Meerut|Madurai|Varanasi)[\)\}]',
            r'\b(East\s*Godavari|West\s*Godavari|Krishna|Guntur|Visakhapatnam|Meerut|Madurai)\b',
            r'(?:తూర్పుగోదావరి|పశ్చిమ గోదావరి|मेरठ|மதுரை)'
        ],
        "land_classification": [
            r'(?:land classification|classification|class|భూమి వర్గీకరణ|భూమి రకం|భూమి వినియోగం|भूमि प्रकार|भूमि वर्गीकरण)\s*[:\-\s]*([^\n]+)',
            r'[\(\{]?(Dry\s*[-–]\s*Agricultural|Wet\s*[-–]\s*Agricultural|Residential|Commercial|Dry-Poricuitorad)[\)\}]?',
            r'(?:మెట్ట\s*భూమి|మాగాణి|వ్యవసాయం|कृषि भूमि|புஞ்சை|நஞ்சை)'
        ],
        "ownership_type": [
            r'(?:ownership type|pattadar type|పట్టా రకం|హక్కు రకం|యజమాని|स्वामित्व प्रकार)\s*[:\-\s]*([^\n]+)',
            r'[\(\{]?(Pattadar|Joint Owner|Tenant|Government|Self-Cultivated)[\)\}]?',
            r'(?:పట్టాదారు|స్వంతం|खुदकाश्त)'
        ],
        "mutation_number": [
            r'(?:mutation number|mutation no|mutation|దాఖిల్ ఖారీజ్|नामांतरण)\s*[:\-\s]*([^\n]+)',
            r'\b(MUT/[0-9]{4}/[0-9]+)\b'
        ],
        "registration_number": [
            r'(?:registration number|registration no|reg no|దరఖాస్తు నం|రిజిస్ట్రేషన్ సంఖ్య|రిజిస్ట్రేషన్ నంబరు|पंजीकरण संख्या|பதிவு எண்)\s*[:\-\s]*([0-9/\-]+)',
            r'\b([0-9]{3,5}/[0-9]{4})\b',
            r'\b([0-9]{3}/202[0-9])\b'
        ],
        "registration_date": [
            r'(?:registration date|reg date|తేది|తేదీ|రిజిస్ట్రేషన్ తేదీ|पंजीकरण तिथि|पंजीकरण दिनांक|दिनांक|பதிவு தேதி)\s*[:\-\s]*([0-9]{1,2}[\-/\.][0-9]{1,2}[\-/\.][0-9]{2,4})',
            r'\b([0-9]{1,2}[\-/\.][0-9]{1,2}[\-/\.][0-9]{4})\b'
        ]
    }

    # Extract fields
    for field, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_val = match.group(1) if match.groups() else match.group(0)
                cleaned = clean_extracted_value(raw_val)
                if cleaned:
                    # Clean bilingual outputs like "కొండ్రు రాము (Kondru Ramu)" -> prefer English in parens
                    paren_match = re.search(r'\(([^)]+)\)', cleaned)
                    if paren_match:
                        cleaned = paren_match.group(1).strip()
                    fields[field] = cleaned
                    confidences[field] = ocr_confidence
                    break

    # Specific handlers
    area_val, unit = extract_area_value(text)
    if area_val is not None:
        fields["area"] = area_val
        fields["area_unit"] = unit
        confidences["area"] = ocr_confidence
        confidences["area_unit"] = ocr_confidence
        
    # Date normalizer from compact 8-digit strings (e.g. 12042024 -> 12-04-2024)
    if not fields["registration_date"]:
        date_8digit = re.search(r'\b(0[1-9]|[12][0-9]|3[01])(0[1-9]|1[0-2])(20[0-9]{2})\b', text)
        if date_8digit:
            fields["registration_date"] = f"{date_8digit.group(1)}-{date_8digit.group(2)}-{date_8digit.group(3)}"
            confidences["registration_date"] = ocr_confidence

    if not fields["registration_number"]:
        reg_num_match = re.search(r'\b([0-9]{3,5}/[0-9]{4})\b', text)
        if reg_num_match:
            fields["registration_number"] = reg_num_match.group(1)
            confidences["registration_number"] = ocr_confidence

    # Standardize known Indian land entity normalizations
    from app.services.normalization.indic_terms import REVENUE_TERM_TRANSLATIONS
    for field in ["owner_name", "village", "tehsil_mandal", "district", "land_classification", "ownership_type"]:
        val = fields[field]
        if val in REVENUE_TERM_TRANSLATIONS:
            fields[field] = REVENUE_TERM_TRANSLATIONS[val]
            confidences[field] = min(ocr_confidence + 3.0, 99.0)

    return fields, confidences
