import os
import base64
import json
import logging
import requests
from typing import Dict, Any, Optional
from PIL import Image
import io

from app.core.config import settings
from app.services.ai_router.providers.base_provider import BaseAIProvider
from app.services.ai_router.vlm_understanding import CANONICAL_19_FIELDS, init_canonical_schema
from app.services.normalization.date_normalizer import normalize_date
from app.services.normalization.area_normalizer import normalize_area

logger = logging.getLogger(__name__)

GROQ_SYSTEM_PROMPT = """You are an expert AI Indian Land Revenue Officer and Vision-Language Cadastral Document Parser.
Your objective is to analyze the provided image of an Indian land record (e.g., Form I-B / ROR, Grama Adangal, Pahani, Khata Khatauni, Patta Chitta, 7/12 Extract, Mutation Record, or Sale Deed) along with any optional OCR supporting context.

You must extract the key cadastral attributes into a strictly formatted JSON object adhering to the canonical schema below.

Strict Extraction Rules:
1. Extract ONLY information visibly present and verifiable in the document.
2. NEVER guess, invent, or hallucinate missing information. If a field cannot be read or is not present, return null for its value.
3. Keep all identifiers (survey_number, khasra_number, khata_number, plot_number, registration_number) as EXACT STRING LITERALS (e.g. "145/3A", "KH/99201", "2401/2024"). Never convert survey numbers like "145/3A" to numeric floats.
4. Normalize dates to standard ISO "YYYY-MM-DD" format.
5. If the model cannot provide a reliable bounding box, use null for source_bbox. Do NOT fabricate bounding boxes.
6. Return ONLY valid JSON with no markdown fences, conversational filler, or commentary.

Output JSON Schema:
{
  "detected_language": "English|Telugu|Hindi|Tamil|Kannada|Malayalam|Marathi|Bengali|Gujarati|Odia|Punjabi",
  "document_type": "Pattadar/Land Ownership Record|Survey Record|Mutation Record|Registration Record|Cadastral Map|Other",
  "format_type": "PRINTED|HANDWRITTEN|MIXED",
  "fields": {
    "owner_name": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "father_name": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "survey_number": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "khasra_number": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "khata_number": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "plot_number": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "area": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "area_unit": {"value": "Acres", "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "village": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "mandal": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "tehsil": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "taluk": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "district": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "state": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "land_classification": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "ownership_type": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "mutation_number": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "registration_number": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"},
    "registration_date": {"value": null, "original_value": null, "confidence": 0, "source_text": null, "source_bbox": null, "engine": "groq"}
  }
}
"""

