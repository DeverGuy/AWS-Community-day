"""
Cloudflare Workers AI Image Generation Engine for BUILD THE FUTURE - AI Prompt Battle

Integrates with a deployed Cloudflare Worker from:
https://github.com/saurav-z/free-image-generation-api

Sends the participant's typed prompt strictly as-is via:
  POST <CF_WORKER_URL>
  Authorization: Bearer <CF_WORKER_API_KEY>
  Content-Type: application/json
  Body: {"prompt": "<exact user prompt>"}
"""

import os
import time
import base64
import requests
from dotenv import load_dotenv, dotenv_values

load_dotenv()

DEFAULT_WORKER_URL = "https://prompt-battle-image-api.mokshrjain3137.workers.dev"
DEFAULT_WORKER_API_KEY = "aws-ai-battle-2026-secret"

PLACEHOLDER_URLS = {
    "",
    "your_worker_url",
    "https://your-worker-name.your-subdomain.workers.dev",
    "https://<your-worker-name>.<your-subdomain>.workers.dev",
}
PLACEHOLDER_KEYS = {
    "",
    "your_worker_api_key_here",
    "your-secret-api-key",
}


def _clean_worker_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    u = raw_url.strip()
    while u.endswith((".0.", ".0", "..", ".")):
        if u.endswith(".0."):
            u = u[:-3]
        elif u.endswith(".0"):
            u = u[:-2]
        else:
            u = u.rstrip(".")
    u = u.rstrip("/")
    if u and not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    return u


def _detect_image_mime(raw_bytes: bytes, content_type_header: str = "") -> str:
    if raw_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if raw_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(raw_bytes) >= 12 and raw_bytes[:4] == b"RIFF" and raw_bytes[8:12] == b"WEBP":
        return "image/webp"
    if content_type_header:
        mime = content_type_header.split(";")[0].strip().lower()
        if mime.startswith("image/"):
            return mime
    return "image/jpeg"


def _detect_b64_mime(b64_str: str) -> str:
    if b64_str.startswith("iVBOR"):
        return "image/png"
    if b64_str.startswith("UklGR"):
        return "image/webp"
    return "image/jpeg"


