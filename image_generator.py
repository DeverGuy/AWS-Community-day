"""
Multi-Tier Resilient Image Generation Engine for BUILD THE FUTURE - AI Prompt Battle

Supported Generation Engines:
1. AWS Bedrock (Amazon Titan Image Generator G1 / SDXL) - Cloud Native AWS
2. NVIDIA NIM API (FLUX.1-dev / SDXL)
3. High-Speed AI Generative Cloud (Pollinations Turbo: 512x512 in ~2-3s)
4. Client-Side Direct Fetch Pass-Through (Bypasses server IP rate limits)
5. Standalone Scene Semantic Digital Compositor (Offline Fallback)
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
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))

    def generate(self, prompt: str, category: str = "", challenge_title: str = "", seed: int = None) -> dict:
        """
        Generates an image for the prompt with resilient fallback cascades.
        Passes user prompt as it is without alterations.
        """
        start_time = time.time()
        clean_prompt = prompt.strip()

        # Tier 1: Try AWS Bedrock if credentials exist
        if self.aws_access_key and self.aws_secret_key:
            bedrock_res = self._generate_bedrock(clean_prompt, seed=seed)
            if bedrock_res.get("success"):
                bedrock_res["latency"] = round(time.time() - start_time, 2)
                return bedrock_res
            print(f"[ImageGenerator] Bedrock skipped/failed: {bedrock_res.get('error')}. Cascading...")

        # Tier 2: Try NVIDIA NIM API if key is present
        if self.nvidia_api_key and self.nvidia_api_key.startswith("nvapi-"):
            result = self._generate_nvidia(clean_prompt)
            if result.get("success"):
                result["latency"] = round(time.time() - start_time, 2)
                return result
            print(f"[ImageGenerator] NVIDIA skipped/failed: {result.get('error')}. Cascading to Tier 3...")

        # Tier 3: Try Pollinations AI Cloud (Turbo model, 512x512 for high speed)
        pollinations_result = self._generate_pollinations(clean_prompt, seed=seed)
        if pollinations_result.get("success"):
            pollinations_result["latency"] = round(time.time() - start_time, 2)
            return pollinations_result

        # If Pollinations is rate-limited on the server IP, provide client URL for direct browser fetch
        if pollinations_result.get("rate_limited"):
            print("[ImageGenerator] Server IP rate limited on Pollinations. Providing client fallback URL...")
            pollinations_result["latency"] = round(time.time() - start_time, 2)
            return pollinations_result

        print(f"[ImageGenerator] Cloud cascade failed: {pollinations_result.get('error')}. Cascading to Tier 4 Procedural...")

        # Tier 4: Standalone Scene Semantic Digital Compositor
        procedural_result = self._generate_procedural(clean_prompt, category=category, challenge_title=challenge_title, seed=seed)
        procedural_result["latency"] = round(time.time() - start_time, 2)
        return procedural_result

    def _generate_bedrock(self, prompt: str, seed: int = None) -> dict:
        """Invokes Amazon Titan Image Generator G1 on AWS Bedrock"""
        try:
            import boto3
            client = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )
            body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt[:500]
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "quality": "standard",
                    "height": 512,
                    "width": 512,
                    "cfgScale": 8.0,
                    "seed": seed if seed is not None else random.randint(0, 2147483647)
                }
            }
            import json
            resp = client.invoke_model(
                modelId="amazon.titan-image-generator-v1",
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json"
            )
            res_body = json.loads(resp.get("body").read())
            images = res_body.get("images", [])
            if images:
                return {
                    "success": True,
                    "image_data": f"data:image/jpeg;base64,{images[0]}",
                    "source": "aws-bedrock-titan",
                    "error": None
                }
            return {"success": False, "error": "No images returned by AWS Bedrock"}
        except Exception as e:
            return {"success": False, "error": f"AWS Bedrock error: {str(e)}"}

    def _generate_nvidia(self, prompt: str) -> dict:
        invoke_url = f"https://ai.api.nvidia.com/v1/genai/{self.nvidia_model}"
        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {"prompt": prompt}

        try:
            resp = requests.post(invoke_url, headers=headers, json=payload, timeout=5)
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
            return {"success": False, "error": "NVIDIA API timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_pollinations(self, prompt: str, seed: int = None) -> dict:
        """High-speed Turbo image generation via Pollinations (512x512 in ~2-3s)"""
        try:
            encoded_prompt = urllib.parse.quote(prompt[:300])
            gen_seed = seed if seed is not None else random.randint(1000, 999999)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=turbo&width=512&height=512&nologo=true&seed={gen_seed}"

            resp = requests.get(url, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 1000:
                b64 = base64.b64encode(resp.content).decode("utf-8")
                mime = "image/jpeg" if resp.content.startswith(b'\xff\xd8') else "image/png"
                return {
                    "success": True,
                    "image_data": f"data:{mime};base64,{b64}",
                    "source": "pollinations-turbo",
                    "error": None
                }
            elif resp.status_code == 402:
                # Rate limited on server IP (1 image per 45s per IP)
                return {
                    "success": False,
                    "rate_limited": True,
                    "client_url": url,
                    "error": "Server IP hit free tier rate limit. Client direct fetch available."
                }
            return {"success": False, "error": f"Pollinations returned status {resp.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Pollinations request timed out (15s)"}
        except Exception as e:
            return {"success": False, "error": f"Pollinations error: {str(e)}"}

    def _generate_procedural(self, prompt: str, category: str = "", challenge_title: str = "", seed: int = None) -> dict:
        """
        Photographic / cinematic digital landscape compositor.
        Renders rich visual digital art without text on the canvas so it never leaks hidden prompts.
        """
        try:
            w, h = 512, 512
            img = Image.new("RGB", (w, h), color=(15, 20, 30))
            draw = ImageDraw.Draw(img)

            prompt_hash = sum(ord(c) for c in prompt) if prompt else 42
            actual_seed = seed if seed is not None else (prompt_hash + int(time.time() * 100) % 10000)
            rng = random.Random(actual_seed)

            # Analyze prompt for dynamic color tones
            p_low = prompt.lower()
            if any(k in p_low for k in ["red", "fire", "flame", "sunset", "ferrari", "amber", "warm"]):
                sky_top = (40, 15, 25)
                sky_bottom = (240, 100, 45)
                sun_color = (255, 220, 120)
                ground_color = (30, 20, 25)
            elif any(k in p_low for k in ["neon", "cyberpunk", "tokyo", "rain", "purple", "violet"]):
                sky_top = (15, 10, 35)
                sky_bottom = (90, 20, 120)
                sun_color = (0, 230, 240)
                ground_color = (10, 15, 25)
            elif any(k in p_low for k in ["space", "astronaut", "earth", "star", "cosmic", "abyss"]):
                sky_top = (5, 5, 12)
                sky_bottom = (15, 25, 55)
                sun_color = (100, 180, 255)
                ground_color = (10, 12, 20)
            else:
                sky_top = (20, 35, 60)
                sky_bottom = (180, 140, 90)
                sun_color = (255, 240, 180)
                ground_color = (25, 30, 35)

            # Horizon gradient
            horizon_y = int(h * 0.60)
            for y in range(horizon_y):
                ratio = y / horizon_y
                r = int(sky_top[0] + (sky_bottom[0] - sky_top[0]) * ratio)
                g = int(sky_top[1] + (sky_bottom[1] - sky_top[1]) * ratio)
                b = int(sky_top[2] + (sky_bottom[2] - sky_top[2]) * ratio)
                draw.line([(0, y), (w, y)], fill=(r, g, b))

            # Ground gradient
            for y in range(horizon_y, h):
                ratio = (y - horizon_y) / (h - horizon_y)
                r = int(sky_bottom[0] * 0.3 + (ground_color[0] - sky_bottom[0] * 0.3) * ratio)
                g = int(sky_bottom[1] * 0.3 + (ground_color[1] - sky_bottom[1] * 0.3) * ratio)
                b = int(sky_bottom[2] * 0.3 + (ground_color[2] - sky_bottom[2] * 0.3) * ratio)
                draw.line([(0, y), (w, y)], fill=(r, g, b))

            # Sun / Atmosphere source
            sun_cx = int(w * 0.65)
            sun_cy = int(horizon_y * 0.70)
            for rad in range(60, 5, -5):
                alpha_blend = (65 - rad) / 60
                sr = int(sun_color[0] * alpha_blend + sky_bottom[0] * (1 - alpha_blend))
                sg = int(sun_color[1] * alpha_blend + sky_bottom[1] * (1 - alpha_blend))
                sb = int(sun_color[2] * alpha_blend + sky_bottom[2] * (1 - alpha_blend))
                draw.ellipse([sun_cx - rad, sun_cy - rad, sun_cx + rad, sun_cy + rad], fill=(sr, sg, sb))

            # Mountain ridge / urban silhouettes on horizon
            points = [(0, horizon_y)]
            cur_y = horizon_y
            step = 16
            for x in range(0, w + step, step):
                jitter = rng.randint(-35, 20)
                points.append((x, max(cur_y + jitter, int(h * 0.35))))
            points.append((w, horizon_y))
            draw.polygon(points, fill=(int(ground_color[0] * 1.5), int(ground_color[1] * 1.5), int(ground_color[2] * 1.5)))

            # Foreground dynamic motion lines / light streaks
            for _ in range(12):
                lx1 = rng.randint(0, w)
                ly1 = rng.randint(horizon_y, h)
                lx2 = lx1 + rng.randint(-80, 80)
                ly2 = ly1 + rng.randint(10, 40)
                flare_color = (
                    min(255, sun_color[0] + rng.randint(-20, 20)),
                    min(255, sun_color[1] + rng.randint(-20, 20)),
                    min(255, sun_color[2] + rng.randint(-20, 20))
                )
                draw.line([(lx1, ly1), (lx2, ly2)], fill=flare_color, width=rng.randint(1, 3))

            # Output base64 data URI
            out_buf = io.BytesIO()
            img.save(out_buf, format="JPEG", quality=85)
            b64_str = base64.b64encode(out_buf.getvalue()).decode("utf-8")

            return {
                "success": True,
                "image_data": f"data:image/jpeg;base64,{b64_str}",
                "source": "cinematic-procedural-synth",
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "image_data": None,
                "source": "failed",
                "error": str(e)
            }


image_generator = ImageGenerator()
