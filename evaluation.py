"""
Standardized AI Evaluation Engine for BUILD THE FUTURE - AI Prompt Battle
Maintains consistent scoring standards across all 8 challenge categories:
1. Thematic Relevance & Challenge Alignment (0-25)
2. Creativity & Originality / Imagination (0-25)
3. Prompt Engineering & Technical Quality (0-25)
4. Visual & Future Impact / Builder Ethos (0-25)
Total Score: 0 - 100
"""

import os
import re
import math
import random
from typing import Dict, Any

# Technical prompt engineering keywords and aesthetic modifiers
LIGHTING_TERMS = {
    "cinematic lighting", "volumetric lighting", "god rays", "bioluminescent", "ambient occlusion",
    "golden hour", "blue hour", "dappled sunlight", "neon glow", "crepuscular rays", "rim lighting",
    "chromatic aberration", "photorealistic lighting", "soft diffused light", "specular highlights",
    "caustics", "subsurface scattering", "atmospheric glow", "luminous", "iridescent"
}

CAMERA_COMPOSITION_TERMS = {
    "wide angle", "panoramic", "establishing shot", "ultra wide", "depth of field", "bokeh",
    "isometric", "birds eye view", "low angle shot", "macro detail", "8k", "hyper-detailed",
    "octane render", "unreal engine 5", "ray tracing", "photorealistic", "imax", "cinematic composition",
    "rule of thirds", "symmetrical", "telephoto", "anamorphic lens"
}

FUTURISTIC_VISION_TERMS = {
    "sustainable", "solarpunk", "biophilic", "quantum", "holographic", "autonomous",
    "cybernetic", "zero-emission", "carbon-neutral", "renewable", "modular", "adaptive",
    "symbiotic", "neural", "serverless", "distributed", "telepresence", "terraforming",
    "geodesic", "nanotech", "cleantech", "clean energy", "next-generation", "interstellar",
    "bio-regenerative", "kinetic", "harmonious", "eco-friendly", "empowerment"
}

CLICHE_OR_VAGUE_TERMS = {
    "good", "nice", "pretty", "cool", "future", "futuristic", "best quality", "masterpiece",
    "trending on artstation", "beautiful", "high quality", "hd", "stuff", "things"
}

