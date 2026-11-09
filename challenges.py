"""
Real-Scenario Challenge Management for BUILD THE FUTURE - AI Prompt Battle
Movie Scenes and High-Action Real-World Scenarios
"""

import os
import io
import json
import random
import uuid
import base64
from PIL import Image

OFFICIAL_CATEGORIES = [
    "Cinematic Movie Scenes",
    "Dynamic Objects in Action"
]

DEFAULT_CHALLENGES = [
    # Category 1: Cinematic Movie Scenes
    {
        "id": "movie-vintage-ferrari",
        "category": "Cinematic Movie Scenes",
        "title": "The Riviera Coastal Cliff Drift",
        "brief": "A classic cherry-red vintage sports car drifting around a sharp mountain hairpin curve on a coastal cliff road at golden hour, with white tire smoke curling and the deep blue Mediterranean sea below.",
        "visual_goals": "Cherry-red vintage sports car, dynamic drift angle, white tire smoke, winding mountain asphalt road, rocky coastal cliff, golden hour sunlight flare, deep blue ocean.",
        "inspiration_keywords": ["Vintage Red Sports Car", "Coastal Cliff Drift", "Golden Hour Flare", "Italian Riviera", "Tire Smoke", "Cinematic Film Still"],
        "key_subjects": ["vintage red sports car", "mountain hairpin road", "ocean cliff", "tire smoke"],
        "action": "drifting around a sharp hairpin curve at high speed",
        "lighting_mood": "warm golden hour sunlight, low angle sun flare",
        "evaluation_focus": "Accurate color of the vehicle, dynamic drifting motion and tire smoke, coastal cliff setting, and golden hour lighting.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "movie-tokyo-rain-neon",
        "category": "Cinematic Movie Scenes",
        "title": "Midnight Rain in Neo-Tokyo",
        "brief": "A moody, narrow Tokyo alley drenched in heavy nighttime rain with glowing neon signs, steam rising from street drains, and neon reflections shimmering across wet dark asphalt.",
        "visual_goals": "Wet glistening asphalt street, vibrant neon signs (cyan, magenta, amber), pouring rain atmosphere, urban narrow alley, reflections in puddles.",
        "inspiration_keywords": ["Rainy Tokyo Alley", "Vibrant Neon Signs", "Wet Asphalt Reflections", "Atmospheric Night Haze", "Cinematic Cyberpunk"],
        "key_subjects": ["narrow Tokyo alley", "glowing neon signs", "wet asphalt street", "rain puddles"],
        "action": "heavy rain pouring down, steam rising from street drains",
        "lighting_mood": "dark night with vibrant cyan and magenta neon reflections",
        "evaluation_focus": "Atmospheric rainy night mood, vivid neon lighting reflections on wet ground, narrow urban perspective.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "movie-astronaut-earth",
        "category": "Cinematic Movie Scenes",
        "title": "Spacewalk Over Earth Horizon",
        "brief": "A breathtaking cinematic shot of an astronaut in a pressurized white EVA spacesuit floating in deep space outside a spacecraft, with the brilliant curved blue horizon of planet Earth glowing below.",
        "visual_goals": "Detailed white spacesuit, gold-tinted visor reflection, deep black space background, glowing blue curvature of Earth, bright solar lens flare.",
        "inspiration_keywords": ["Astronaut Spacewalk", "Curved Earth Horizon", "Deep Black Space", "Gold Visor Reflection", "Cinematic IMAX Scale"],
        "key_subjects": ["astronaut in white EVA spacesuit", "curved planet Earth", "deep black space", "spacecraft hull"],
        "action": "spacewalking and floating weightlessly in orbit",
        "lighting_mood": "harsh direct sunlight with solar lens flare against jet-black void",
        "evaluation_focus": "Scale of the earth curvature, detailed spacesuit textures, contrast between brilliant Earth and deep black void.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "movie-gothic-rooftop",
        "category": "Cinematic Movie Scenes",
        "title": "The Gothic Rooftop Sentinel",
        "brief": "A weathered stone gargoyle perched atop a soaring gothic cathedral rooftop, looking down upon a fog-shrouded modern city skyline at blue twilight hour with cinematic rolling clouds.",
        "visual_goals": "Weathered stone gargoyle foreground, dramatic gothic spires, misty blue-hour city skyline below, moody dusk clouds, cinematic high-altitude perspective.",
        "inspiration_keywords": ["Gothic Gargoyle", "Skyscraper Twilight", "Foggy City Skyline", "Blue Hour Mood", "Cinematic High Angle"],
        "key_subjects": ["stone gargoyle", "gothic cathedral spires", "foggy modern skyline", "twilight clouds"],
        "action": "perched motionless looking down over the sprawling metropolis",
        "lighting_mood": "moody blue twilight hour, atmospheric fog, city night lights emerging",
        "evaluation_focus": "Foreground stone sculpture vs background cityscape contrast, atmospheric blue hour fog, dramatic elevation.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "movie-desert-dunes",
        "category": "Cinematic Movie Scenes",
        "title": "Sahara Sandstorm Horizon",
        "brief": "Vast, sweeping golden sand dunes carved by desert winds, with sharp crest shadows and fine sand grains blowing across the ridge under a blazing golden sun flare.",
        "visual_goals": "Sinuous sand dune curves, dramatic light and shadow ridges, fine blowing sand dust, warm golden sand texture, blazing desert sun flare.",
        "inspiration_keywords": ["Golden Sand Dunes", "Desert Wind Ridges", "Sun Flare Horizon", "Blowing Sand Grains", "Cinematic Dunescape"],
        "key_subjects": ["sweeping golden sand dunes", "sharp ridge crests", "blowing sand plumes", "desert horizon"],
        "action": "wind whipping fine sand grains across the knife-edge dune ridges",
        "lighting_mood": "blazing golden sunlight with sharp diagonal shadows on dune faces",
        "evaluation_focus": "Clean geometric curves of the sand ridges, contrast between sunlit and shadowed faces, golden desert atmosphere.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "movie-cyberpunk-subway",
        "category": "Cinematic Movie Scenes",
        "title": "Subway Platform at Blue Hour",
        "brief": "A high-speed modern underground metro train arriving at an illuminated urban station platform, motion blur streaking lights across sleek tiled pillars.",
        "visual_goals": "Sleek subway train with motion blur trails, bright headlights, clean urban platform tiles, cool blue and yellow lighting, vanishing point perspective.",
        "inspiration_keywords": ["Speeding Subway Train", "Motion Blur Lights", "Underground Platform", "Vanishing Point Perspective", "Urban Transit Action"],
        "key_subjects": ["underground metro train", "station platform", "tiled pillars", "overhead yellow lights"],
        "action": "train speeding into station with motion blur light trails",
        "lighting_mood": "cool cyan and blue ambient lighting with warm yellow platform lights",
        "evaluation_focus": "Dynamic speed motion blur, underground station geometry and perspective lines, contrasting headlight glow.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "movie-cyberpunk-market",
        "category": "Cinematic Movie Scenes",
        "title": "Neon Night Market Atmosphere",
        "brief": "A lively outdoor night market filled with glowing lanterns, neon signage, bustling food stalls with rising steam, and vibrant nighttime street life.",
        "visual_goals": "Glowing paper lanterns, neon signs, food stall steam clouds, narrow walkway, warm and cool color contrast, rich street textures.",
        "inspiration_keywords": ["Neon Night Market", "Floating Steam Clouds", "Glowing Lanterns", "Vibrant Street Life", "Rich Urban Texture"],
        "key_subjects": ["bustling night market stalls", "glowing paper lanterns", "neon signs", "rising food steam"],
        "action": "crowds walking through market, vendors cooking with billowing steam",
        "lighting_mood": "warm amber lantern illumination contrasted with cool neon glow",
        "evaluation_focus": "Atmospheric street density, lighting from lanterns and neon, warm culinary steam.",
        "is_active": True,
        "created_by": "system"
    },

    # Category 2: Dynamic Objects in Action
    {
        "id": "action-coffee-splash",
        "category": "Dynamic Objects in Action",
        "title": "Exploding Coffee Cup Kinetics",
        "brief": "A dramatic high-speed photograph capturing a cup of dark coffee exploding into the air, with frozen liquid arcs, coffee droplets suspended in mid-flight, and roasted coffee beans scattering.",
        "visual_goals": "High-speed shutter freeze (1/8000s), dark coffee splash waves, floating roasted beans, ceramic mug, moody rustic backdrop, dramatic side lighting.",
        "inspiration_keywords": ["High-Speed Liquid Splash", "Coffee Droplets Freeze", "Roasted Beans Mid-Air", "Rustic Ceramic Mug", "Dramatic Side Lighting"],
        "key_subjects": ["ceramic coffee mug", "dark coffee liquid waves", "suspended roasted coffee beans", "liquid droplets"],
        "action": "liquid bursting violently upwards in mid-air frozen motion",
        "lighting_mood": "dramatic directional side lighting on dark rustic backdrop",
        "evaluation_focus": "High-speed kinetic freeze effect, detailed liquid droplets and splash geometry, scattering coffee beans.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "action-chef-wok-flame",
        "category": "Dynamic Objects in Action",
        "title": "The Master Chef Wok Inferno",
        "brief": "An intense culinary action shot of a master street chef tossing noodles in a seasoned iron carbon wok, with a towering column of orange flame erupting upward and green scallions flying in mid-air.",
        "visual_goals": "Vibrant roaring orange fire column, seasoned iron wok, chef tossing noodles, flying green scallions, high contrast dark kitchen, motion freeze.",
        "inspiration_keywords": ["Wok Fire Flare", "Noodle Toss Action", "Flying Scallions", "High Contrast Dark Kitchen", "Culinary Energy"],
        "key_subjects": ["iron carbon wok", "roaring orange fire column", "tossed noodles", "green scallions"],
        "action": "chef tossing noodles with a towering burst of cooking flame",
        "lighting_mood": "high-contrast dark environment lit primarily by the roaring orange flame",
        "evaluation_focus": "Intensity of the flame vortex, dynamic food motion mid-toss, focused culinary action.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "action-skateboard-jump",
        "category": "Dynamic Objects in Action",
        "title": "Sunset Stairway Kickflip Apex",
        "brief": "A street skateboarder frozen in mid-air at the apex of a kickflip over an urban concrete stairway, silhouetted against a brilliant sunset sky with silhouette palm trees.",
        "visual_goals": "Mid-air suspended skateboarder, deck rotating mid-kickflip, concrete stairs, warm sunset glow, urban architecture, low angle perspective.",
        "inspiration_keywords": ["Mid-Air Kickflip", "Skater Apex Freeze", "Concrete Stair Set", "Warm Sunset Backlight", "Low Angle Urban Action"],
        "key_subjects": ["skateboarder in mid-air", "spinning skateboard deck", "concrete stairway", "sunset sky"],
        "action": "frozen at the highest apex of a kickflip over stairs",
        "lighting_mood": "warm golden sunset backlight creating dynamic silhouettes",
        "evaluation_focus": "Action pose frozen at apex, skateboard rotation, clear urban stairway context, warm backlight.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "action-guitarist-stage",
        "category": "Dynamic Objects in Action",
        "title": "Stadium Rock Solo in Laser Fog",
        "brief": "A passionate rock guitarist leaning back during an intense guitar solo on a stadium stage, engulfed in dense purple stage haze, piercing laser beams, and flying sweat droplets.",
        "visual_goals": "Electric guitar in hands, dramatic back-bending posture, purple and magenta stage lighting, atmospheric smoke haze, laser light beams.",
        "inspiration_keywords": ["Electric Guitar Solo", "Stadium Stage Fog", "Purple Laser Beams", "Intense Musical Action", "Concert Lighting"],
        "key_subjects": ["electric guitarist", "electric guitar", "dense purple stage haze", "laser beams"],
        "action": "leaning back in an aggressive, emotional guitar solo",
        "lighting_mood": "intense purple and magenta concert spotlights cutting through stage smoke",
        "evaluation_focus": "Musical energy and posture, dramatic concert stage lighting and atmospheric fog effects.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "action-hummingbird-flower",
        "category": "Dynamic Objects in Action",
        "title": "High-Speed Emerald Wingbeat",
        "brief": "An extreme macro high-speed photograph of an iridescent emerald green hummingbird hovering with rapid wing blur at an exotic pink flower, with glistening morning dew droplets.",
        "visual_goals": "Shimmering green feathers, wing blur motion, needle-like beak sipping nectar, vivid pink petals, glistening dew droplets, creamy bokeh background.",
        "inspiration_keywords": ["Emerald Hummingbird Hover", "High-Speed Wing Blur", "Exotic Flower Blossom", "Glistening Dew Drops", "Macro Bokeh"],
        "key_subjects": ["iridescent green hummingbird", "pink exotic flower blossom", "dew droplets", "creamy green bokeh"],
        "action": "hovering precisely in mid-air with rapid wing motion blur",
        "lighting_mood": "soft diffused morning sunlight highlighting iridescent feathers",
        "evaluation_focus": "Precision of the hovering bird and beak position, wing motion blur vs frozen body, vibrant color contrast.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "action-water-splash",
        "category": "Dynamic Objects in Action",
        "title": "Crystalline Water Splash Crown",
        "brief": "A crystal-clear macro photograph of a single water droplet hitting a surface, exploding into a perfectly symmetrical coronet water crown with suspended bead droplets.",
        "visual_goals": "Symmetrical water splash crown, suspended micro droplets, concentric ripples, crystal refraction, pristine aquatic blue lighting.",
        "inspiration_keywords": ["Water Droplet Crown", "High-Speed Liquid Freeze", "Concentric Ripples", "Crystalline Refraction", "Aquatic Macro"],
        "key_subjects": ["water droplet splash crown", "suspended water beads", "concentric ripples", "aquatic blue surface"],
        "action": "single droplet impact forming a high-speed coronet crown",
        "lighting_mood": "clean studio light refracting through crystal-clear water droplets",
        "evaluation_focus": "Symmetry of the splash crown, crystal liquid clarity, micro droplet suspension.",
        "is_active": True,
        "created_by": "system"
    }
]


