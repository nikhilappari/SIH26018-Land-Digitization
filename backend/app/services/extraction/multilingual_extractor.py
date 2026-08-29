import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.services.normalization.indic_terms import CANONICAL_FIELD_ALIASES
from app.services.normalization.date_normalizer import normalize_date
from app.services.normalization.area_normalizer import normalize_area

logger = logging.getLogger(__name__)

# Transliteration/English cleaning map for common Indian administrative terms & values
INDIAN_PLACE_TRANSLITERATION = {
    # Andhra / Telangana
    "పెద్దవెంకటాపురం": "Pedavenkatapuram",
    "రాజమండ్రి": "Rajahmundry",
    "రాజమండ్రి గ్రామీణ": "Rajahmundry Rural",
    "తూర్పుగోదావరి": "East Godavari",
    "పశ్చిమగోదావరి": "West Godavari",
    "కృష్ణా": "Krishna",
    "గుంటూరు": "Guntur",
    "విశాఖపట్నం": "Visakhapatnam",
    "చిత్తూరు": "Chittoor",
    "కడప": "Kadapa",
    "అనంతపురం": "Anantapur",
    "కర్నూలు": "Kurnool",
    "నెల్లూరు": "Nellore",
    "శ్రీకాకుళం": "Srikakulam",
    "విజయనగరం": "Vizianagaram",
    # Hindi / UP / MP
    "हापुड़": "Hapur",
    "मेरठ": "Meerut",
    "गाजियाबाद": "Ghaziabad",
    "लखनऊ": "Lucknow",
    "कानपुर": "Kanpur",
    "वाराणसी": "Varanasi",
    "प्रयागराज": "Prayagraj",
    # Tamil Nadu
    "மதுரை": "Madurai",
    "சோழவந்தான்": "Sholavandan",
    "சென்னை": "Chennai",
    "கோயம்புத்தூர்": "Coimbatore",
    "திருச்சிராப்பள்ளி": "Tiruchirappalli"
}

