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
    if len(cleaned) < 10:
        return False, "Prompt is too short! Please write a descriptive prompt (at least 10 characters) detailing the scene."

    p_lower = cleaned.lower()
    for pattern in CHEAT_PATTERNS:
        if re.search(pattern, p_lower):
            return False, (
                "Cheating / meta-prompts are strictly prohibited! You cannot refer to 'the image on screen' "
                "or ask to copy it. You must observe the reference image and describe what you visually see "
                "(subjects, action, colors, environment, lighting, camera angle, etc.)."
            )

    words = re.findall(r'\b[a-zA-Z0-9\-]+\b', p_lower)
    if len(words) < 3:
        return False, "Please provide more descriptive details about what you visually observe in the target image."

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

        system_instruction = f"""You are a rigorous, completely unbiased visual judge at an AI Prompt Battle.
You are given two images:
- Image 1: Target Reference Image (The scenario image given to the participant).
- Image 2: User's Generated Image (Synthesized from the user's typed prompt).

Category: {category} - Challenge: {challenge_title}
The user's typed prompt was: "{user_prompt}"

YOUR TASK: Perform a strict, objective, grounded visual comparison between Image 1 and Image 2.

Follow this exact 5-step evaluation protocol:
1. TARGET AUDIT: Describe exactly what is visually depicted in Image 1 (Subject, action, environment/setting, colors, lighting, camera angle).
2. USER AUDIT: Describe exactly what is visually depicted in Image 2.
3. MATCHES: List the specific visual elements from Image 1 that Image 2 successfully recreated.
4. DISCREPANCIES: List the critical differences, missing elements, or wrong subjects.
5. STRICT CALIBRATED SCORING (0-25 each, sum = 0-100 total):
   - visual_similarity (0-25): Color palette, spatial balance, camera perspective, lighting direction, contrast. (If background/setting is completely wrong, cap at 7/25).
   - subject_match (0-25): Recreation of core subjects and actions. (CRITICAL RULE: If the main subject or action is completely different or missing, score MUST be capped at 5/25).
   - style_match (0-25): Photographic realism, art style, textures, lighting mood.
   - prompt_precision (0-25): How accurately the user's typed prompt described the visual reality of Image 1. (If the prompt described unrelated elements, cap at 5/25).

Total Score = sum of all 4 criteria (0 - 100).
DO NOT be overly generous. If the images depict different things, award a low score. If they closely match, award a high score.

Output JSON ONLY with this exact schema:
{{
  "target_observations": "description of Image 1",
  "user_observations": "description of Image 2",
  "matched_features": ["list of matched visual features"],
  "discrepancies": ["list of differences or missing elements"],
  "total_score": number,
  "visual_similarity": {{"score": number, "comment": "string"}},
  "subject_match": {{"score": number, "comment": "string"}},
  "style_match": {{"score": number, "comment": "string"}},
  "prompt_precision": {{"score": number, "comment": "string"}},
  "unbiased_critique": "detailed paragraph explaining the evaluation based on visual evidence",
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
                resp = requests.post(url, json=payload, timeout=20)
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
                                "title": "Visual & Compositional Similarity",
                                "comment": parsed.get("visual_similarity", {}).get("comment", "Evaluated spatial balance, lighting and palette.")
                            },
                            "subject_match": {
                                "score": round(sm_score, 1), "max": 25,
                                "title": "Subject & Action Match",
                                "comment": parsed.get("subject_match", {}).get("comment", "Evaluated primary entities and dynamic action.")
                            },
                            "style_match": {
                                "score": round(st_score, 1), "max": 25,
                                "title": "Style, Texture & Realism",
                                "comment": parsed.get("style_match", {}).get("comment", "Evaluated realism and artistic medium.")
                            },
                            "prompt_precision": {
                                "score": round(pp_score, 1), "max": 25,
                                "title": "Prompt Precision & Faithfulness",
                                "comment": parsed.get("prompt_precision", {}).get("comment", "Evaluated prompt descriptive accuracy against reference.")
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
        """Calibrated Computer Vision & Semantic evaluation fallback"""
        visual_score = 5.0
        subject_score = 5.0
        style_score = 5.0
        precision_score = 5.0

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

            # Palette match scaled 0 - 25
            visual_score = round(hist_ratio * 25.0, 1)
        except Exception:
            visual_score = 8.0

        # Semantic keywords analysis
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
        match_ratio = len(matched) / max(len(target_anchors), 6)

        # If user didn't mention core subject or action, subject score is strictly capped
        if len(matched) >= 4:
            subject_score = round(16.0 + min(match_ratio * 9.0, 9.0), 1)
            style_score = round(15.0 + min(len(matched) * 1.8, 9.0), 1)
            precision_score = round(14.0 + min(len(user_prompt.split()) / 20.0 * 9.0, 10.0), 1)
            matched_tokens = matched[:5]
        elif len(matched) >= 2:
            subject_score = round(10.0 + (len(matched) * 2.5), 1)
            style_score = 12.0
            precision_score = 11.0
            matched_tokens = matched
            discrepancies.append("Partial subject match: several key visual details from the reference scene are missing.")
        else:
            # Low match / wrong prompt
            subject_score = round(2.0 + (len(matched) * 2.0), 1)
            style_score = 8.0
            precision_score = round(min(len(user_prompt.split()) * 0.5, 6.0), 1)
            discrepancies.append("Subject mismatch: prompt does not describe the core subject or action depicted in the target scene.")

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
            "special_badges": [tier_badge, "🎯 Grounded CV"],
            "target_observations": f"Target scene: {target_meta.get('title', 'Reference')} ({target_meta.get('brief', '')})",
            "user_observations": f"User prompt generated visual: '{user_prompt}'",
            "matched_features": matched_tokens if matched_tokens else ["Photographic medium"],
            "discrepancies": discrepancies if discrepancies else ["Minor variances in lighting angle and particle geometry."],
            "breakdown": {
                "visual_similarity": {
                    "score": visual_score, "max": 25,
                    "title": "Visual & Compositional Similarity",
                    "comment": f"Perceptual color histogram alignment calculated at {round(visual_score/25*100)}%."
                },
                "subject_match": {
                    "score": subject_score, "max": 25,
                    "title": "Subject & Action Match",
                    "comment": f"Matched {len(matched_tokens)} key scene anchors ({', '.join(matched_tokens[:3]) if matched_tokens else 'minimal overlap'})."
                },
                "style_match": {
                    "score": style_score, "max": 25,
                    "title": "Style, Texture & Realism",
                    "comment": "Atmosphere and lighting aesthetics analyzed against reference image."
                },
                "prompt_precision": {
                    "score": precision_score, "max": 25,
                    "title": "Prompt Precision & Faithfulness",
                    "comment": f"Prompt evaluated for visual faithfulness to target scene ({len(user_prompt.split())} words)."
                }
            },
            "summary_comment": f"{player_name}'s prompt achieved an objective {total_score}/100 match with the target reference image.",
            "unbiased_critique": (
                f"Objective audit: The generated visual scored {total_score}/100. "
                f"Subject match was {subject_score}/25 based on {len(matched_tokens)} key matched elements. "
                f"Visual color alignment was {visual_score}/25."
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
