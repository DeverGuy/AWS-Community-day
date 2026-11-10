"""
Google Gemini Only Image Generation Engine for BUILD THE FUTURE - AI Prompt Battle

Uses Google Gemini native multimodal image generation models exclusively
(e.g., gemini-2.5-flash-image, gemini-3.1-flash-image, gemini-3-pro-image)
with zero non-Gemini fallbacks (no NVIDIA, no Pollinations, no procedural art).
Passes the user's typed prompt strictly as-is.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_GEMINI_IMAGE_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image-preview",
    "gemini-3.1-flash-image",
    "gemini-3.1-flash-lite-image",
    "gemini-3-pro-image-preview",
    "gemini-3-pro-image",
    "gemini-nano-banana-2.1",
    "nano-banana-pro-preview",
]


class ImageGenerator:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.gemini_image_model = os.getenv("GEMINI_IMAGE_MODEL", "").strip()

    def _get_api_key(self) -> str:
        load_dotenv(override=False)
        return (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or self.gemini_api_key or "").strip()

    def generate(self, prompt: str, category: str = "", challenge_title: str = "", seed: int = None) -> dict:
        """
        Generates an image exclusively through Google Gemini API.
        Passes the user prompt strictly as it is without alterations.
        """
        start_time = time.time()
        clean_prompt = (prompt or "").strip()
        if not clean_prompt:
            return {
                "success": False,
                "image_data": None,
                "source": "gemini-only",
                "quota_exceeded": False,
                "error": "Prompt cannot be empty.",
                "latency": 0.0,
            }

        api_key = self._get_api_key()
        if not api_key or len(api_key) <= 10:
            return {
                "success": False,
                "image_data": None,
                "source": "gemini-only",
                "quota_exceeded": False,
                "error": "GEMINI_API_KEY is not configured in .env.",
                "latency": round(time.time() - start_time, 2),
            }

        result = self._generate_gemini(clean_prompt, api_key)
        result["latency"] = round(time.time() - start_time, 2)
        return result

    def _generate_gemini(self, prompt: str, api_key: str) -> dict:
        """
        Invokes Google Gemini multimodal image generation API using the exact prompt as-is.
        """
        preferred = self.gemini_image_model or os.getenv("GEMINI_IMAGE_MODEL", "").strip()
        candidate_models = []
        if preferred:
            candidate_models.append(preferred)
        for m in DEFAULT_GEMINI_IMAGE_MODELS:
            if m not in candidate_models:
                candidate_models.append(m)

        last_error = "Gemini image generation failed."
        saw_quota_limit_zero = False
        saw_quota_exceeded = False

        for model in candidate_models:
            # Handle explicit Imagen model override if configured via GEMINI_IMAGE_MODEL
            if model.startswith("imagen-"):
                res = self._call_imagen_predict(model, prompt, api_key)
                if res.get("success"):
                    return res
                last_error = res.get("error", last_error)
                continue

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "responseModalities": ["IMAGE", "TEXT"]
                }
            }

            try:
                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        candidate = candidates[0]
                        parts = candidate.get("content", {}).get("parts", [])
                        for part in parts:
                            inline = part.get("inlineData") or part.get("inline_data")
                            if inline and inline.get("data"):
                                b64 = inline.get("data")
                                mime = inline.get("mimeType") or inline.get("mime_type") or "image/png"
                                return {
                                    "success": True,
                                    "image_data": f"data:{mime};base64,{b64}",
                                    "source": f"gemini-{model}",
                                    "quota_exceeded": False,
                                    "error": None,
                                }
                        finish_reason = candidate.get("finishReason")
                        text_notes = " ".join(p.get("text", "") for p in parts if "text" in p).strip()
                        last_error = f"Gemini model {model} returned no image data (finishReason={finish_reason}). {text_notes}".strip()
                    else:
                        block_reason = data.get("promptFeedback", {}).get("blockReason")
                        last_error = f"Gemini model {model} returned no candidates (blockReason={block_reason})."
                else:
                    err_msg = resp.text[:300]
                    try:
                        err_msg = resp.json().get("error", {}).get("message", err_msg)
                    except Exception:
                        pass

                    if resp.status_code == 429:
                        saw_quota_exceeded = True
                        if "limit: 0" in err_msg:
                            saw_quota_limit_zero = True
                        print(f"[GeminiImage] {model} quota 429: {err_msg[:180]}")
                    else:
                        print(f"[GeminiImage] {model} HTTP {resp.status_code}: {err_msg[:180]}")
                    last_error = f"Gemini {model} ({resp.status_code}): {err_msg}"
            except requests.exceptions.Timeout:
                print(f"[GeminiImage] {model} timed out (30s).")
                last_error = f"Gemini model {model} request timed out."
            except Exception as e:
                print(f"[GeminiImage] {model} exception: {e}")
                last_error = f"Gemini model {model} exception: {str(e)}"

        if saw_quota_limit_zero:
            friendly_err = (
                "Gemini API returned quota limit: 0 for image generation on the Free Tier key in .env. "
                "Please enable Pay-as-you-go billing on your Google AI Studio project or update GEMINI_API_KEY with a billed key."
            )
            return {
                "success": False,
                "image_data": None,
                "source": "gemini-only",
                "quota_exceeded": True,
                "error": friendly_err,
            }

        return {
            "success": False,
            "image_data": None,
            "source": "gemini-only",
            "quota_exceeded": saw_quota_exceeded,
            "error": last_error,
        }

    def _call_imagen_predict(self, model: str, prompt: str, api_key: str) -> dict:
        """Calls Google Imagen :predict endpoint when an Imagen model is configured."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "outputMimeType": "image/jpeg"
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            if resp.status_code == 200:
                preds = resp.json().get("predictions", [])
                if preds and "bytesBase64Encoded" in preds[0]:
                    b64 = preds[0]["bytesBase64Encoded"]
                    return {
                        "success": True,
                        "image_data": f"data:image/jpeg;base64,{b64}",
                        "source": f"gemini-{model}",
                        "quota_exceeded": False,
                        "error": None,
                    }
            return {
                "success": False,
                "quota_exceeded": resp.status_code == 429,
                "error": f"Imagen {model} ({resp.status_code}): {resp.text[:200]}",
            }
        except Exception as e:
            return {"success": False, "quota_exceeded": False, "error": str(e)}


# Singleton instance
image_generator = ImageGenerator()