def clean_value_text(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    cleaned = str(val).strip()
    # Remove leading colons, dashes, pipes, equals
    cleaned = re.sub(r'^[:;\-\|=\.\s]+', '', cleaned).strip()
    # Remove trailing colons, dashes, pipes
    cleaned = re.sub(r'[:;\-\|=\.\s]+$', '', cleaned).strip()
    return cleaned if len(cleaned) > 0 else None

class MultilingualFieldExtractor:
    """
    Data-driven, multi-strategy land record field extractor with strict null safety
    and rich provenance (original_value, source_text, source_bbox, confidence).
    """

    def __init__(self):
        self.aliases = CANONICAL_FIELD_ALIASES

    def extract_all(self, raw_ocr_data: Dict[str, Any], doc_confidence: float = 85.0) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Processes OCR text & line bounding boxes to extract canonical land record fields.
        Returns:
            (structured_fields_dict, staging_record_dict)
        """
        raw_text = raw_ocr_data.get("text", "")
        lines = raw_ocr_data.get("lines", [])
        
        # If no lines with bboxes were extracted, build line items from raw text
        if not lines and raw_text:
            for line_str in raw_text.split('\n'):
                line_str_clean = line_str.strip()
                if line_str_clean:
                    lines.append({
                        "line_text": line_str_clean,
                        "bbox": [0, 0, 0, 0],
                        "words": []
                    })

        # Structured provenance dictionary initialized to null
        structured_fields: Dict[str, Dict[str, Any]] = {
            "owner_name": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "father_name": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "survey_number": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "khata_number": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "khasra_number": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "plot_number": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "area": {"value": None, "unit": "Acres", "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "village": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "mandal": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "district": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "registration_number": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "registration_date": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None},
            "land_classification": {"value": None, "original_value": None, "confidence": 0.0, "source_text": None, "source_bbox": None}
        }

        # -------------------------------------------------------------
        # 1. Proximity & Label-Value Matching across lines
        # -------------------------------------------------------------
        for field_name, alias_list in self.aliases.items():
            if field_name not in structured_fields:
                continue
            for idx, line_item in enumerate(lines):
                line_text = line_item.get("line_text", "")
                line_bbox = line_item.get("bbox", [0, 0, 0, 0])
                
                matched_alias = None
                for alias in alias_list:
                    # Match alias anywhere in line (case insensitive)
                    pattern = rf'(?i)(?:^|[\s,;])({re.escape(alias)})[\s:;\-=\.]*(.*)$'
                    match = re.search(pattern, line_text)
                    if match:
                        matched_alias = alias
                        remainder = match.group(2).strip()
                        
                        # Value on the same line
                        if remainder and len(remainder) > 0:
                            extracted_val = clean_value_text(remainder)
                            if extracted_val and len(extracted_val) > 0:
                                self._assign_field_value(
                                    structured_fields, field_name, extracted_val,
                                    source_text=line_text, source_bbox=line_bbox, confidence=doc_confidence
                                )
                                break
                        # Value might be on the immediate next line if remainder is empty
                        elif idx + 1 < len(lines):
                            next_line_text = lines[idx + 1].get("line_text", "").strip()
                            next_line_bbox = lines[idx + 1].get("bbox", [0, 0, 0, 0])
                            # Check that next line isn't another label
                            if not self._is_known_label(next_line_text):
                                extracted_val = clean_value_text(next_line_text)
                                if extracted_val and len(extracted_val) > 0:
                                    self._assign_field_value(
                                        structured_fields, field_name, extracted_val,
                                        source_text=f"{line_text} -> {next_line_text}", source_bbox=next_line_bbox, confidence=doc_confidence * 0.9
                                    )
                                    break
                if structured_fields[field_name]["value"] is not None:
                    break

        # -------------------------------------------------------------
        # 2. Heuristic Pattern Fallbacks for Unextracted Identifiers
        # -------------------------------------------------------------
        # Survey Number Regex (e.g. 124/2A, 124/2, 125/3, 12-15, 123/4A)
        if structured_fields["survey_number"]["value"] is None and raw_text:
            sy_matches = re.findall(r'(?:survey|sy|నం|సంఖ్య|నంబరు|నెం)[\s\.:\-_]*([0-9]{1,4}[\/\-][0-9]{1,4}[A-Za-z]*)', raw_text, re.IGNORECASE)
            if not sy_matches:
                # Look for standalone sub-division numbers e.g. 124/2A or 124/3, explicitly ignoring date strings like 15/06/2022
                all_slashes = re.findall(r'\b([0-9]{1,4}[\/\-][0-9]{1,3}[A-Za-z0-9]*)\b', raw_text)
                for cand in all_slashes:
                    # Ignore if it's a date or 4-digit year format (e.g. 15/06 or 217/2022)
                    if not re.search(r'\b(?:19|20)[0-9]{2}\b', cand) and not re.match(r'^[0-3]?[0-9]\/[0-1]?[0-9]$', cand):
                        sy_matches.append(cand)
            if sy_matches:
                # Clean trailing noise if any
                clean_sy = re.sub(r'[^0-9A-Za-z\/\-]', '', sy_matches[0])
                structured_fields["survey_number"] = {
                    "value": str(clean_sy),
                    "original_value": str(sy_matches[0]),
                    "confidence": 88.0,
                    "source_text": str(sy_matches[0]),
                    "source_bbox": None
                }

        # Registration / Application Number Regex (e.g. 217/2022 or 217/2022-A)
        if structured_fields["registration_number"]["value"] is None and raw_text:
            reg_matches = re.findall(r'(?:దరఖాస్తు|రిజిస్ట్రేషన్|application|reg)[\s\.:\-_]*(?:నం|నంబరు|no)?[\s\.:\-_]*([0-9]{1,6}[\/\-][0-9]{4}[A-Za-z\-]*)', raw_text, re.IGNORECASE)
            if not reg_matches:
                reg_matches = re.findall(r'\b([0-9]{2,5}\/20[0-9]{2}[A-Za-z\-]*)\b', raw_text)
            if reg_matches:
                clean_reg = re.sub(r'[^0-9A-Za-z\/\-]', '', reg_matches[0])
                structured_fields["registration_number"] = {
                    "value": str(clean_reg),
                    "original_value": str(reg_matches[0]),
                    "confidence": 90.0,
                    "source_text": str(reg_matches[0]),
                    "source_bbox": None
                }

        # Registration Date Regex (e.g. 15/06/2022, 15-06-2022, 15.06.2022)
        if structured_fields["registration_date"]["value"] is None and raw_text:
            date_matches = re.findall(r'\b([0-3]?[0-9][\/\-\.][0-1]?[0-9][\/\-\.]20[0-9]{2})\b', raw_text)
            if date_matches:
                norm_d = normalize_date(date_matches[0])
                if norm_d:
                    structured_fields["registration_date"] = {
                        "value": norm_d["normalized"],
                        "original_value": norm_d["original"],
                        "confidence": 92.0,
                        "source_text": date_matches[0],
                        "source_bbox": None
                    }

        # Khata Number Regex (e.g. ఖాతా నం: 356 or standalone 356 in table)
        if structured_fields["khata_number"]["value"] is None and raw_text:
            khata_matches = re.findall(r'(?:ఖాతా|खाता|khata|பட்டா)[\s\.:\-_]*(?:నం|సంఖ్య|no)?[\s\.:\-_]*([0-9]{1,6})\b', raw_text, re.IGNORECASE)
            if khata_matches:
                structured_fields["khata_number"] = {
                    "value": str(khata_matches[0]),
                    "original_value": str(khata_matches[0]),
                    "confidence": 90.0,
                    "source_text": str(khata_matches[0]),
                    "source_bbox": None
                }

        # Area / Extent Fallback
        if structured_fields["area"]["value"] is None and raw_text:
            area_matches = re.findall(r'(?:విస్తీర్ణం|వైశాల్యం|क्षेत्रफल|extent|area)[\s\.:\-_]*([0-9]+[\.:][0-9]{1,3}(?:\s*(?:ఎకరాలు|acres|acre|హెక్టార్లు|हेक्टेयर|cents))?)', raw_text, re.IGNORECASE)
            if not area_matches:
                # Look for decimal extents like 2.35 or 2:35 in agricultural ledger lines
                area_matches = re.findall(r'\b([0-9]{1,2}[\.:][0-9]{2})\b', raw_text)
            if area_matches:
                norm_a = normalize_area(None, source_text=area_matches[0])
                if norm_a:
                    structured_fields["area"] = {
                        "value": norm_a["value"],
                        "unit": norm_a["unit"],
                        "original_value": norm_a["original"],
                        "confidence": 90.0,
                        "source_text": area_matches[0],
                        "source_bbox": None
                    }

        # -------------------------------------------------------------
        # 3. Construct Final Clean Staging Record
        # -------------------------------------------------------------
        staging_record = {
            "owner_name": structured_fields["owner_name"]["value"],
            "survey_number": str(structured_fields["survey_number"]["value"]) if structured_fields["survey_number"]["value"] is not None else None,
            "khasra_number": str(structured_fields["khasra_number"]["value"]) if structured_fields["khasra_number"]["value"] is not None else None,
            "khata_number": str(structured_fields["khata_number"]["value"]) if structured_fields["khata_number"]["value"] is not None else None,
            "plot_number": str(structured_fields["plot_number"]["value"]) if structured_fields["plot_number"]["value"] is not None else None,
            "area": structured_fields["area"]["value"],
            "area_unit": structured_fields["area"].get("unit", "Acres"),
            "village": structured_fields["village"]["value"],
            "tehsil_mandal": structured_fields["mandal"]["value"],
            "district": structured_fields["district"]["value"],
            "land_classification": structured_fields["land_classification"]["value"],
            "registration_number": str(structured_fields["registration_number"]["value"]) if structured_fields["registration_number"]["value"] is not None else None,
            "registration_date": structured_fields["registration_date"]["value"]
        }

        # Confidence map
        confidences = {k: v["confidence"] for k, v in structured_fields.items()}

        return structured_fields, staging_record

    def _assign_field_value(self, structured_fields: Dict[str, Any], field_name: str, raw_val: str, source_text: str, source_bbox: Any, confidence: float):
        clean_val = clean_value_text(raw_val)
        if not clean_val:
            return

        # Strip secondary bilingual prefixes if line contains e.g. "Survey No / సర్వే నం: 123/4A"
        for alias_list in self.aliases.values():
            for al in alias_list:
                clean_val = re.sub(rf'^[\/\s:;\-=]*{re.escape(al)}[\/\s:;\-=]*', '', clean_val, flags=re.IGNORECASE).strip()
        clean_val = re.sub(r'^\([^\)]*\)\s*[:;\-=]*', '', clean_val).strip()
        clean_val = clean_value_text(clean_val)
        if not clean_val:
            return

        # Special normalization by field type
        if field_name == "survey_number":
            sy_m = re.search(r'([0-9]{1,4}[\/\-][0-9]{1,4}[A-Za-z]*)', clean_val)
            val = sy_m.group(1) if sy_m else clean_val
            structured_fields["survey_number"] = {
                "value": str(val),
                "original_value": clean_val,
                "confidence": confidence,
                "source_text": source_text,
                "source_bbox": source_bbox
            }
        elif field_name == "registration_date":
            norm_d = normalize_date(clean_val)
            if norm_d:
                structured_fields["registration_date"] = {
                    "value": norm_d["normalized"],
                    "original_value": norm_d["original"],
                    "confidence": confidence,
                    "source_text": source_text,
                    "source_bbox": source_bbox
                }
        elif field_name == "area":
            norm_a = normalize_area(None, source_text=clean_val)
            if norm_a:
                structured_fields["area"] = {
                    "value": norm_a["value"],
                    "unit": norm_a["unit"],
                    "original_value": norm_a["original"],
                    "confidence": confidence,
                    "source_text": source_text,
                    "source_bbox": source_bbox
                }
        elif field_name in ["village", "mandal", "district"]:
            # Check transliteration dictionary if regional script
            transliterated = INDIAN_PLACE_TRANSLITERATION.get(clean_val, clean_val)
            structured_fields[field_name] = {
                "value": transliterated,
                "original_value": clean_val,
                "confidence": confidence,
                "source_text": source_text,
                "source_bbox": source_bbox
            }
        else:
            # Check transliteration for owner/general text if exact match exists
            transliterated = INDIAN_PLACE_TRANSLITERATION.get(clean_val, clean_val)
            structured_fields[field_name] = {
                "value": transliterated,
                "original_value": clean_val,
                "confidence": confidence,
                "source_text": source_text,
                "source_bbox": source_bbox
            }

    def _is_known_label(self, text: str) -> bool:
        lower_t = text.lower()
        for alias_list in self.aliases.values():
            for alias in alias_list:
                if lower_t.startswith(alias.lower()):
                    return True
        return False
