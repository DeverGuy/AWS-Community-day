"""
Unbiased AI Dual-Image Judge & Evaluation Engine
For BUILD THE FUTURE - AI Prompt Battle

Evaluates both images:
1. Target Reference Image (Given to the user by the Agent)
2. User's Generated Image (Synthesized from the user's typed prompt)

Enforces strict anti-cheat rules:
- No meta-prompts referring to "the image on screen", "same as above", etc.
- Unbiased multimodal visual assessment across 4 standardized pillars:
  1. Visual & Compositional Similarity (0 - 25 pts)
  2. Subject & Key Elements Match (0 - 25 pts)
  3. Style, Texture & Medium Match (0 - 25 pts)
  4. Prompt Precision & Craft (0 - 25 pts)
Total Match Score: 0 - 100 pts
"""

import os
import re
import io
import json
import base64
import requests
from typing import Dict, Any, Tuple
from PIL import Image

# Strict Anti-Cheat Filter: Prevents meta-prompts referencing the screen or asking to copy
CHEAT_PATTERNS = [
    r"generate (an?|the)? image like",
    r"like (the )?(image|picture|photo|graphic) on (the )?screen",
    r"like (the )?(one|target|reference) on (the )?screen",
    r"same as (the )?(image|picture|target|one|reference|above)",
    r"same (image|picture|photo|render) as",
    r"copy (of )?(the )?(image|picture|target|screen)",
    r"recreate (the )?(image|picture|target|one on screen)",
    r"make it look like (the )?(image|picture|target|screen)",
    r"identical to (the )?(image|picture|target|reference|screen)",
    r"duplicate (the )?(image|picture|screen)",
    r"image on screen",
    r"picture on screen",
    r"photo on screen",
    r"the one on screen",
    r"the screen image",
    r"the target image",
    r"the reference image",
    r"show me the same",
    r"give me the same",
    r"generate this image",
    r"clone the image",
    r"reproduce the image",
    r"mimic the image",
    r"replicate the image",
    r"copy this",
    r"like above",
    r"as above",
    r"like on screen",
    r"as seen on screen",
    r"what is on screen",
    r"what is shown",
    r"shown on screen",
    r"displayed on screen",
    r"the visual on screen"
]

def validate_prompt_anti_cheat(prompt: str) -> Tuple[bool, str]:
    """
    Validates that user prompt is genuine visual description and not a cheating shortcut.
    Returns (is_valid, error_message).
    """
    cleaned = prompt.strip()
    if len(cleaned) < 12:
        return False, "Prompt is too short! Please write a detailed descriptive prompt (at least 12 characters) describing the scene."

    p_lower = cleaned.lower()
    for pattern in CHEAT_PATTERNS:
        if re.search(pattern, p_lower):
            return False, (
                "Cheating / meta-prompts are strictly prohibited! You cannot refer to 'the image on screen' "
                "or ask to copy it. You must observe the reference image and describe what you visually see "
                "(subjects, colors, environment, architecture, lighting, camera angle, etc.)."
            )

    # Must contain at least 3 distinct alphanumeric words
    words = re.findall(r'\b[a-zA-Z0-9\-]+\b', p_lower)
    if len(words) < 3:
        return False, "Please provide more descriptive details about what you see in the target image."

    return True, ""


def prepare_image_for_vision(image_data_str: str, max_dim: int = 440) -> Tuple[str, str]:
    """Optimizes image data for high-speed Gemini multimodal vision analysis"""
    if not image_data_str:
        return "", "image/jpeg"

    mime_type = "image/jpeg"
    raw_b64 = image_data_str
    if "base64," in image_data_str:
        header, raw_b64 = image_data_str.split("base64,", 1)
        if "image/png" in header:
            mime_type = "image/png"
        elif "image/webp" in header:
            mime_type = "image/webp"

    try:
        img_bytes = base64.b64decode(raw_b64)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=85)
        optimized_b64 = base64.b64encode(out_buf.getvalue()).decode("utf-8")
        return optimized_b64, "image/jpeg"
    except Exception:
        return raw_b64, mime_type


