"""
Real-Scenario Challenge Management for BUILD THE FUTURE - AI Prompt Battle
Movie Scenes and High-Action Real-World Scenarios
Zero Repetition Engine (Dealt without replacement)
"""
import os
import io
import json
import random
import uuid
import base64
from PIL import Image

OFFICIAL_CATEGORIES = []

DEFAULT_CHALLENGES = [
    {
        "id": "cat-sunglasses-chair",
        "title": "The Sunlit Solarium",
        "brief": "A fluffy white cat wearing stylish black sunglasses sitting comfortably on a bright yellow armchair in a sunlit room.",
        "visual_goals": "Fluffy white cat sitting upright, black sunglasses on its face, bright yellow armchair, sunny morning room with warm daylight.",
        "inspiration_keywords": [
            "White Cat",
            "Black Sunglasses",
            "Yellow Armchair",
            "Sunlit Room",
            "Cozy Indoors"
        ],
        "key_subjects": [
            "fluffy white cat",
            "black sunglasses",
            "bright yellow armchair",
            "sunlit room"
        ],
        "action": "sitting relaxed and upright on the armchair",
        "lighting_mood": "warm natural sunlight streaming from a window",
        "evaluation_focus": "Recreation of the white cat wearing sunglasses on a yellow armchair with bright daytime lighting.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "vintage-red-bicycle",
        "title": "Passage of Summer",
        "brief": "A classic bright red vintage bicycle with a woven wicker basket filled with blooming yellow sunflowers, parked next to a blue wooden door.",
        "visual_goals": "Bright red bicycle frame, woven wicker front basket brimming with yellow sunflowers, rustic blue wooden door, cobblestone ground.",
        "inspiration_keywords": [
            "Red Bicycle",
            "Wicker Basket",
            "Yellow Sunflowers",
            "Blue Door",
            "Cobblestones"
        ],
        "key_subjects": [
            "red vintage bicycle",
            "woven wicker basket",
            "blooming yellow sunflowers",
            "weathered blue wooden door"
        ],
        "action": "parked against the blue door",
        "lighting_mood": "warm golden daylight casting soft shadows",
        "evaluation_focus": "Red bicycle color, prominent sunflower basket, blue door background contrast.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "coffee-latte-book",
        "title": "A Quiet Chapter",
        "brief": "A warm ceramic mug with heart-shaped latte art in the foam, sitting next to an open hardcover book on a dark rustic wooden table.",
        "visual_goals": "Ceramic coffee mug, heart pattern in latte foam, open book with visible printed page text, rustic dark wood table, cozy morning lighting.",
        "inspiration_keywords": [
            "Coffee Mug",
            "Heart Latte Art",
            "Open Book",
            "Wooden Table",
            "Cozy Morning"
        ],
        "key_subjects": [
            "ceramic coffee mug",
            "heart latte art",
            "open hardcover book",
            "dark rustic wooden table"
        ],
        "action": "steaming gently on the table",
        "lighting_mood": "soft warm morning cafe illumination",
        "evaluation_focus": "Heart-shaped latte art foam, open book presence, cozy cafe ambiance.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "robot-chef-cookies",
        "title": "The Sweet Circuit",
        "brief": "A cute round metallic robot wearing a tall white chef hat, holding a baking tray of freshly baked chocolate chip cookies in a bright modern kitchen.",
        "visual_goals": "Smiling metallic robot, white chef hat, metal baking sheet with warm chocolate chip cookies, clean bright modern kitchen.",
        "inspiration_keywords": [
            "Cute Robot",
            "Chef Hat",
            "Chocolate Chip Cookies",
            "Baking Sheet",
            "Modern Kitchen"
        ],
        "key_subjects": [
            "round metallic robot",
            "white chef hat",
            "tray of chocolate chip cookies",
            "modern kitchen"
        ],
        "action": "proudly presenting a freshly baked tray of cookies",
        "lighting_mood": "bright clean indoor kitchen lighting",
        "evaluation_focus": "Cute robot wearing a chef hat, visible chocolate chip cookies, cheerful kitchen setting.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "frog-mushroom-umbrella",
        "title": "Under the Crimson Canopy",
        "brief": "A small cute bright green tree frog sitting on a mossy grey stone under a red mushroom with white polka dots during gentle rain.",
        "visual_goals": "Bright green frog, red toadstool mushroom with white polka dots acting as an umbrella, wet moss-covered stone, soft rain droplets.",
        "inspiration_keywords": [
            "Green Tree Frog",
            "Red Toadstool Mushroom",
            "White Polka Dots",
            "Mossy Stone",
            "Gentle Rain"
        ],
        "key_subjects": [
            "green tree frog",
            "red mushroom with white spots",
            "mossy grey stone",
            "raindrops"
        ],
        "action": "sheltering calmly under the mushroom cap",
        "lighting_mood": "soft diffused rainy day forest lighting",
        "evaluation_focus": "Green frog, red-and-white mushroom umbrella, mossy forest atmosphere.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "astronaut-moon-tea",
        "title": "Tranquility Break",
        "brief": "An astronaut in a white spacesuit sitting in a folding camping chair on the lunar surface, holding a steaming mug with planet Earth in the sky.",
        "visual_goals": "White EVA spacesuit, metallic folding chair, cratered grey moon surface, steaming mug in gloved hand, glowing blue Earth in black starry sky.",
        "inspiration_keywords": [
            "Astronaut",
            "White Spacesuit",
            "Camping Chair",
            "Moon Surface",
            "Planet Earth",
            "Steaming Mug"
        ],
        "key_subjects": [
            "astronaut in white spacesuit",
            "folding camping chair",
            "steaming mug",
            "lunar moon dust",
            "planet Earth in sky"
        ],
        "action": "relaxing in chair drinking tea on the moon",
        "lighting_mood": "stark space sunlight with deep black starry void",
        "evaluation_focus": "Astronaut in chair holding mug, cratered lunar surface, visible blue Earth in sky.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "guitar-beach-campfire",
        "title": "Twilight Embers",
        "brief": "A polished wooden acoustic guitar resting on golden beach sand beside a glowing campfire pit at sunset with ocean waves in the background.",
        "visual_goals": "Warm wooden acoustic guitar, small glowing orange campfire embers, smooth golden beach sand, purple and orange sunset sky over ocean waves.",
        "inspiration_keywords": [
            "Acoustic Guitar",
            "Beach Campfire",
            "Golden Sand",
            "Ocean Sunset",
            "Warm Embers"
        ],
        "key_subjects": [
            "wooden acoustic guitar",
            "glowing campfire pit",
            "sandy beach",
            "ocean sunset"
        ],
        "action": "resting peacefully beside the crackling fire",
        "lighting_mood": "warm firelight glow combined with twilight sunset sky",
        "evaluation_focus": "Wooden guitar placement next to campfire, golden beach sand, sunset ocean horizon.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "dog-party-cake",
        "title": "Another Year Wiser",
        "brief": "A happy golden retriever dog wearing a colorful pointed birthday party hat, sitting in front of a small cake with a single lit candle on a table.",
        "visual_goals": "Smiling golden retriever, striped cone party hat, small decorated cake with one glowing candle, festive colorful background.",
        "inspiration_keywords": [
            "Golden Retriever",
            "Birthday Party Hat",
            "Small Cake",
            "Lit Candle",
            "Celebration"
        ],
        "key_subjects": [
            "golden retriever dog",
            "pointed party hat",
            "cake with lit candle",
            "table"
        ],
        "action": "smiling happily behind the birthday cake",
        "lighting_mood": "warm cheerful indoor party illumination",
        "evaluation_focus": "Golden retriever wearing party hat, cake with candle, joyful celebratory mood.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "red-telephone-desk",
        "title": "The Direct Line",
        "brief": "A classic rotary dial bright red telephone sitting on a polished antique dark wood desk next to a glowing green banker desk lamp.",
        "visual_goals": "Glossy red rotary dial telephone with coiled cord, polished dark mahogany wood desk, brass banker lamp with emerald green glass shade.",
        "inspiration_keywords": [
            "Vintage Red Telephone",
            "Rotary Dial",
            "Dark Wood Desk",
            "Green Banker Lamp",
            "Antique Study"
        ],
        "key_subjects": [
            "red rotary telephone",
            "dark wooden desk",
            "green banker lamp"
        ],
        "action": "resting on the polished executive desk",
        "lighting_mood": "warm focused emerald lamp glow in a dim cozy study",
        "evaluation_focus": "Red rotary telephone, green banker lamp, rich polished wood surface.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "panda-eating-bamboo",
        "title": "The Verdant Sanctuary",
        "brief": "A fluffy black-and-white giant panda sitting upright on green grass, happily munching on fresh green bamboo stalks in a tranquil bamboo grove.",
        "visual_goals": "Fluffy giant panda seated comfortably, holding green bamboo stalks with leaves, lush green grass ground, bamboo forest background.",
        "inspiration_keywords": [
            "Giant Panda",
            "Green Bamboo Stalks",
            "Fluffy Fur",
            "Green Grass",
            "Bamboo Forest"
        ],
        "key_subjects": [
            "giant panda",
            "green bamboo stalks",
            "lush green grass",
            "bamboo grove"
        ],
        "action": "holding and chewing fresh bamboo shoots",
        "lighting_mood": "gentle natural daytime light filtering through bamboo",
        "evaluation_focus": "Panda bear holding green bamboo, natural bamboo forest setting, cheerful peaceful vibe.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "lighthouse-coastal-cliff",
        "title": "Sentinel of the Deep",
        "brief": "A tall red-and-white striped lighthouse standing on a dark rocky coastal cliff, beaming a bright warm light beam over ocean waves at dusk.",
        "visual_goals": "Red and white striped lighthouse tower, dark jagged sea cliff rocks, powerful yellow beam of light cutting through dusk sky, ocean waves.",
        "inspiration_keywords": [
            "Red and White Lighthouse",
            "Rocky Cliff",
            "Yellow Light Beam",
            "Twilight Ocean",
            "Coastal Waves"
        ],
        "key_subjects": [
            "red and white lighthouse",
            "rocky cliff",
            "bright light beam",
            "ocean waves at dusk"
        ],
        "action": "projecting its beacon light across the darkening water",
        "lighting_mood": "deep blue hour dusk with glowing yellow lighthouse lantern",
        "evaluation_focus": "Striped red-white lighthouse, prominent light beam, coastal rocks and evening ocean.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "greenhouse-tropical-plants",
        "title": "The Glass Conservatory",
        "brief": "Interior of a sunlit glass dome greenhouse filled with vibrant green tropical monstera leaves, blooming purple orchids, and hanging ferns.",
        "visual_goals": "Glass pane dome ceiling, large split-leaf monstera plants, bright purple orchid flowers, hanging wicker planters, sunny botanical atmosphere.",
        "inspiration_keywords": [
            "Glass Greenhouse",
            "Tropical Plants",
            "Monstera Leaves",
            "Purple Orchids",
            "Hanging Ferns",
            "Sunlit Conservatory"
        ],
        "key_subjects": [
            "glass greenhouse dome",
            "large monstera leaves",
            "blooming purple orchids",
            "hanging ferns"
        ],
        "action": "flourishing inside the humid sunlit conservatory",
        "lighting_mood": "bright golden sunlight streaming through geometric glass panes",
        "evaluation_focus": "Abundant green plants with purple orchids, architectural glass dome, sunlit greenhouse aesthetic.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "pizza-brick-oven",
        "title": "Flames of the Hearth",
        "brief": "A delicious round artisanal pizza with melted bubbling mozzarella cheese, fresh green basil leaves, and red cherry tomatoes inside a brick pizza oven with glowing flames.",
        "visual_goals": "Round golden pizza crust, melted white mozzarella, vibrant green basil leaves, red tomatoes, stone brick oven interior with orange fire embers.",
        "inspiration_keywords": [
            "Neapolitan Pizza",
            "Melted Mozzarella",
            "Fresh Basil",
            "Brick Oven",
            "Wood Fire Flames"
        ],
        "key_subjects": [
            "fresh round pizza",
            "melted cheese and green basil",
            "brick pizza oven",
            "glowing wood flames"
        ],
        "action": "baking on the stone hearth with fire behind it",
        "lighting_mood": "warm golden firelight from the burning wood embers",
        "evaluation_focus": "Appetizing pizza with visible cheese and basil, stone brick oven opening, warm wood fire glow.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "desert-cactus-sunset",
        "title": "Dusk on the Badlands",
        "brief": "A tall green saguaro cactus with white blooming flowers on top, standing in the red sand dunes of a desert during a blazing orange and purple sunset.",
        "visual_goals": "Tall multi-armed green cactus, white crown flowers, red desert sand ripples, brilliant gradient sky of orange, red, and deep purple.",
        "inspiration_keywords": [
            "Saguaro Cactus",
            "White Desert Flowers",
            "Red Sand Dunes",
            "Vibrant Sunset Sky",
            "Desert Horizon"
        ],
        "key_subjects": [
            "tall saguaro cactus",
            "white crown blossoms",
            "red sand desert",
            "orange purple sunset sky"
        ],
        "action": "standing tall against the desert horizon",
        "lighting_mood": "dramatic golden hour sunset with rich orange and violet gradients",
        "evaluation_focus": "Saguaro cactus with white flowers, desert sand setting, warm sunset sky colors.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "cozy-fireplace-cat",
        "title": "Hearthside Slumber",
        "brief": "A cute orange tabby cat curled up fast asleep on a soft knitted blanket on a wooden floor in front of a warm stone fireplace with crackling fire.",
        "visual_goals": "Sleeping orange ginger cat curled into a circle, cream knitted throw blanket, warm stone fireplace hearth, glowing orange fire logs.",
        "inspiration_keywords": [
            "Orange Tabby Cat",
            "Sleeping Cat",
            "Knitted Blanket",
            "Stone Fireplace",
            "Crackling Hearth"
        ],
        "key_subjects": [
            "orange tabby cat",
            "knitted blanket",
            "stone fireplace",
            "crackling fire logs"
        ],
        "action": "sleeping peacefully by the warm hearth",
        "lighting_mood": "warm amber room glow from the fireplace",
        "evaluation_focus": "Curled sleeping orange cat, knitted blanket, stone fireplace with visible fire.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "sailboat-turquoise-sea",
        "title": "Azure Drift",
        "brief": "A modern sleek white sailboat with full sails gliding across crystal-clear turquoise ocean water near a lush green tropical island under a sunny blue sky.",
        "visual_goals": "White hull sailboat with hoisted white sails, bright turquoise transparent water revealing sandy seabed, tropical palm island in background, clear blue sky.",
        "inspiration_keywords": [
            "White Sailboat",
            "Crystal Turquoise Water",
            "Tropical Island",
            "Full White Sails",
            "Sunny Sky"
        ],
        "key_subjects": [
            "white sailboat",
            "clear turquoise water",
            "tropical green island",
            "sunny blue sky"
        ],
        "action": "sailing gracefully across the turquoise lagoon",
        "lighting_mood": "bright midday tropical sunshine with sparkling water reflections",
        "evaluation_focus": "White sailboat, vibrant turquoise ocean water, tropical island backdrop.",
        "is_active": True,
        "created_by": "system"
    }
]


