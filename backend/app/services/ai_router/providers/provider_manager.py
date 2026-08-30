import logging
import time
from typing import Dict, Any, Optional
from app.services.ai_router.providers.base_provider import BaseAIProvider
from app.services.ai_router.providers.local_provider import LocalAIProvider
from app.services.ai_router.providers.groq_provider import GroqVisionProvider
from app.services.handwriting.format_classifier import classify_document_format

logger = logging.getLogger(__name__)

class AIProviderManager:
    """
    Intelligent Multi-Provider Manager.
    Orchestrates local offline OCR and optional Groq Vision cloud perception,
    enforcing seamless fallback, provenance merging on mixed documents, and zero downtime.
    """

    def __init__(self, groq_api_key: Optional[str] = None, groq_model: Optional[str] = None):
        self.local_provider = LocalAIProvider()
        self.groq_provider = GroqVisionProvider(api_key=groq_api_key, model=groq_model)

    def process_document(
        self,
        image_path: str,
        hint_language: Optional[str] = None,
        force_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for AI document perception.
        Executes routing based on image format assessment, provider availability, and fallback rules.
        """
        start_time = time.time()

        # Step 1: Preliminary format classification (Purely image-based)
        format_assessment = classify_document_format(image_path)
        format_type = format_assessment.get("format_type", "UNKNOWN")
        
        selected_provider = "local"
        provider_status = "SUCCESS"
        fallback_reason = None

        # Determine Routing Strategy
        groq_is_ready = self.groq_provider.is_available()

        # Scenario A: User explicitly forced Groq OR Document is Handwritten/Mixed and Groq is configured
        if (force_provider == "groq" or format_type in ["HANDWRITTEN", "MIXED"]) and groq_is_ready:
            selected_provider = "groq"
            
            # For mixed documents, get local OCR context first
            local_ocr = None
            if format_type == "MIXED":
                local_res = self.local_provider.analyze_document(image_path, hint_language=hint_language)
                local_ocr = local_res.get("ocr")

            groq_res = self.groq_provider.analyze_document(image_path, ocr_context=local_ocr, hint_language=hint_language)
            
            if groq_res.get("provider_status") == "SUCCESS":
                # Scenario A1: Mixed document provenance merge
                if format_type == "MIXED" and local_ocr:
                    merged = self._merge_mixed_provenance(local_res, groq_res)
                    merged["processing_time_ms"] = int((time.time() - start_time) * 1000)
                    return merged

                groq_res["processing_time_ms"] = int((time.time() - start_time) * 1000)
                return groq_res
            else:
                # Groq failed (timeout, rate limit, error) -> Fallback gracefully to local provider
                fallback_reason = f"Groq {groq_res.get('provider_status')}: {groq_res.get('error', 'Unspecified')}"
                logger.warning(f"Falling back to Local AI Provider due to: {fallback_reason}")
                selected_provider = "local"
                provider_status = f"FALLBACK_FROM_GROQ ({groq_res.get('provider_status')})"

        elif format_type == "HANDWRITTEN" and not groq_is_ready:
            fallback_reason = "GROQ_API_KEY not configured; routed to local fallback with mandatory human review."

        # Scenario B: Local Offline Perception (Printed documents, or offline fallback)
        local_result = self.local_provider.analyze_document(image_path, hint_language=hint_language)
        local_result["selected_provider"] = selected_provider
        local_result["provider_status"] = provider_status
        local_result["fallback_reason"] = fallback_reason
        local_result["processing_time_ms"] = int((time.time() - start_time) * 1000)

        if format_type in ["HANDWRITTEN", "UNKNOWN"] or fallback_reason:
            local_result["needs_human_review"] = True

        return local_result

    def _merge_mixed_provenance(self, local_res: Dict[str, Any], groq_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merges results for MIXED documents:
        Prefers Groq Vision for handwritten filled values and Local OCR for printed table structures.
        """
        merged_fields = dict(local_res.get("fields", {}))
        groq_fields = groq_res.get("fields", {})

        for field_name, groq_field_obj in groq_fields.items():
            if field_name not in merged_fields:
                continue
            
            g_val = groq_field_obj.get("value")
            l_val = merged_fields[field_name].get("value")

            if g_val is not None and l_val is None:
                # Field missed by OCR but captured by Groq
                merged_fields[field_name] = groq_field_obj
            elif g_val is not None and l_val is not None:
                # Both captured: if Groq has higher confidence, use Groq with dual-engine provenance
                if groq_field_obj.get("confidence", 0) >= merged_fields[field_name].get("confidence", 0):
                    merged_fields[field_name] = groq_field_obj
                    merged_fields[field_name]["engine"] = "hybrid_groq_local_ocr"

        staging = {k: v["value"] for k, v in merged_fields.items()}
        active_confs = [v["confidence"] for v in merged_fields.values() if v["value"] is not None]
        overall_conf = round(float(sum(active_confs) / max(len(active_confs), 1)), 1) if active_confs else 75.0

        return {
            "provider": "hybrid_local_groq",
            "provider_status": "SUCCESS",
            "format_type": "MIXED",
            "format_confidence": max(local_res.get("format_confidence", 0), groq_res.get("format_confidence", 0)),
            "language": groq_res.get("language") or local_res.get("language"),
            "script": groq_res.get("script") or local_res.get("script"),
            "doc_type": groq_res.get("doc_type") or local_res.get("doc_type"),
            "ocr": local_res.get("ocr"),
            "fields": merged_fields,
            "staging": staging,
            "confidence": overall_conf,
            "needs_human_review": True,  # Mixed documents always trigger officer review
            "fallback_required": False
        }
