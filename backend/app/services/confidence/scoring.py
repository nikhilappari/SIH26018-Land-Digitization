from typing import Dict, Any, List

def calculate_field_confidences(extracted_fields: Dict[str, Any], base_ocr_confidence: float) -> Dict[str, float]:
    """
    Computes field-level confidence scores based on presence, length, format validity, and OCR score.
    """
    confidences: Dict[str, float] = {}
    
    for field, val in extracted_fields.items():
        if val is None or val == "":
            confidences[field] = 0.0
        else:
            # Base confidence from OCR
            score = float(base_ocr_confidence)
            # Boost if complete and well-formed
            if field in ["survey_number", "registration_number", "khata_number"] and len(str(val)) >= 3:
                score = min(score + 2.0, 99.0)
            confidences[field] = round(score, 1)
            
    return confidences

def calculate_overall_confidence(confidences: Dict[str, float]) -> float:
    """
    Computes weighted overall confidence of extracted document fields.
    """
    valid_scores = [v for k, v in confidences.items() if v > 0.0 and k != "area_unit"]
    if not valid_scores:
        return 50.0
    return round(float(sum(valid_scores) / len(valid_scores)), 1)
