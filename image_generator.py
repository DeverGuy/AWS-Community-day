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

    def generate(self, prompt: str, category: str = "", challenge_title: str = "") -> dict:
        """
        Generate image for the prompt with fallback cascades.
        Returns: {
            "success": bool,
            "image_data": str (data URI),
            "source": str ("nvidia", "pollinations", "procedural"),
            "latency": float,
            "error": str or None
        }
        """
        start_time = time.time()

        # Tier 1: Try NVIDIA NIM API if key is present
        if self.nvidia_api_key and self.nvidia_api_key.startswith("nvapi-"):
            result = self._generate_nvidia(prompt)
            if result.get("success"):
                result["latency"] = round(time.time() - start_time, 2)
                return result
            print(f"[ImageGenerator] NVIDIA generation failed/skipped: {result.get('error')}. Cascading to Tier 2...")

        # Tier 2: Try Pollinations AI Cloud
        pollinations_result = self._generate_pollinations(prompt, category)
        if pollinations_result.get("success"):
            pollinations_result["latency"] = round(time.time() - start_time, 2)
            return pollinations_result

        print(f"[ImageGenerator] Cloud fallback failed: {pollinations_result.get('error')}. Cascading to Tier 3 Procedural...")

        # Tier 3: Standalone Procedural Futuristic Synthesizer
        procedural_result = self._generate_procedural(prompt, category, challenge_title)
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
            resp = requests.post(invoke_url, headers=headers, json=payload, timeout=12)
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
            return {"success": False, "error": "NVIDIA API timed out (25s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_pollinations(self, prompt: str, category: str = "") -> dict:
        try:
            # Enhance prompt slightly for futuristic aesthetic
            enhanced = f"{prompt}, futuristic aesthetic, cinematic lighting, 8k render, masterpiece"
            encoded_prompt = urllib.parse.quote(enhanced[:250])
            seed = random.randint(1000, 999999)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=768&nologo=true&seed={seed}"

            resp = requests.get(url, timeout=9)
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

    def _generate_procedural(self, prompt: str, category: str = "", challenge_title: str = "") -> dict:
        """Procedural futuristic canvas renderer when external networks are unavailable"""
        try:
            w, h = 768, 768
            img = Image.new("RGB", (w, h), color=(10, 15, 30))
            draw = ImageDraw.Draw(img)

            # Choose color palette based on category
            palette_map = {
                "Future of Education": ((30, 80, 160), (120, 220, 255), (255, 180, 50)),
                "Smart Cities and Sustainable Living": ((20, 100, 60), (70, 230, 150), (240, 250, 120)),
                "Artificial Intelligence and Humanity": ((70, 30, 120), (200, 100, 255), (100, 230, 255)),
                "Space Exploration and Future Civilizations": ((20, 15, 60), (255, 120, 70), (255, 230, 120)),
                "Technology for Social Impact": ((100, 60, 20), (255, 170, 60), (80, 230, 200)),
                "Future of Work": ((25, 45, 90), (100, 180, 255), (255, 210, 100)),
                "Cloud-Powered Innovation": ((15, 50, 100), (0, 168, 255), (255, 153, 0)),
                "Robotics and Automation": ((50, 50, 70), (255, 80, 80), (100, 220, 255)),
            }
            deep_col, bright_col, accent_col = palette_map.get(
                category, ((25, 30, 70), (100, 200, 255), (255, 150, 50))
            )

            # Gradient background
            for y in range(h):
                ratio = y / h
                r = int(10 + (deep_col[0] - 10) * ratio)
                g = int(15 + (deep_col[1] - 15) * ratio)
                b = int(25 + (deep_col[2] - 25) * ratio)
                draw.line([(0, y), (w, y)], fill=(r, g, b))

            # Perspective Cyber Grid on bottom half
            horizon_y = int(h * 0.55)
            vp_x = w // 2
            # Radiating grid lines
            for i in range(-12, 13):
                target_x = vp_x + i * 70
                draw.line([(vp_x, horizon_y), (target_x, h)], fill=(bright_col[0]//3, bright_col[1]//3, bright_col[2]//3), width=1)
            # Horizontal depth lines
            for step in range(1, 16):
                depth = (step / 16.0) ** 2.2
                grid_y = int(horizon_y + depth * (h - horizon_y))
                alpha = int(40 + 180 * depth)
                draw.line([(0, grid_y), (w, grid_y)], fill=(bright_col[0]//2, bright_col[1]//2, bright_col[2]//2), width=1)

            # Horizon glow
            draw.line([(0, horizon_y), (w, horizon_y)], fill=bright_col, width=2)

            # Futuristic planetary orb / energy core
            cx, cy, radius = w // 2, int(horizon_y * 0.7), 130
            for r_step in range(radius, 0, -3):
                p_ratio = r_step / radius
                pr = int(accent_col[0] * (1 - p_ratio) + deep_col[0] * p_ratio)
                pg = int(accent_col[1] * (1 - p_ratio) + deep_col[1] * p_ratio)
                pb = int(accent_col[2] * (1 - p_ratio) + deep_col[2] * p_ratio)
                draw.ellipse([cx - r_step, cy - r_step, cx + r_step, cy + r_step], fill=(pr, pg, pb))

            # Orbital rings
            draw.arc([cx - 190, cy - 60, cx + 190, cy + 60], start=0, end=360, fill=bright_col, width=2)
            draw.arc([cx - 240, cy - 40, cx + 240, cy + 40], start=10, end=190, fill=accent_col, width=1)

            # Starfield / data particles
            random.seed(sum(ord(c) for c in prompt))
            for _ in range(90):
                sx = random.randint(20, w - 20)
                sy = random.randint(20, horizon_y - 10)
                sr = random.choice([1, 2, 3])
                sc = random.choice([bright_col, accent_col, (240, 245, 255)])
                draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=sc)

            # Top branding banner overlay
            draw.rectangle([20, 20, w - 20, 85], fill=(15, 20, 35), outline=bright_col, width=1)
            draw.text((40, 32), "BUILD THE FUTURE", fill=accent_col)
            draw.text((40, 52), f"CATEGORY: {category.upper() or 'INNOVATION'}", fill=(200, 220, 255))

            # Prompt label on bottom
            draw.rectangle([20, h - 85, w - 20, h - 20], fill=(15, 20, 35), outline=accent_col, width=1)
            snippet = prompt if len(prompt) < 70 else prompt[:67] + "..."
            draw.text((35, h - 70), f"PROMPT: \"{snippet}\"", fill=(255, 255, 255))
            draw.text((35, h - 45), f"CHALLENGE: {challenge_title or 'Creative Challenge'}", fill=bright_col)

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