class ImageGenerator:
    def __init__(self):
        self.worker_url = _clean_worker_url(os.getenv("CF_WORKER_URL") or os.getenv("IMAGE_API_URL") or DEFAULT_WORKER_URL)
        self.worker_api_key = (os.getenv("CF_WORKER_API_KEY") or os.getenv("IMAGE_API_KEY") or DEFAULT_WORKER_API_KEY).strip()

    def _get_worker_config(self) -> tuple[str, str]:
        """Reads Cloudflare Worker URL and API key dynamically so .env edits apply immediately."""
        env_file_vals = dotenv_values(".env") if os.path.exists(".env") else {}

        def _pick(*names: str, default: str = "") -> str:
            for name in names:
                val = (env_file_vals.get(name) or "").strip()
                if val:
                    return val
            for name in names:
                val = (os.getenv(name) or "").strip()
                if val:
                    return val
            return default

        url = _pick("CF_WORKER_URL", "IMAGE_API_URL", default=self.worker_url or DEFAULT_WORKER_URL)
        key = _pick("CF_WORKER_API_KEY", "IMAGE_API_KEY", default=self.worker_api_key or DEFAULT_WORKER_API_KEY)
        url = _clean_worker_url(url)
        return url, key

    def generate(self, prompt: str, category: str = "", challenge_title: str = "", seed: int = None) -> dict:
        """
        Generates an image via the deployed Cloudflare Worker (saurav-z/free-image-generation-api).
        Passes the user prompt strictly as it is without alterations.
        """
        start_time = time.time()
        clean_prompt = (prompt or "").strip()
        if not clean_prompt:
            return {
                "success": False,
                "image_data": None,
                "source": "cloudflare-workers-ai",
                "quota_exceeded": False,
                "error": "Prompt cannot be empty.",
                "latency": 0.0,
            }

        worker_url, api_key = self._get_worker_config()
        if not worker_url or worker_url.lower() in PLACEHOLDER_URLS:
            return {
                "success": False,
                "image_data": None,
                "source": "cloudflare-workers-ai",
                "quota_exceeded": False,
                "error": (
                    "CF_WORKER_URL is not configured in .env. "
                    "Deploy cloudflare-worker/worker.js on Cloudflare Workers and set CF_WORKER_URL and CF_WORKER_API_KEY in .env."
                ),
                "latency": round(time.time() - start_time, 2),
            }

        if not api_key or api_key.lower() in PLACEHOLDER_KEYS:
            return {
                "success": False,
                "image_data": None,
                "source": "cloudflare-workers-ai",
                "quota_exceeded": False,
                "error": (
                    "CF_WORKER_API_KEY is not configured in .env. "
                    "Set CF_WORKER_API_KEY in .env to match your Cloudflare Worker's API_KEY variable."
                ),
                "latency": round(time.time() - start_time, 2),
            }

        result = self._generate_cloudflare_worker(clean_prompt, worker_url, api_key)
        result["latency"] = round(time.time() - start_time, 2)
        return result

    def _generate_cloudflare_worker(self, prompt: str, worker_url: str, api_key: str) -> dict:
        """
        Calls the deployed free-image-generation-api Cloudflare Worker with the exact prompt as-is.
        Supports both raw binary JPEG/PNG streams (SDXL) and JSON base64 responses (FLUX).
        """
        url = worker_url.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {"prompt": prompt}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)

            if resp.status_code == 200:
                content_type = (resp.headers.get("Content-Type") or "").lower()
                body_bytes = resp.content or b""

                # Handle JSON response (e.g. FLUX {"image": "<b64>"} or worker error)
                if "application/json" in content_type or body_bytes.lstrip().startswith(b"{"):
                    try:
                        data = resp.json()
                    except Exception:
                        return {
                            "success": False,
                            "image_data": None,
                            "source": "cloudflare-workers-ai",
                            "quota_exceeded": False,
                            "error": "Cloudflare Worker returned malformed JSON response.",
                        }

                    if data.get("error"):
                        details = data.get("details")
                        msg = f"{data['error']}: {details}" if details else str(data["error"])
                        return {
                            "success": False,
                            "image_data": None,
                            "source": "cloudflare-workers-ai",
                            "quota_exceeded": False,
                            "error": f"Cloudflare Worker error: {msg}",
                        }

                    b64_img = data.get("image") or data.get("image_data") or data.get("data")
                    if isinstance(b64_img, str) and len(b64_img) > 50:
                        if b64_img.startswith("data:image/"):
                            image_uri = b64_img
                        else:
                            mime = _detect_b64_mime(b64_img)
                            image_uri = f"data:{mime};base64,{b64_img}"
                        model_tag = data.get("model", "")
                        source_label = "cloudflare-flux" if "flux" in model_tag.lower() else "cloudflare-workers-ai"
                        return {
                            "success": True,
                            "image_data": image_uri,
                            "source": source_label,
                            "quota_exceeded": False,
                            "error": None,
                        }

                    return {
                        "success": False,
                        "image_data": None,
                        "source": "cloudflare-workers-ai",
                        "quota_exceeded": False,
                        "error": "Cloudflare Worker returned JSON without image data.",
                    }

                # Standard raw binary image response from saurav-z/free-image-generation-api/worker.js
                if len(body_bytes) < 100:
                    return {
                        "success": False,
                        "image_data": None,
                        "source": "cloudflare-workers-ai",
                        "quota_exceeded": False,
                        "error": "Cloudflare Worker returned an empty image payload.",
                    }

                mime = _detect_image_mime(body_bytes, content_type)
                b64 = base64.b64encode(body_bytes).decode("utf-8")
                return {
                    "success": True,
                    "image_data": f"data:{mime};base64,{b64}",
                    "source": "cloudflare-workers-ai",
                    "quota_exceeded": False,
                    "error": None,
                }

            # Error status handling
            err_detail = resp.text[:300]
            try:
                err_json = resp.json()
                err_part = err_json.get("error", "")
                det_part = err_json.get("details", "")
                if err_part or det_part:
                    err_detail = f"{err_part} ({det_part})" if (err_part and det_part) else (err_part or det_part)
            except Exception:
                pass

            if resp.status_code in (401, 403):
                return {
                    "success": False,
                    "image_data": None,
                    "source": "cloudflare-workers-ai",
                    "quota_exceeded": False,
                    "auth_failed": True,
                    "error": (
                        f"Cloudflare Worker authentication failed ({resp.status_code}): {err_detail}. "
                        "Verify CF_WORKER_API_KEY in .env matches the API_KEY variable in Cloudflare."
                    ),
                }

            if resp.status_code == 405:
                return {
                    "success": False,
                    "image_data": None,
                    "source": "cloudflare-workers-ai",
                    "quota_exceeded": False,
                    "error": (
                        "Cloudflare Worker returned 405 Not Allowed. "
                        "Ensure CF_WORKER_URL points to the root Worker URL (https://<name>.<subdomain>.workers.dev) with no extra path."
                    ),
                }

            if resp.status_code == 429:
                return {
                    "success": False,
                    "image_data": None,
                    "source": "cloudflare-workers-ai",
                    "quota_exceeded": True,
                    "error": f"Cloudflare Workers AI rate/quota limit reached (429): {err_detail}",
                }

            hint = ""
            if "reading 'run'" in err_detail or "binding" in err_detail.lower():
                hint = " Make sure you added the Workers AI binding named 'AI' in Worker Settings -> Bindings."

            return {
                "success": False,
                "image_data": None,
                "source": "cloudflare-workers-ai",
                "quota_exceeded": False,
                "error": f"Cloudflare Worker error ({resp.status_code}): {err_detail}.{hint}",
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "image_data": None,
                "source": "cloudflare-workers-ai",
                "quota_exceeded": False,
                "error": "Cloudflare Worker image generation timed out after 45s. Please try again.",
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "image_data": None,
                "source": "cloudflare-workers-ai",
                "quota_exceeded": False,
                "error": f"Could not reach Cloudflare Worker at {url}: {str(e)}",
            }


# Singleton instance
image_generator = ImageGenerator()