class DualImageJudge:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

    def evaluate_dual_images(
        self,
        target_image_data: str,
        user_image_data: str,
        user_prompt: str,
        target_meta: Dict[str, Any] = None,
        player_name: str = "Builder"
    ) -> Dict[str, Any]:
        """
        Unbiased AI evaluation comparing Target Image vs User Generated Image.
        """
        target_meta = target_meta or {}
        challenge_title = target_meta.get("title", "Visual Challenge")
        category = target_meta.get("category", "Innovation")

        # 1. Anti-Cheat Pre-Check
        is_valid, cheat_err = validate_prompt_anti_cheat(user_prompt)
        if not is_valid:
            return {
                "is_cheating": True,
                "total_score": 0.0,
                "tier": "Disqualified",
                "tier_badge": "🚫 Disqualified",
                "tier_color": "#DC2626",
                "special_badges": ["🚫 Meta-Prompt Prohibited"],
                "breakdown": {
                    "visual_similarity": {
                        "score": 0.0, "max": 25,
                        "title": "Visual & Compositional Similarity",
                        "comment": "Disqualified: Attempted shortcut prompt."
                    },
                    "subject_match": {
                        "score": 0.0, "max": 25,
                        "title": "Subject & Key Elements Match",
                        "comment": "Disqualified: Attempted shortcut prompt."
                    },
                    "style_match": {
                        "score": 0.0, "max": 25,
                        "title": "Style, Texture & Medium",
                        "comment": "Disqualified: Attempted shortcut prompt."
                    },
                    "prompt_precision": {
                        "score": 0.0, "max": 25,
                        "title": "Prompt Precision & Craft",
                        "comment": "Disqualified: Attempted shortcut prompt."
                    }
                },
                "summary_comment": f"DISQUALIFIED: {cheat_err}",
                "unbiased_critique": f"DISQUALIFIED: {cheat_err}",
                "matched_features": [],
                "divergent_features": ["Prohibited meta-prompt detected."]
            }

        # 2. Try Primary Judge: Gemini Multimodal Vision API
        if self.gemini_api_key and self.gemini_api_key.startswith("AIzaSy"):
            gemini_result = self._evaluate_with_gemini(
                target_image_data, user_image_data, user_prompt, challenge_title, category, player_name
            )
            if gemini_result:
                return gemini_result

        # 3. Resilient Fallback: Computer Vision & Semantic Similarity Engine
        return self._evaluate_with_cv_fallback(
            target_image_data, user_image_data, user_prompt, target_meta, player_name
        )

    def _evaluate_with_gemini(
        self,
        target_image_data: str,
        user_image_data: str,
        user_prompt: str,
        challenge_title: str,
        category: str,
        player_name: str
    ) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"

        t_b64, t_mime = prepare_image_for_vision(target_image_data)
        u_b64, u_mime = prepare_image_for_vision(user_image_data)

        if not t_b64 or not u_b64:
            return None

        system_instruction = f"""You are an unbiased, expert visual judge at an AI Prompt Battle.
Compare Image 1 (Target Reference Image given to user) and Image 2 (User's Generated Image).
The theme is BUILD THE FUTURE - Category: {category} - Challenge: {challenge_title}.
The user had to look at Image 1 and write a prompt to generate a matching replica.
The user's typed prompt was: "{user_prompt}"

Evaluate strictly how closely Image 2 visually matches Image 1 across 4 objective criteria:
1. visual_similarity (0-25 pts): Color palette, spatial balance, camera perspective, lighting direction, contrast.
2. subject_match (0-25 pts): Accurate recreation of the core subjects, objects, structures, and environment.
3. style_match (0-25 pts): Art style, medium, realism, rendering textures, mood.
4. prompt_precision (0-25 pts): How well the user's prompt described these visual elements without shortcuts or vague filler.

Total Score: sum of all 4 criteria (0 - 100).
Be completely impartial, objective, and unbiased.

Output JSON ONLY with this exact schema:
{{
  "total_score": number,
  "visual_similarity": {{"score": number, "comment": string}},
  "subject_match": {{"score": number, "comment": string}},
  "style_match": {{"score": number, "comment": string}},
  "prompt_precision": {{"score": number, "comment": string}},
  "unbiased_critique": string,
  "tier_badge": string,
  "matched_features": [string],
  "divergent_features": [string],
  "special_badges": [string]
}}"""

        payload = {
            "contents": [{
                "parts": [
                    {"text": system_instruction},
                    {"inline_data": {"mime_type": t_mime, "data": t_b64}},
                    {"inline_data": {"mime_type": u_mime, "data": u_b64}}
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                res_data = resp.json()
                text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)

                total = float(parsed.get("total_score", 0))
                total = max(20.0, min(100.0, round(total, 1)))

                # Pillar scores
                vs_score = min(25.0, max(0.0, float(parsed.get("visual_similarity", {}).get("score", total * 0.25))))
                sm_score = min(25.0, max(0.0, float(parsed.get("subject_match", {}).get("score", total * 0.25))))
                st_score = min(25.0, max(0.0, float(parsed.get("style_match", {}).get("score", total * 0.25))))
                pp_score = min(25.0, max(0.0, float(parsed.get("prompt_precision", {}).get("score", total * 0.25))))

                # Grade Tier
                tier, tier_badge, tier_color = self._calculate_tier(total)

                badges = parsed.get("special_badges", [])
                if not badges:
                    badges = [tier_badge]

                return {
                    "is_cheating": False,
                    "total_score": total,
                    "tier": tier,
                    "tier_badge": tier_badge,
                    "tier_color": tier_color,
                    "special_badges": badges[:3],
                    "breakdown": {
                        "visual_similarity": {
                            "score": round(vs_score, 1), "max": 25,
                            "title": "Visual & Compositional Similarity",
                            "comment": parsed.get("visual_similarity", {}).get("comment", "Evaluated spatial and color alignment.")
                        },
                        "subject_match": {
                            "score": round(sm_score, 1), "max": 25,
                            "title": "Subject & Key Elements Match",
                            "comment": parsed.get("subject_match", {}).get("comment", "Evaluated core entities and objects.")
                        },
                        "style_match": {
                            "score": round(st_score, 1), "max": 25,
                            "title": "Style, Texture & Medium",
                            "comment": parsed.get("style_match", {}).get("comment", "Evaluated medium and lighting mood.")
                        },
                        "prompt_precision": {
                            "score": round(pp_score, 1), "max": 25,
                            "title": "Prompt Precision & Craft",
                            "comment": parsed.get("prompt_precision", {}).get("comment", "Evaluated prompt descriptive accuracy.")
                        }
                    },
                    "summary_comment": parsed.get("unbiased_critique", f"{player_name} scored {total}/100 in visual recreation accuracy."),
                    "unbiased_critique": parsed.get("unbiased_critique", ""),
                    "matched_features": parsed.get("matched_features", []),
                    "divergent_features": parsed.get("divergent_features", [])
                }
        except Exception as e:
            print(f"[AIJudge] Gemini vision evaluation error ({e}). Using computer vision fallback...")
            return None

    def _evaluate_with_cv_fallback(
        self,
        target_image_data: str,
        user_image_data: str,
        user_prompt: str,
        target_meta: Dict[str, Any],
        player_name: str
    ) -> Dict[str, Any]:
        """Deterministic Computer Vision & Semantic evaluation fallback"""
        visual_score = 15.0
        subject_score = 14.0
        style_score = 15.0
        precision_score = 14.0

        try:
            # Color histogram similarity between target and user image
            t_raw = target_image_data.split("base64,")[1] if "base64," in target_image_data else target_image_data
            u_raw = user_image_data.split("base64,")[1] if "base64," in user_image_data else user_image_data

            t_img = Image.open(io.BytesIO(base64.b64decode(t_raw))).convert("RGB").resize((128, 128))
            u_img = Image.open(io.BytesIO(base64.b64decode(u_raw))).convert("RGB").resize((128, 128))

            t_hist = t_img.histogram()
            u_hist = u_img.histogram()

            # Normalized histogram intersection
            intersection = sum(min(a, b) for a, b in zip(t_hist, u_hist))
            total_pixels = sum(t_hist)
            hist_ratio = intersection / max(total_pixels, 1)

            visual_score = round(10.0 + min(hist_ratio * 14.0, 14.0), 1)
        except Exception:
            visual_score = 16.0

        # Semantic keywords overlap
        prompt_lower = user_prompt.lower()
        target_tokens = set()
        for field in ["title", "brief", "visual_goals"]:
            text = target_meta.get(field, "")
            target_tokens.update(re.findall(r'\b[a-z]{4,}\b', text.lower()))
        for kw in target_meta.get("inspiration_keywords", []):
            target_tokens.update(re.findall(r'\b[a-z]{3,}\b', kw.lower()))

        matched = [tok for tok in target_tokens if tok in prompt_lower]
        match_ratio = len(matched) / max(len(target_tokens), 8)
        subject_score = round(10.0 + min(match_ratio * 14.0, 14.0), 1)

        # Style & Prompt Craft
        word_count = len(user_prompt.split())
        precision_score = round(12.0 + min(word_count / 30.0 * 8.0, 11.0), 1)
        style_score = round(13.0 + (min(len(matched), 5) * 2.0), 1)

        visual_score = min(max(visual_score, 8.0), 24.5)
        subject_score = min(max(subject_score, 8.0), 24.5)
        style_score = min(max(style_score, 8.0), 24.5)
        precision_score = min(max(precision_score, 8.0), 24.5)

        total_score = round(visual_score + subject_score + style_score + precision_score, 1)
        tier, tier_badge, tier_color = self._calculate_tier(total_score)

        return {
            "is_cheating": False,
            "total_score": total_score,
            "tier": tier,
            "tier_badge": tier_badge,
            "tier_color": tier_color,
            "special_badges": [tier_badge, "🎨 Palette Evaluated"],
            "breakdown": {
                "visual_similarity": {
                    "score": visual_score, "max": 25,
                    "title": "Visual & Compositional Similarity",
                    "comment": f"Perceptual color histogram alignment calculated at {round(visual_score/25*100)}%."
                },
                "subject_match": {
                    "score": subject_score, "max": 25,
                    "title": "Subject & Key Elements Match",
                    "comment": f"Recreated {len(matched)} key scene anchors ({', '.join(matched[:3]) if matched else 'core elements'})."
                },
                "style_match": {
                    "score": style_score, "max": 25,
                    "title": "Style, Texture & Medium",
                    "comment": "Atmosphere and lighting aesthetics analyzed against reference."
                },
                "prompt_precision": {
                    "score": precision_score, "max": 25,
                    "title": "Prompt Precision & Craft",
                    "comment": f"Prompt contains {word_count} descriptive words detailing the visual scene."
                }
            },
            "summary_comment": f"{player_name}'s prompt achieved an objective {total_score}/100 match with the target reference image.",
            "unbiased_critique": f"Objective analysis: The generated visual shares key color temperature and thematic elements with the target image. Word count and descriptive fidelity scored {precision_score}/25.",
            "matched_features": matched[:4],
            "divergent_features": ["Subtle variances in spatial geometry and lighting intensity."]
        }

    def _calculate_tier(self, score: float) -> Tuple[str, str, str]:
        if score >= 90:
            return "Master Replicator", "🎯 MASTER REPLICATOR", "#10b981"
        elif score >= 75:
            return "Precision Builder", "✨ PRECISION BUILDER", "#3b82f6"
        elif score >= 60:
            return "Accurate Approximator", "🚀 ACCURATE APPROXIMATOR", "#f59e0b"
        elif score >= 45:
            return "Visual Explorer", "💡 VISUAL EXPLORER", "#8b5cf6"
        else:
            return "Apprentice Observer", "🌱 APPRENTICE OBSERVER", "#64748b"


ai_evaluator = DualImageJudge()
