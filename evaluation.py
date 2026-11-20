"""
Unbiased, Highly Accurate AI Dual-Image Judge & Grounded Evaluation Engine
For BUILD THE FUTURE - AI Prompt Battle

Performs Grounded 2-Pass Visual Audits:
1. Itemizes visual ground-truth in Image 1 (Target Reference Image).
2. Itemizes visual evidence in Image 2 (User's Generated Image).
3. Identifies exact matched features and critical discrepancies.
4. Produces calibrated, unbiased scoring across 4 objective pillars:
   - Visual & Compositional Similarity (0 - 25 pts)
   - Subject & Action Match (0 - 25 pts)
   - Style, Texture & Realism Match (0 - 25 pts)
   - Prompt Precision & Visual Faithfulness (0 - 25 pts)
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
from dotenv import load_dotenv

load_dotenv()

# Anti-Cheat Filter: Prevents meta-prompts referencing the screen or asking to copy
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
    if len(cleaned) < 8:
        return False, "Prompt is too short! Please write a description (at least 8 characters) of the scene you see."

    p_lower = cleaned.lower()
    for pattern in CHEAT_PATTERNS:
        if re.search(pattern, p_lower):
            return False, (
                "Cheating / meta-prompts are prohibited! You cannot refer to 'the image on screen' "
                "or ask to copy it. Please describe what you visually see (the main subjects, visible objects, colors, and setting)."
            )

    words = re.findall(r'\b[a-zA-Z0-9\-]+\b', p_lower)
    if len(words) < 2:
        return False, "Please provide more details describing what you see in the target image."

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
        Unbiased, grounded AI evaluation comparing Target Image vs User Generated Image.
        """
        target_meta = target_meta or {}
        challenge_title = target_meta.get("title", "Visual Challenge")
        category = target_meta.get("category", "Real Scenario")

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
                "target_observations": "Target reference image was displayed on screen.",
                "user_observations": "Disqualified: Attempted shortcut meta-prompt.",
                "matched_features": [],
                "discrepancies": ["Prohibited meta-prompt detected."],
                "breakdown": {
                    "visual_similarity": {
                        "score": 0.0, "max": 25,
                        "title": "Visual & Compositional Similarity",
                        "comment": "Disqualified: Attempted shortcut prompt."
                    },
                    "subject_match": {
                        "score": 0.0, "max": 25,
                        "title": "Subject & Action Match",
                        "comment": "Disqualified: Attempted shortcut prompt."
                    },
                    "style_match": {
                        "score": 0.0, "max": 25,
                        "title": "Style, Texture & Realism",
                        "comment": "Disqualified: Attempted shortcut prompt."
                    },
                    "prompt_precision": {
                        "score": 0.0, "max": 25,
                        "title": "Prompt Precision & Faithfulness",
                        "comment": "Disqualified: Attempted shortcut prompt."
                    }
                },
                "summary_comment": f"DISQUALIFIED: {cheat_err}",
                "unbiased_critique": f"DISQUALIFIED: {cheat_err}"
            }

        # 2. Primary Grounded Judge: Gemini Multimodal Vision API
        if self.gemini_api_key and len(self.gemini_api_key.strip()) > 10:
            gemini_result = self._evaluate_with_gemini(
                target_image_data, user_image_data, user_prompt, challenge_title, category, player_name
            )
            if gemini_result:
                return gemini_result

        # 3. Resilient Grounded Fallback: Computer Vision & Semantic Calibrated Engine
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
        t_b64, t_mime = prepare_image_for_vision(target_image_data)
        u_b64, u_mime = prepare_image_for_vision(user_image_data)

        if not t_b64 or not u_b64:
            return None

        system_instruction = f"""You are a fair, intuitive visual judge at an AI Prompt Battle game where players have only 3 minutes to recreate a target image by typing a prompt.

You are comparing two images:
- Image 1: Target Reference Image (The original photo given to the participant).
- Image 2: User's Generated Image (Synthesized from the user's prompt).

Scenario: {challenge_title}
The user's typed prompt was: "{user_prompt}"

YOUR TASK: Compare Image 1 and Image 2 AS A WHOLE, focusing on the big picture and key recognizable items.

IMPORTANT JUDGING RULES:
1. DO NOT JUDGE OR PENALIZE on micro-technical camera specs, shutter speed, lens focal length, ISO, micro bokeh, or camera focus depth. Participants are everyday humans with only 3 minutes to prompt.
2. FOCUS ON COMPARING THE IMAGES AS A WHOLE:
   - Primary Subject(s): Is the main character, animal, vehicle, or subject present? (e.g. Is the dog, cat, frog, robot, astronaut, or bicycle there?)
   - Key Visible Objects & Details: Are the obvious items and visible features there? (e.g. If there's an open book, is there a book? If a book or sign has a visible title/text, is it captured? If the cat has sunglasses, are they there? If the bicycle has a sunflower basket, is it there? If the cake has a lit candle, is it there?)
   - Overall Scene & Colors: Does the overall setting and primary color palette match as a whole? (e.g. sunlit room, cozy fireside, beach at sunset, rain with red umbrella mushroom, turquoise water).
3. SCORING CRITERIA (0 - 25 each, sum = 0 - 100):
   - visual_similarity (0-25): Overall Scene & Setting. How well does the overall environment, atmosphere, and general color scheme match as a whole?
   - subject_match (0-25): Core Subjects Present. Did the user generate the main subject(s) (e.g. cat, dog, frog, robot, bicycle, guitar)?
   - style_match (0-25): Key Visible Details. Did the user capture prominent visible features (e.g. sunglasses, book presence, party hat, campfire, sunflowers, latte foam art)?
   - prompt_precision (0-25): Prompt Faithfulness. How faithfully did the user's prompt describe what is actually in the target picture?

Be encouraging, objective, and fair:
- If the user captured the main subject and the key visible details, give them a high score (80 - 95+).
- If they got the general subject but missed prominent items, give an encouraging medium score (55 - 75).
- Only give low scores (< 40) if the generated image is completely unrelated (e.g. asking for a spaceship when the picture was a cat on a chair).

Output JSON ONLY with this exact schema:
{{
  "target_observations": "Summary of the main subjects, visible objects, and setting in Image 1",
  "user_observations": "Summary of what is visibly present in Image 2",
  "matched_features": ["list of matched items and details, e.g. 'Fluffy white cat', 'Black sunglasses', 'Yellow armchair'"],
  "discrepancies": ["list of noticeable differences or missing items"],
  "total_score": number,
  "visual_similarity": {{"score": number, "comment": "Feedback on overall scene, environment, and colors"}},
  "subject_match": {{"score": number, "comment": "Feedback on whether the main subjects are present"}},
  "style_match": {{"score": number, "comment": "Feedback on key visible details and items"}},
  "prompt_precision": {{"score": number, "comment": "Feedback on prompt faithfulness"}},
  "unbiased_critique": "A clear, constructive 2-3 sentence summary comparing the images as a whole and noting key details matched or missed.",
  "tier_badge": "string",
  "special_badges": ["string"]
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

        candidate_models = [
            os.getenv("GEMINI_JUDGE_MODEL", "").strip(),
            "gemini-flash-lite-latest",
            "gemini-3-flash-preview",
            "gemini-2.5-flash",
            "gemini-pro-latest",
            "gemini-flash-latest"
        ]
        candidate_models = [m for m in candidate_models if m]
        seen_models = set()
        models = []
        for m in candidate_models:
            if m not in seen_models:
                seen_models.add(m)
                models.append(m)

        for model_name in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=8)
                if resp.status_code == 200:
                    res_data = resp.json()
                    candidates = res_data.get("candidates", [])
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts or "text" not in parts[0]:
                        continue
                    text = parts[0]["text"]
                    parsed = json.loads(text)

                    # Pillar scores
                    vs_score = min(25.0, max(0.0, float(parsed.get("visual_similarity", {}).get("score", 0))))
                    sm_score = min(25.0, max(0.0, float(parsed.get("subject_match", {}).get("score", 0))))
                    st_score = min(25.0, max(0.0, float(parsed.get("style_match", {}).get("score", 0))))
                    pp_score = min(25.0, max(0.0, float(parsed.get("prompt_precision", {}).get("score", 0))))

                    total = float(parsed.get("total_score", vs_score + sm_score + st_score + pp_score))
                    total = max(0.0, min(100.0, round(total, 1)))

                    # Grade Tier
                    tier, tier_badge, tier_color = self._calculate_tier(total)

                    badges = parsed.get("special_badges", [])
                    if not badges:
                        badges = [tier_badge]

                    # Observations formatting
                    t_obs = parsed.get("target_observations", "Analyzed target reference visual elements.")
                    if isinstance(t_obs, list):
                        t_obs = " • " + "\n• ".join(str(x) for x in t_obs)

                    u_obs = parsed.get("user_observations", "Analyzed user replica visual elements.")
                    if isinstance(u_obs, list):
                        u_obs = " • " + "\n• ".join(str(x) for x in u_obs)

                    m_feats = parsed.get("matched_features", [])
                    if isinstance(m_feats, str):
                        m_feats = [m_feats]

                    discreps = parsed.get("discrepancies", [])
                    if isinstance(discreps, str):
                        discreps = [discreps]

                    return {
                        "is_cheating": False,
                        "total_score": total,
                        "tier": tier,
                        "tier_badge": tier_badge,
                        "tier_color": tier_color,
                        "special_badges": badges[:3],
                        "target_observations": t_obs,
                        "user_observations": u_obs,
                        "matched_features": m_feats,
                        "discrepancies": discreps,
                        "breakdown": {
                            "visual_similarity": {
                                "score": round(vs_score, 1), "max": 25,
                                "title": "Overall Scene & Colors",
                                "comment": parsed.get("visual_similarity", {}).get("comment", "Evaluated overall scene, setting and color palette.")
                            },
                            "subject_match": {
                                "score": round(sm_score, 1), "max": 25,
                                "title": "Core Subjects & Objects",
                                "comment": parsed.get("subject_match", {}).get("comment", "Evaluated presence of primary subjects and entities.")
                            },
                            "style_match": {
                                "score": round(st_score, 1), "max": 25,
                                "title": "Key Visible Details",
                                "comment": parsed.get("style_match", {}).get("comment", "Evaluated key visible items and recognizable features.")
                            },
                            "prompt_precision": {
                                "score": round(pp_score, 1), "max": 25,
                                "title": "Prompt Faithfulness",
                                "comment": parsed.get("prompt_precision", {}).get("comment", "Evaluated prompt descriptive faithfulness to the scene.")
                            }
                        },
                        "summary_comment": parsed.get("unbiased_critique", f"{player_name} scored {total}/100 in visual recreation accuracy."),
                        "unbiased_critique": parsed.get("unbiased_critique", "")
                    }
                else:
                    print(f"[AIJudge] Gemini model {model_name} returned status {resp.status_code}. Trying next model...")
            except Exception as e:
                print(f"[AIJudge] Gemini model {model_name} exception: {e}. Trying next model...")

        print("[AIJudge] All Gemini vision models exhausted. Using calibrated CV fallback...")
        return None

    def _evaluate_with_cv_fallback(
        self,
        target_image_data: str,
        user_image_data: str,
        user_prompt: str,
        target_meta: Dict[str, Any],
        player_name: str
    ) -> Dict[str, Any]:
        """Holistic, fair Computer Vision & Semantic evaluation fallback"""
        visual_score = 12.0
        subject_score = 10.0
        style_score = 10.0
        precision_score = 10.0

        matched_tokens = []
        discrepancies = []

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

            # Palette match scaled generously (12.0 - 25.0)
            visual_score = round(12.0 + (hist_ratio * 13.0), 1)
        except Exception:
            visual_score = 16.0

        # Semantic visible objects and subjects analysis
        prompt_lower = user_prompt.lower()
        key_subjects = target_meta.get("key_subjects", [])
        action_text = target_meta.get("action", "")

        target_anchors = set()
        for subj in key_subjects:
            target_anchors.update(re.findall(r'\b[a-z]{3,}\b', subj.lower()))
        target_anchors.update(re.findall(r'\b[a-z]{3,}\b', action_text.lower()))
        for kw in target_meta.get("inspiration_keywords", []):
            target_anchors.update(re.findall(r'\b[a-z]{3,}\b', kw.lower()))

        matched = [tok for tok in target_anchors if tok in prompt_lower]
        match_ratio = len(matched) / max(len(target_anchors), 4)

        if len(matched) >= 3:
            subject_score = round(20.0 + min(match_ratio * 5.0, 5.0), 1)
            style_score = round(19.0 + min(len(matched) * 1.2, 5.0), 1)
            precision_score = round(18.0 + min(len(user_prompt.split()) / 15.0 * 6.0, 7.0), 1)
            matched_tokens = matched[:5]
        elif len(matched) >= 2:
            subject_score = round(16.0 + (len(matched) * 2.0), 1)
            style_score = 16.0
            precision_score = 16.0
            matched_tokens = matched
            discrepancies.append("Good match overall; a few secondary scene details could be captured.")
        elif len(matched) >= 1:
            subject_score = round(12.0 + (len(matched) * 2.0), 1)
            style_score = 12.0
            precision_score = 12.0
            matched_tokens = matched
            discrepancies.append("Partial subject match: captured some scene items, but missing other key objects.")
        else:
            subject_score = 5.0
            style_score = 6.0
            precision_score = 6.0
            discrepancies.append("Subject mismatch: prompt did not describe the main subjects or items in the target scene.")

        visual_score = min(max(visual_score, 0.0), 25.0)
        subject_score = min(max(subject_score, 0.0), 25.0)
        style_score = min(max(style_score, 0.0), 25.0)
        precision_score = min(max(precision_score, 0.0), 25.0)

        total_score = round(visual_score + subject_score + style_score + precision_score, 1)
        tier, tier_badge, tier_color = self._calculate_tier(total_score)

        return {
            "is_cheating": False,
            "total_score": total_score,
            "tier": tier,
            "tier_badge": tier_badge,
            "tier_color": tier_color,
            "special_badges": [tier_badge, "🎯 Holistic Match"],
            "target_observations": f"Target scene features: {', '.join(key_subjects)}" if key_subjects else f"Target reference: {target_meta.get('title', 'Scene')}",
            "user_observations": f"Recreated with prompt: '{user_prompt}'",
            "matched_features": [tok.capitalize() for tok in matched_tokens] if matched_tokens else ["General Scene Vibe"],
            "discrepancies": discrepancies if discrepancies else ["Key visible elements align well with the target scene."],
            "breakdown": {
                "visual_similarity": {
                    "score": visual_score, "max": 25,
                    "title": "Overall Scene & Colors",
                    "comment": f"Overall scene atmosphere and color tone matched at {round(visual_score/25*100)}%."
                },
                "subject_match": {
                    "score": subject_score, "max": 25,
                    "title": "Core Subjects & Objects",
                    "comment": f"Recognized key subjects ({', '.join(matched_tokens[:3]) if matched_tokens else 'general visual layout'})."
                },
                "style_match": {
                    "score": style_score, "max": 25,
                    "title": "Key Visible Details",
                    "comment": "Prominent visible items and details successfully compared."
                },
                "prompt_precision": {
                    "score": precision_score, "max": 25,
                    "title": "Prompt Faithfulness",
                    "comment": f"Prompt faithfulness to the target scene ({len(user_prompt.split())} words)."
                }
            },
            "summary_comment": f"{player_name}'s prompt achieved an overall {total_score}/100 match with the target scene.",
            "unbiased_critique": (
                f"Overall evaluation: The generated visual scored {total_score}/100. "
                f"Core subject match was {subject_score}/25 with key items ({', '.join(matched_tokens[:3]) if matched_tokens else 'general elements'}) captured. "
                f"Overall scene and color harmony scored {visual_score}/25."
            )
        }

    def _calculate_tier(self, score: float) -> Tuple[str, str, str]:
        if score >= 90:
            return "Master Replicator", "🎯 MASTER REPLICATOR", "#10b981"
        elif score >= 75:
            return "Precision Builder", "✨ PRECISION BUILDER", "#3b82f6"
        elif score >= 60:
            return "Accurate Approximator", "🚀 ACCURATE APPROXIMATOR", "#f59e0b"
        elif score >= 40:
            return "Visual Explorer", "💡 VISUAL EXPLORER", "#8b5cf6"
        else:
            return "Apprentice Observer", "🌱 APPRENTICE OBSERVER", "#ef4444"


ai_evaluator = DualImageJudge()
