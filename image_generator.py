"""
Image Generation Engine for BUILD THE FUTURE - AI Prompt Battle
Multi-tier resilient generation:
1. NVIDIA NIM API (FLUX.1-dev) via NVIDIA_API_KEY
2. High-speed AI Generative Cloud (Pollinations AI) fallback
3. Offline Procedural Futuristic Synth (Pillow) fallback
"""

import os
import re
import io
import time
import base64
import random
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont

class ImageGenerator:
    def __init__(self):
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY")
        self.nvidia_model = os.getenv("NVIDIA_MODEL", "black-forest-labs/flux.1-dev")

    def generate(self, prompt: str, category: str = "", challenge_title: str = "", seed: int = None) -> dict:
        """
        Generate image for the prompt with fallback cascades.
        Passes user prompt as it is without alterations.
        Returns: {
            "success": bool,
            "image_data": str (data URI),
            "source": str ("nvidia", "pollinations", "procedural"),
            "latency": float,
            "error": str or None
        }
        """
        start_time = time.time()
        clean_prompt = prompt.strip()

        # Tier 1: Try NVIDIA NIM API if key is present
        if self.nvidia_api_key and self.nvidia_api_key.startswith("nvapi-"):
            result = self._generate_nvidia(clean_prompt)
            if result.get("success"):
                result["latency"] = round(time.time() - start_time, 2)
                return result
            print(f"[ImageGenerator] NVIDIA generation failed/skipped: {result.get('error')}. Cascading to Tier 2...")

        # Tier 2: Try Pollinations AI Cloud
        pollinations_result = self._generate_pollinations(clean_prompt, seed=seed)
        if pollinations_result.get("success"):
            pollinations_result["latency"] = round(time.time() - start_time, 2)
            return pollinations_result

        print(f"[ImageGenerator] Cloud fallback failed: {pollinations_result.get('error')}. Cascading to Tier 3 Procedural...")

        # Tier 3: Standalone Procedural Futuristic Synthesizer
        procedural_result = self._generate_procedural(clean_prompt, category=category, challenge_title=challenge_title, seed=seed)
        procedural_result["latency"] = round(time.time() - start_time, 2)
        return procedural_result

    def _generate_nvidia(self, prompt: str) -> dict:
        invoke_url = f"https://ai.api.nvidia.com/v1/genai/{self.nvidia_model}"
        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {"prompt": prompt}

        try:
            resp = requests.post(invoke_url, headers=headers, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                img_b64 = None
                if "artifacts" in data and len(data["artifacts"]) > 0:
                    img_b64 = data["artifacts"][0].get("base64")
                elif "data" in data and len(data["data"]) > 0:
                    img_b64 = data["data"][0].get("b64_json") or data["data"][0].get("base64")
                elif "b64_json" in data:
                    img_b64 = data["b64_json"]

                if img_b64:
                    if not img_b64.startswith("data:"):
                        img_b64 = f"data:image/jpeg;base64,{img_b64}"
                    return {
                        "success": True,
                        "image_data": img_b64,
                        "source": "nvidia-nim",
                        "error": None
                    }
            return {
                "success": False,
                "error": f"NVIDIA status {resp.status_code}: {resp.text[:120]}"
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "NVIDIA API timed out (12s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_pollinations(self, prompt: str, seed: int = None) -> dict:
        try:
            # Send the prompt as it is without forced suffixes
            encoded_prompt = urllib.parse.quote(prompt[:320])
            gen_seed = seed if seed is not None else random.randint(1000, 999999)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=768&nologo=true&seed={gen_seed}"

            resp = requests.get(url, timeout=6)
            if resp.status_code == 200 and len(resp.content) > 1000:
                b64 = base64.b64encode(resp.content).decode("utf-8")
                mime = "image/jpeg" if resp.content.startswith(b'\xff\xd8') else "image/png"
                return {
                    "success": True,
                    "image_data": f"data:{mime};base64,{b64}",
                    "source": "pollinations-ai",
                    "error": None
                }
            return {"success": False, "error": f"Pollinations returned status {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": f"Pollinations error: {str(e)}"}

    def _generate_procedural(self, prompt: str, category: str = "", challenge_title: str = "", seed: int = None) -> dict:
        """
        Procedural futuristic digital art synthesizer.
        Renders rich visual digital art without text on the canvas so it never leaks hidden prompts.
        """
        try:
            w, h = 768, 768
            img = Image.new("RGB", (w, h), color=(10, 15, 30))
            draw = ImageDraw.Draw(img)

            # Seed determination for visual reproducibility and uniqueness
            prompt_hash = sum(ord(c) for c in prompt) if prompt else 42
            actual_seed = seed if seed is not None else (prompt_hash + int(time.time() * 100) % 10000)
            rng = random.Random(actual_seed)

            # Dynamic color palette based on category or prompt keywords
            palette_map = {
                "Future of Education": ((25, 60, 140), (100, 200, 255), (255, 190, 60)),
                "Smart Cities and Sustainable Living": ((15, 80, 50), (60, 220, 140), (230, 245, 100)),
                "Artificial Intelligence and Humanity": ((60, 25, 110), (180, 90, 245), (90, 220, 245)),
                "Space Exploration and Future Civilizations": ((15, 10, 50), (245, 110, 60), (250, 220, 110)),
                "Technology for Social Impact": ((90, 50, 15), (245, 150, 50), (70, 220, 190)),
                "Future of Work": ((20, 40, 80), (90, 170, 245), (245, 200, 90)),
                "Cloud-Powered Innovation": ((10, 45, 95), (0, 158, 245), (255, 145, 0)),
                "Robotics and Automation": ((45, 45, 65), (245, 70, 70), (90, 210, 245)),
            }
            deep_col, bright_col, accent_col = palette_map.get(
                category, ((20, 30, 65), (90, 190, 245), (245, 140, 50))
            )

            # Gradient background
            for y in range(h):
                ratio = y / h
                r = int(10 + (deep_col[0] - 10) * ratio)
                g = int(15 + (deep_col[1] - 15) * ratio)
                b = int(25 + (deep_col[2] - 25) * ratio)
                draw.line([(0, y), (w, y)], fill=(r, g, b))

            # Perspective Cyber Grid on bottom half
            horizon_y = int(h * (0.50 + rng.uniform(-0.05, 0.08)))
            vp_x = w // 2 + int(rng.uniform(-40, 40))

            # Radiating grid lines
            num_lines = rng.randint(14, 22)
            step_x = w // num_lines
            for i in range(-num_lines, num_lines + 1):
                target_x = vp_x + i * step_x
                draw.line([(vp_x, horizon_y), (target_x, h)], fill=(bright_col[0]//3, bright_col[1]//3, bright_col[2]//3), width=1)

            # Horizontal depth lines
            for step in range(1, 18):
                depth = (step / 18.0) ** 2.0
                grid_y = int(horizon_y + depth * (h - horizon_y))
                draw.line([(0, grid_y), (w, grid_y)], fill=(bright_col[0]//2, bright_col[1]//2, bright_col[2]//2), width=1)

            # Horizon glow bar
            draw.line([(0, horizon_y), (w, horizon_y)], fill=bright_col, width=2)

            # Central futuristic architectural construct / celestial focal point
            cx = vp_x
            cy = int(horizon_y * 0.65)
            radius = rng.randint(110, 150)
            
            # Shaded focal sphere / energy nexus
            for r_step in range(radius, 0, -3):
                p_ratio = r_step / radius
                pr = int(accent_col[0] * (1 - p_ratio) + deep_col[0] * p_ratio)
                pg = int(accent_col[1] * (1 - p_ratio) + deep_col[1] * p_ratio)
                pb = int(accent_col[2] * (1 - p_ratio) + deep_col[2] * p_ratio)
                draw.ellipse([cx - r_step, cy - r_step, cx + r_step, cy + r_step], fill=(pr, pg, pb))

            # Architectural / Orbital Rings
            ring_w = radius + rng.randint(40, 90)
            ring_h = int(ring_w * 0.35)
            draw.arc([cx - ring_w, cy - ring_h, cx + ring_w, cy + ring_h], start=0, end=360, fill=bright_col, width=2)
            draw.arc([cx - ring_w - 30, cy - ring_h + 10, cx + ring_w + 30, cy + ring_h - 10], start=20, end=200, fill=accent_col, width=1)

            # Vertical structural spires / futuristic towers on the horizon
            num_spires = rng.randint(4, 8)
            for _ in range(num_spires):
                sx = rng.randint(40, w - 40)
                if abs(sx - cx) < 60:
                    continue
                sh = rng.randint(90, 260)
                sw = rng.randint(18, 38)
                top_y = horizon_y - sh
                # Spire silhouette
                draw.rectangle([sx, top_y, sx + sw, horizon_y], fill=(deep_col[0]//2, deep_col[1]//2, deep_col[2]//2), outline=bright_col, width=1)
                # Spire beacon light
                draw.ellipse([sx + sw//2 - 3, top_y - 6, sx + sw//2 + 3, top_y], fill=accent_col)

            # Starfield / floating volumetric particles
            for _ in range(rng.randint(70, 110)):
                px = rng.randint(10, w - 10)
                py = rng.randint(10, horizon_y - 10)
                pr = rng.choice([1, 2, 3])
                col = rng.choice([bright_col, accent_col, (240, 245, 255)])
                draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=col)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            return {
                "success": True,
                "image_data": f"data:image/jpeg;base64,{b64}",
                "source": "procedural-synth",
                "error": None
            }
        except Exception as e:
            return {"success": False, "error": f"Procedural rendering error: {str(e)}"}

image_generator = ImageGenerator()