class ChallengeManager:
    def __init__(self, data_file="data/challenges.json"):
        self.data_file = data_file
        self.challenges = []
        # Non-repeating deck state
        self.participant_seen = {}       # participant_id -> set of seen challenge IDs
        self.global_deck_order = []       # Shuffled global IDs
        self.global_deck_index = 0
        self._load()
        self._init_deck()

    def _load(self):
        load_candidates = []
        if os.path.exists("challenges.json"):
            load_candidates.append("challenges.json")
        if self.data_file and os.path.exists(self.data_file) and self.data_file not in load_candidates:
            load_candidates.append(self.data_file)

        for path in load_candidates:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.challenges = json.load(f)
                    return
            except Exception as e:
                print(f"[ChallengeManager] Error loading {path}: {e}")
        self.challenges = [dict(c) for c in DEFAULT_CHALLENGES]

    def _save(self):
        for path in [self.data_file, "challenges.json"]:
            if not path:
                continue
            dir_name = os.path.dirname(path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.challenges, f, indent=2)
            except Exception as e:
                print(f"[ChallengeManager] Error saving {path}: {e}")

    def _init_deck(self):
        ids = [c["id"] for c in self.challenges if c.get("is_active", True)]
        random.shuffle(ids)
        self.global_deck_order = ids
        self.global_deck_index = 0

    def get_all(self, active_only=False):
        raw = [c for c in self.challenges if (not active_only or c.get("is_active", True))]
        results = []
        for c in raw:
            item = dict(c)
            cid = item.get("id")
            for ext in [".jpg", ".jpeg", ".png", ".webp"]:
                if os.path.exists(os.path.join("static", "images", "challenges", f"{cid}{ext}")):
                    item["static_url"] = f"/static/images/challenges/{cid}{ext}"
                    break
            results.append(item)
        return results

    def get_all_challenges(self):
        return self.get_all(active_only=False)

    def get_active_challenges(self, category=None):
        if category:
            return self.get_by_category(category)
        return self.get_all(active_only=True)

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

    def get_unique_target_challenge(
        self,
        participant_id: str = None,
        category: str = None,
        exclude_ids: list = None,
        **kwargs
    ) -> dict:
        """
        Assigns an authentic real-scenario reference image.
        Guarantees ZERO REPETITIONS:
        - Tracks seen challenges per participant.
        - Dealt without replacement from a shuffled deck.
        - Loads curated high-res photo assets in static/images/challenges/ in 0ms!
        """
        exclude_set = set(exclude_ids or [])
        if participant_id:
            seen_set = self.participant_seen.setdefault(participant_id, set())
            exclude_set.update(seen_set)

        pool = self.get_by_category(category) if category else self.get_all(active_only=True)
        if not pool:
            pool = [c for c in DEFAULT_CHALLENGES if c.get("is_active", True)]

        # Filter out already seen / excluded challenges
        unseen_pool = [c for c in pool if c.get("id") not in exclude_set]

        # If participant has seen ALL challenges in the pool, reset their history so they can cycle through fresh
        if not unseen_pool:
            if participant_id:
                self.participant_seen[participant_id] = set()
            unseen_pool = list(pool)

        # Draw the next unique card using global deck or randomized unseen
        selected_ch = None
        for _ in range(len(self.global_deck_order)):
            if self.global_deck_index >= len(self.global_deck_order):
                self._init_deck()
            candidate_id = self.global_deck_order[self.global_deck_index]
            self.global_deck_index += 1
            if candidate_id not in exclude_set:
                candidate_ch = self.get_by_id(candidate_id)
                if candidate_ch and (not category or candidate_ch.get("category") == category):
                    selected_ch = candidate_ch
                    break

        if not selected_ch:
            selected_ch = random.choice(unseen_pool)

        # Record this challenge as seen by this participant
        if participant_id:
            self.participant_seen[participant_id].add(selected_ch["id"])

        target = dict(selected_ch)
        challenge_id = target.get("id", "")
        target["seed"] = random.randint(100000, 999999)

        # Look for local static photo asset
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            local_img_path = os.path.join("static", "images", "challenges", f"{challenge_id}{ext}")
            if os.path.exists(local_img_path):
                try:
                    with open(local_img_path, "rb") as f:
                        b64_data = base64.b64encode(f.read()).decode("utf-8")
                    mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
                    target["image_data"] = f"data:{mime};base64,{b64_data}"
                    target["image_source"] = "cinematic-photo-bank"
                    target["static_url"] = f"/static/images/challenges/{challenge_id}{ext}"
                    target["hidden_prompt"] = f"{target['title']}: {target['brief']}"
                    return target
                except Exception as e:
                    print(f"[ChallengeManager] Error loading local image {local_img_path}: {e}")

        # Fallback to image generator if local file is missing
        from image_generator import image_generator
        target_prompt = f"{target['title']}, {target['brief']}. {target.get('visual_goals', '')}"
        gen = image_generator.generate(
            prompt=target_prompt,
            category=target.get("category", ""),
            challenge_title=target.get("title", ""),
            seed=target["seed"]
        )
        target["image_data"] = gen.get("image_data")
        target["image_source"] = gen.get("source", "agent-synthesizer")
        target["hidden_prompt"] = target_prompt
        return target

    def save_challenge_image(self, challenge_id, image_data):
        if not image_data:
            return None
        os.makedirs(os.path.join("static", "images", "challenges"), exist_ok=True)
        img_path = os.path.join("static", "images", "challenges", f"{challenge_id}.jpg")
        try:
            if isinstance(image_data, str) and "base64," in image_data:
                b64_content = image_data.split("base64,")[1]
                raw_bytes = base64.b64decode(b64_content)
            elif isinstance(image_data, bytes):
                raw_bytes = image_data
            else:
                return None

            with open(img_path, "wb") as f:
                f.write(raw_bytes)

            for c in self.challenges:
                if c.get("id") == challenge_id:
                    c["static_url"] = f"/static/images/challenges/{challenge_id}.jpg"
                    break
            self._save()
            return f"/static/images/challenges/{challenge_id}.jpg"
        except Exception as e:
            print(f"[ChallengeManager] Error saving image for {challenge_id}: {e}")
            return None

    def add_challenge(self, title, brief, category="General", visual_goals="", inspiration_keywords=None, evaluation_focus="", is_active=True, created_by="admin", image_data=None):
        challenge_id = f"custom-{uuid.uuid4().hex[:8]}"
        if isinstance(inspiration_keywords, str):
            inspiration_keywords = [k.strip() for k in inspiration_keywords.split(",") if k.strip()]
        elif not inspiration_keywords:
            inspiration_keywords = []

        new_challenge = {
            "id": challenge_id,
            "category": category or "General",
            "title": title.strip(),
            "brief": brief.strip(),
            "visual_goals": visual_goals.strip(),
            "inspiration_keywords": inspiration_keywords,
            "evaluation_focus": evaluation_focus.strip() or f"Creative visual interpretation of {category}.",
            "is_active": bool(is_active),
            "created_by": created_by
        }
        if image_data:
            self.save_challenge_image(challenge_id, image_data)
            new_challenge["static_url"] = f"/static/images/challenges/{challenge_id}.jpg"

        self.challenges.append(new_challenge)
        self._init_deck()
        self._save()
        return new_challenge

    def remove_challenge(self, challenge_id):
        initial_len = len(self.challenges)
        self.challenges = [c for c in self.challenges if c.get("id") != challenge_id]
        if len(self.challenges) != initial_len:
            self._init_deck()
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
                self._init_deck()
                self._save()
                return c
        return None

    def reset_to_defaults(self):
        self.challenges = [dict(c) for c in DEFAULT_CHALLENGES]
        self._init_deck()
        self._save()
        return self.challenges

    def get_stats(self):
        total = len(self.challenges)
        active = sum(1 for c in self.challenges if c.get("is_active", True))
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "categories": {}
        }

challenge_manager = ChallengeManager()