class ChallengeManager:
    def __init__(self, data_file="data/challenges.json"):
        self.data_file = data_file
        self.challenges = []
        self._load()

    def _load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.challenges = json.load(f)
                    return
            except Exception as e:
                print(f"[ChallengeManager] Error loading {self.data_file}: {e}")
        self.challenges = [dict(c) for c in DEFAULT_CHALLENGES]

    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.challenges, f, indent=2)
        except Exception as e:
            print(f"[ChallengeManager] Error saving {self.data_file}: {e}")

    def get_all(self, active_only=False):
        if active_only:
            return [c for c in self.challenges if c.get("is_active", True)]
        return list(self.challenges)

    def get_by_category(self, category):
        return [c for c in self.challenges if c.get("category") == category and c.get("is_active", True)]

    def get_by_id(self, challenge_id):
        for c in self.challenges:
            if c.get("id") == challenge_id:
                return dict(c)
        return None

    def get_challenge_by_id(self, challenge_id):
        return self.get_by_id(challenge_id)

    def get_random_challenge(self, category=None):
        pool = self.get_by_category(category) if category else self.get_all(active_only=True)
        if not pool:
            pool = [c for c in DEFAULT_CHALLENGES if c.get("is_active", True)]
        return dict(random.choice(pool))

    def get_unique_target_challenge(self, user_seed: int = None, category: str = None, participant_id: str = None, exclude_ids: list = None, **kwargs) -> dict:
        """
        Assigns an authentic real-scenario reference image.
        Loads from curated high-res photo assets in static/images/challenges/ in 0ms!
        """
        pool = self.get_by_category(category) if category else self.get_all(active_only=True)
        if exclude_ids:
            pool = [c for c in pool if c.get("id") not in exclude_ids]
        if not pool:
            pool = [c for c in DEFAULT_CHALLENGES if c.get("is_active", True)]

        # Determine seed from user_seed or participant_id
        seed_val = user_seed
        if seed_val is None and participant_id:
            seed_val = sum(ord(c) for c in participant_id)

        if seed_val is not None:
            rng = random.Random(seed_val)
            base_ch = dict(rng.choice(pool))
        else:
            base_ch = dict(random.choice(pool))

        target = dict(base_ch)
        target["seed"] = seed_val if seed_val is not None else random.randint(1000, 999999)
        challenge_id = target.get("id", "")

        # Look for local static photo asset
        local_img_path = os.path.join("static", "images", "challenges", f"{challenge_id}.jpg")
        if os.path.exists(local_img_path):
            try:
                with open(local_img_path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                target["image_data"] = f"data:image/jpeg;base64,{b64_data}"
                target["image_source"] = "cinematic-photo-bank"
                target["static_url"] = f"/static/images/challenges/{challenge_id}.jpg"
                target["hidden_prompt"] = f"{target['title']}: {target['brief']}"
                return target
            except Exception as e:
                print(f"[ChallengeManager] Error loading local image {local_img_path}: {e}")

        # Fallback to image generator if local file is missing
        from image_generator import image_generator
        target_prompt = f"{base_ch['title']}, {base_ch['brief']}. {base_ch.get('visual_goals', '')}"
        gen = image_generator.generate(
            prompt=target_prompt,
            category=base_ch.get("category", ""),
            challenge_title=base_ch.get("title", ""),
            seed=user_seed
        )
        target["image_data"] = gen.get("image_data")
        target["image_source"] = gen.get("source", "agent-synthesizer")
        target["hidden_prompt"] = target_prompt
        return target

    def add_challenge(self, category, title, brief, visual_goals="", inspiration_keywords=None, evaluation_focus="", is_active=True, created_by="admin"):
        challenge_id = f"custom-{uuid.uuid4().hex[:8]}"
        if isinstance(inspiration_keywords, str):
            inspiration_keywords = [k.strip() for k in inspiration_keywords.split(",") if k.strip()]
        elif not inspiration_keywords:
            inspiration_keywords = []

        new_challenge = {
            "id": challenge_id,
            "category": category,
            "title": title.strip(),
            "brief": brief.strip(),
            "visual_goals": visual_goals.strip(),
            "inspiration_keywords": inspiration_keywords,
            "evaluation_focus": evaluation_focus.strip() or f"Creative visual interpretation of {category}.",
            "is_active": bool(is_active),
            "created_by": created_by
        }
        self.challenges.append(new_challenge)
        self._save()
        return new_challenge

    def remove_challenge(self, challenge_id):
        initial_len = len(self.challenges)
        self.challenges = [c for c in self.challenges if c.get("id") != challenge_id]
        if len(self.challenges) != initial_len:
            self._save()
            return True
        return False

    def toggle_challenge_active(self, challenge_id, is_active=None):
        for c in self.challenges:
            if c.get("id") == challenge_id:
                if is_active is None:
                    c["is_active"] = not c.get("is_active", True)
                else:
                    c["is_active"] = bool(is_active)
                self._save()
                return c
        return None

    def reset_to_defaults(self):
        self.challenges = [dict(c) for c in DEFAULT_CHALLENGES]
        self._save()
        return self.challenges

    def get_stats(self):
        total = len(self.challenges)
        active = sum(1 for c in self.challenges if c.get("is_active", True))
        by_category = {}
        for cat in OFFICIAL_CATEGORIES:
            cat_challenges = [c for c in self.challenges if c.get("category") == cat]
            by_category[cat] = {
                "total": len(cat_challenges),
                "active": sum(1 for c in cat_challenges if c.get("is_active", True))
            }
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "categories": by_category
        }

challenge_manager = ChallengeManager()