class AIEvaluator:
    def __init__(self):
        pass

    def evaluate_submission(self, prompt: str, challenge: Dict[str, Any], player_name: str = "Builder") -> Dict[str, Any]:
        """
        Evaluate a prompt submission against an assigned challenge.
        Maintains consistent scoring standards across all challenge categories.
        """
        prompt_clean = prompt.strip()
        prompt_lower = prompt_clean.lower()
        words = re.findall(r'\b[a-z0-9\-]+\b', prompt_lower)
        word_count = len(words)

        # -------------------------------------------------------------
        # 1. THEMATIC RELEVANCE TO ASSIGNED CHALLENGE (0 - 25 points)
        # -------------------------------------------------------------
        # Extracts key concept terms from challenge title, brief, keywords, and category
        challenge_title = challenge.get("title", "").lower()
        challenge_brief = challenge.get("brief", "").lower()
        challenge_category = challenge.get("category", "").lower()
        keywords = [k.lower() for k in challenge.get("inspiration_keywords", [])]
        visual_goals = challenge.get("visual_goals", "").lower()

        # Build challenge target vocabulary
        target_tokens = set()
        for text in [challenge_title, challenge_brief, visual_goals]:
            tokens = re.findall(r'\b[a-z]{4,}\b', text)
            target_tokens.update(tokens)
        for kw in keywords:
            target_tokens.update(re.findall(r'\b[a-z]{3,}\b', kw))

        # Common stop words to exclude from relevance scoring
        stop_words = {
            "with", "that", "this", "from", "where", "into", "their", "have", "some", "what",
            "show", "design", "depict", "portray", "imagine", "envision", "visualize", "create"
        }
        target_tokens = target_tokens - stop_words

        matched_tokens = set()
        for token in target_tokens:
            if token in prompt_lower:
                matched_tokens.add(token)

        # Keyword direct matches
        kw_matches = sum(1 for kw in keywords if kw in prompt_lower or any(part in prompt_lower for part in kw.split()))

        # Category alignment check
        category_relevance = 0
        if any(cat_word in prompt_lower for cat_word in challenge_category.split() if len(cat_word) > 3):
            category_relevance = 3

        # Base relevance score calculation
        # Normalized so every category has balanced opportunity
        token_ratio = len(matched_tokens) / max(len(target_tokens), 12)
        relevance_score = 10 + (token_ratio * 12) + min(kw_matches * 2.5, 5) + category_relevance
        relevance_score = min(max(relevance_score, 8.0), 25.0)

        # -------------------------------------------------------------
        # 2. CREATIVITY & ORIGINALITY / IMAGINATION (0 - 25 points)
        # -------------------------------------------------------------
        # Evaluates vocabulary diversity, length, futuristic concepts, and avoiding lazy cliches
        unique_words = set(words)
        vocab_richness = len(unique_words) / max(word_count, 1)

        # Count futuristic visionary concepts
        vision_matches = sum(1 for v in FUTURISTIC_VISION_TERMS if v in prompt_lower)

        # Penalty for over-reliance on vague filler buzzwords
        cliche_count = sum(1 for c in CLICHE_OR_VAGUE_TERMS if c in prompt_lower)
        cliche_penalty = min(cliche_count * 0.8, 3.0)

        # Syllable / complexity bonus for rich descriptive writing
        complex_words = sum(1 for w in unique_words if len(w) > 7)

        creativity_score = 9.0 + (min(word_count, 45) / 45.0 * 6.0) + (vocab_richness * 4.0) + min(vision_matches * 1.5, 6.0) + min(complex_words * 0.5, 3.0) - cliche_penalty
        creativity_score = min(max(creativity_score, 7.0), 25.0)

        # -------------------------------------------------------------
        # 3. PROMPT ENGINEERING & TECHNICAL QUALITY (0 - 25 points)
        # -------------------------------------------------------------
        # Evaluates lighting, camera, render engine, resolution, composition specificity
        lighting_hits = [term for term in LIGHTING_TERMS if term in prompt_lower]
        camera_hits = [term for term in CAMERA_COMPOSITION_TERMS if term in prompt_lower]

        has_lighting = len(lighting_hits) > 0
        has_camera = len(camera_hits) > 0

        # Structural discipline: use of descriptive clauses, commas, structured style
        has_structure = "," in prompt_clean or ";" in prompt_clean

        technical_score = 8.0
        technical_score += min(len(lighting_hits) * 3.0, 7.0)
        technical_score += min(len(camera_hits) * 3.0, 7.0)
        if has_structure:
            technical_score += 2.0
        if 20 <= word_count <= 80:
            technical_score += 2.0  # Sweet spot for prompt engineering

        technical_score = min(max(technical_score, 6.0), 25.0)

        # -------------------------------------------------------------
        # 4. VISUAL & FUTURE IMPACT / BUILDER ETHOS (0 - 25 points)
        # -------------------------------------------------------------
        # Evaluates alignment with the AWS Student Builder ethos:
        # Empowering, collaborative, constructive, human-centric, cloud/sustainable innovation
        builder_positive_signals = {
            "collaborative", "students", "community", "clean", "sustainable", "future",
            "healing", "restoring", "protecting", "connecting", "empowerment", "accessible",
            "learning", "discovery", "pioneering", "exploration", "hope", "living", "harmony"
        }
        builder_hits = [sig for sig in builder_positive_signals if sig in prompt_lower]

        # Narrative coherence
        impact_score = 10.0 + min(len(builder_hits) * 2.2, 8.0) + (min(word_count, 35) / 35.0 * 5.0)
        # Subtle seed determinism based on prompt hash to keep exact score consistent for identical prompt
        hash_seed = (sum(ord(c) for c in prompt_clean) % 10) / 10.0 * 2.0
        impact_score += hash_seed
        impact_score = min(max(impact_score, 8.0), 25.0)

        # -------------------------------------------------------------
        # FINAL AGGREGATE & CALIBRATION
        # -------------------------------------------------------------
        relevance_score = round(relevance_score, 1)
        creativity_score = round(creativity_score, 1)
        technical_score = round(technical_score, 1)
        impact_score = round(impact_score, 1)

        total_score = round(relevance_score + creativity_score + technical_score + impact_score, 1)
        # Clamp between 25 and 100
        total_score = max(25.0, min(100.0, total_score))

        # Grade tier
        if total_score >= 90:
            tier = "Grandmaster Builder"
            tier_badge = "🏆 Future Grandmaster"
            tier_color = "#f59e0b"
        elif total_score >= 80:
            tier = "Lead Innovator"
            tier_badge = "⚡ Cloud Innovator"
            tier_color = "#3b82f6"
        elif total_score >= 70:
            tier = "Creative Engineer"
            tier_badge = "🌟 Skilled Craftsman"
            tier_color = "#10b981"
        elif total_score >= 55:
            tier = "Promising Builder"
            tier_badge = "🌱 Rising Builder"
            tier_color = "#8b5cf6"
        else:
            tier = "Apprentice Promptor"
            tier_badge = "🚀 Explorer"
            tier_color = "#94a3b8"

        # Specialized Badges based on performance
        special_badges = []
        if relevance_score >= 22.0:
            special_badges.append("🎯 Laser Thematic Focus")
        if creativity_score >= 22.0:
            special_badges.append("💡 Visionary Originality")
        if technical_score >= 22.0:
            special_badges.append("🔬 Prompt Craft Virtuoso")
        if impact_score >= 22.0:
            special_badges.append("🌍 Social Impact Champion")
        if len(special_badges) == 0:
            special_badges.append(tier_badge)

        # Constructive AI Feedback Commentary
        category_name = challenge.get("category", "the theme")
        feedback_points = []
        strengths = []
        tips = []

        if matched_tokens:
            strengths.append(f"Strongly resonated with {category_name} concepts: {', '.join(list(matched_tokens)[:3])}.")
        else:
            tips.append(f"Incorporate more specific scenario anchors from '{challenge.get('title')}' such as {', '.join(challenge.get('inspiration_keywords', [])[:2])}.")

        if has_lighting:
            strengths.append(f"Sophisticated lighting direction ({', '.join(lighting_hits[:2])}) creates deep visual mood.")
        else:
            tips.append("Try adding precise lighting cues (e.g. 'bioluminescent accents', 'golden hour atmospheric rays').")

        if has_camera:
            strengths.append(f"Excellent cinematic framing using {camera_hits[0]}.")
        else:
            tips.append("Specify camera framing or render aesthetics (e.g. 'cinematic wide establishing shot', 'macro volumetric view').")

        if word_count < 15:
            tips.append("Expand on environmental context and materials to give the generative model more creative nuance.")
        elif word_count > 60:
            strengths.append("Rich, multi-layered descriptive storytelling paints a complete visual world.")

        summary_comment = (
            f"{player_name}'s prompt presents an inspiring future vision for {category_name}. "
            f"Scoring {total_score}/100 with standout execution in {('Relevance' if relevance_score >= max(creativity_score, technical_score) else 'Creativity' if creativity_score >= technical_score else 'Technical Craft')}."
        )

        return {
            "total_score": total_score,
            "tier": tier,
            "tier_badge": tier_badge,
            "tier_color": tier_color,
            "special_badges": special_badges,
            "breakdown": {
                "thematic_relevance": {
                    "score": relevance_score,
                    "max": 25,
                    "title": "Thematic Relevance & Challenge Alignment",
                    "description": f"How faithfully the prompt interprets '{challenge.get('title')}' in {category_name}"
                },
                "creativity_originality": {
                    "score": creativity_score,
                    "max": 25,
                    "title": "Creativity & Originality",
                    "description": "Novelty of imagination, forward-looking vision, and unique conceptual combinations"
                },
                "prompt_engineering": {
                    "score": technical_score,
                    "max": 25,
                    "title": "Prompt Engineering & Technical Quality",
                    "description": "Framing, lighting, camera angle, textural precision, and artistic direction"
                },
                "future_impact": {
                    "score": impact_score,
                    "max": 25,
                    "title": "Visual & Future Impact",
                    "description": "Inspiring builder ethos, emotional resonance, and constructive future worldbuilding"
                }
            },
            "metrics": {
                "word_count": word_count,
                "vocab_richness": round(vocab_richness * 100, 1),
                "matched_keywords": list(matched_tokens)[:6],
                "lighting_tags": lighting_hits,
                "camera_tags": camera_hits
            },
            "summary_comment": summary_comment,
            "strengths": strengths,
            "tips": tips
        }

ai_evaluator = AIEvaluator()