class GroqVisionProvider(BaseAIProvider):
    """
    Multimodal Cloud AI Provider utilizing Groq's low-latency Vision-Language models.
    Supports optical handwriting transcription and zero-shot cadastral document parsing.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", "")
        self.model = model or os.getenv("GROQ_MODEL") or getattr(settings, "GROQ_MODEL", "llama-3.2-11b-vision-preview")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def is_available(self) -> bool:
        """Returns True if a valid API key is configured."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def _encode_image_to_base64_uri(self, image_path: str) -> str:
        """Encodes local image to base64 data URI string with resizing if overly large."""
        with Image.open(image_path) as img:
            # Resize if dimensions exceed 2048 to conserve tokens and bandwidth
            if max(img.size) > 2048:
                img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            
            rgb_img = img.convert("RGB")
            buffer = io.BytesIO()
            rgb_img.save(buffer, format="JPEG", quality=85)
            encoded_bytes = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded_bytes}"

    def analyze_document(
        self,
        image_path: str,
        ocr_context: Optional[Dict[str, Any]] = None,
        hint_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submits image + supporting OCR tokens to Groq Vision model.
        Returns complete analysis or raises an actionable status dictionary on failure.
        """
        if not self.is_available():
            return {
                "provider": "groq",
                "provider_status": "UNAVAILABLE",
                "error": "GROQ_API_KEY is not configured in environment.",
                "fallback_required": True
            }

        try:
            image_data_uri = self._encode_image_to_base64_uri(image_path)
            
            # Construct OCR supporting context prompt
            ocr_text = ocr_context.get("text", "") if ocr_context else ""
            supporting_evidence = ""
            if ocr_text:
                supporting_evidence = f"\n\nLocal OCR Supporting Context (Verify visually against the image):\n\"\"\"{ocr_text}\"\"\""

            user_prompt = f"Analyze this Indian land record image and extract all cadastral fields strictly in the JSON schema.{supporting_evidence}"

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": GROQ_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_data_uri}
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "max_tokens": 1500
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            resp = requests.post(self.api_url, json=payload, headers=headers, timeout=12.0)
            
            if resp.status_code == 200:
                resp_data = resp.json()
                raw_content = resp_data["choices"][0]["message"]["content"]
                parsed_json = json.loads(raw_content)

                # Format and sanitize fields
                canonical_fields = init_canonical_schema()
                model_fields = parsed_json.get("fields", {})

                for field_name in CANONICAL_19_FIELDS:
                    if field_name in model_fields and model_fields[field_name] is not None:
                        f_obj = model_fields[field_name]
                        if isinstance(f_obj, dict):
                            val = f_obj.get("value")
                            canonical_fields[field_name] = {
                                "value": str(val) if (val is not None and field_name in ["survey_number", "khasra_number", "khata_number", "registration_number"]) else val,
                                "original_value": f_obj.get("original_value") or (str(val) if val is not None else None),
                                "confidence": float(f_obj.get("confidence", 90.0) if val is not None else 0.0),
                                "source_text": f_obj.get("source_text"),
                                "source_bbox": f_obj.get("source_bbox"),
                                "engine": "groq"
                            }
                        else:
                            # Scalar fallback
                            canonical_fields[field_name] = {
                                "value": f_obj,
                                "original_value": str(f_obj),
                                "confidence": 88.0,
                                "source_text": None,
                                "source_bbox": None,
                                "engine": "groq"
                            }

                # Normalize dates & areas
                if canonical_fields["registration_date"]["value"]:
                    norm_d = normalize_date(str(canonical_fields["registration_date"]["value"]))
                    if norm_d:
                        canonical_fields["registration_date"]["value"] = norm_d["normalized"]

                if canonical_fields["area"]["value"]:
                    norm_a = normalize_area(None, source_text=str(canonical_fields["area"]["value"]))
                    if norm_a:
                        canonical_fields["area"]["value"] = norm_a["value"]
                        canonical_fields["area_unit"]["value"] = norm_a["unit"]

                staging = {k: v["value"] for k, v in canonical_fields.items()}
                active_confs = [v["confidence"] for v in canonical_fields.values() if v["value"] is not None]
                overall_conf = round(float(sum(active_confs) / max(len(active_confs), 1)), 1) if active_confs else 70.0

                return {
                    "provider": "groq",
                    "provider_status": "SUCCESS",
                    "model": self.model,
                    "format_type": parsed_json.get("format_type", "PRINTED"),
                    "format_confidence": 92.0,
                    "language": parsed_json.get("detected_language", "English"),
                    "script": parsed_json.get("detected_language", "English"),
                    "doc_type": parsed_json.get("document_type", "Other"),
                    "ocr": ocr_context or {"text": "", "confidence": overall_conf, "lines": []},
                    "fields": canonical_fields,
                    "staging": staging,
                    "confidence": overall_conf,
                    "needs_human_review": overall_conf < 75.0,
                    "fallback_required": False
                }

            elif resp.status_code == 429:
                logger.warning(f"Groq API rate limit reached (HTTP 429): {resp.text}")
                return {
                    "provider": "groq",
                    "provider_status": "RATE_LIMITED",
                    "error": "Groq API rate limit exceeded.",
                    "fallback_required": True
                }
            else:
                logger.error(f"Groq API error (HTTP {resp.status_code}): {resp.text}")
                return {
                    "provider": "groq",
                    "provider_status": "API_ERROR",
                    "error": f"Groq HTTP {resp.status_code}: {resp.text}",
                    "fallback_required": True
                }

        except requests.exceptions.Timeout:
            logger.warning("Groq API request timed out (>12s).")
            return {
                "provider": "groq",
                "provider_status": "TIMEOUT",
                "error": "Groq API timed out.",
                "fallback_required": True
            }
        except Exception as e:
            logger.error(f"Groq provider unexpected error: {str(e)}")
            return {
                "provider": "groq",
                "provider_status": "ERROR",
                "error": str(e),
                "fallback_required": True
            }

    def extract_land_fields(
        self,
        image_path: str,
        ocr_context: Optional[Dict[str, Any]] = None,
        language: str = "English",
        doc_type: str = "Other"
    ) -> Dict[str, Any]:
        return self.analyze_document(image_path, ocr_context=ocr_context, hint_language=language)

    def recognize_handwriting(
        self,
        image_path: str,
        ocr_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self.analyze_document(image_path, ocr_context=ocr_context)
