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
        "id": "coffee-latte-book",
        "title": "A Quiet Chapter",
        "brief": "A warm ceramic mug with heart latte art in the foam sitting next to a closed hardcover book on a clean wooden table.",
        "visual_goals": "White ceramic coffee mug, heart pattern in latte foam, closed blue hardcover book, clean dark wooden table.",
        "inspiration_keywords": [
            "Coffee Mug",
            "Heart Latte Art",
            "Closed Book",
            "Wooden Table",
            "Morning Light"
        ],
        "key_subjects": [
            "ceramic coffee mug",
            "heart latte art",
            "hardcover book",
            "wooden table"
        ],
        "action": "resting on the table next to the book",
        "lighting_mood": "warm soft morning daylight",
        "evaluation_focus": "Presence of the coffee mug with heart latte art, the book beside it, and the wooden table.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "cat-sunglasses-chair",
        "title": "The Sunlit Solarium",
        "brief": "A fluffy white cat wearing black sunglasses sitting on a bright yellow armchair in a sunlit room.",
        "visual_goals": "Fluffy white cat, black sunglasses on face, bright yellow armchair, sunny clean room.",
        "inspiration_keywords": [
            "White Cat",
            "Black Sunglasses",
            "Yellow Armchair",
            "Sunlit Room"
        ],
        "key_subjects": [
            "fluffy white cat",
            "black sunglasses",
            "bright yellow armchair"
        ],
        "action": "sitting upright on the armchair",
        "lighting_mood": "bright warm daylight",
        "evaluation_focus": "Recreation of the white cat wearing sunglasses on a bright yellow chair.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "dog-party-cake",
        "title": "Another Year Wiser",
        "brief": "A happy golden retriever wearing a colorful party hat in front of a small birthday cake with a single lit candle.",
        "visual_goals": "Smiling golden retriever, pointed cone party hat, small cake with one glowing candle, clean background.",
        "inspiration_keywords": [
            "Golden Retriever",
            "Party Hat",
            "Small Cake",
            "Lit Candle"
        ],
        "key_subjects": [
            "golden retriever dog",
            "pointed party hat",
            "cake with lit candle"
        ],
        "action": "smiling behind the birthday cake",
        "lighting_mood": "cheerful warm indoor lighting",
        "evaluation_focus": "Golden retriever wearing a party hat with a lit candle on the cake.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "frog-mushroom-umbrella",
        "title": "Under the Crimson Canopy",
        "brief": "A small bright green frog sitting on a red mushroom with white polka dots on green moss.",
        "visual_goals": "Bright green frog, red toadstool mushroom with white polka dots, soft green moss, simple background.",
        "inspiration_keywords": [
            "Green Tree Frog",
            "Red Toadstool Mushroom",
            "White Polka Dots",
            "Green Moss"
        ],
        "key_subjects": [
            "green tree frog",
            "red mushroom with white spots",
            "green moss"
        ],
        "action": "perched calmly on the mushroom cap",
        "lighting_mood": "soft diffused natural light",
        "evaluation_focus": "Green frog sitting on the red-and-white spotted mushroom.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "yellow-rubber-duck",
        "title": "The Sunny Drift",
        "brief": "A classic bright yellow rubber duck floating in clean blue water with white soap bubbles.",
        "visual_goals": "Bright yellow rubber duck, clear blue water, fluffy white soap bubbles, clean composition.",
        "inspiration_keywords": [
            "Yellow Rubber Duck",
            "Blue Water",
            "Soap Bubbles",
            "Clean Minimalist"
        ],
        "key_subjects": [
            "yellow rubber duck",
            "clear blue water",
            "white soap bubbles"
        ],
        "action": "floating on calm water with bubbles",
        "lighting_mood": "clean bright studio lighting",
        "evaluation_focus": "Yellow rubber duck floating in blue water with soap bubbles.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "chocolate-cake-slice",
        "title": "Midnight Confection",
        "brief": "A slice of chocolate cake topped with a fresh red strawberry on a white plate.",
        "visual_goals": "Layered dark chocolate cake, fresh red strawberry on top, clean white plate, wooden table.",
        "inspiration_keywords": [
            "Chocolate Cake",
            "Red Strawberry",
            "White Plate",
            "Wooden Table"
        ],
        "key_subjects": [
            "slice of chocolate cake",
            "fresh red strawberry",
            "white ceramic plate"
        ],
        "action": "served on the plate",
        "lighting_mood": "warm soft cafe lighting",
        "evaluation_focus": "Chocolate cake slice with a red strawberry on a white plate.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "red-apple-table",
        "title": "The Crimson Harvest",
        "brief": "A fresh shiny red apple with a small green leaf on a clean wooden table.",
        "visual_goals": "Glossy red apple, small green leaf, water droplets, light wooden table.",
        "inspiration_keywords": [
            "Red Apple",
            "Green Leaf",
            "Wooden Table",
            "Clean Minimalist"
        ],
        "key_subjects": [
            "shiny red apple",
            "small green leaf",
            "wooden table"
        ],
        "action": "resting on the clean table surface",
        "lighting_mood": "soft bright natural daylight",
        "evaluation_focus": "Shiny red apple with green leaf on a wooden table.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "red-rose-vase",
        "title": "Velvet Petal",
        "brief": "A single blooming red rose in a clear glass vase of water on a clean white surface.",
        "visual_goals": "Deep red rose bloom, green stem and leaves, clear glass vase with water, white marble surface.",
        "inspiration_keywords": [
            "Red Rose",
            "Glass Vase",
            "Clear Water",
            "White Marble Table"
        ],
        "key_subjects": [
            "single red rose",
            "clear glass vase",
            "white table"
        ],
        "action": "standing in the vase",
        "lighting_mood": "soft elegant natural light",
        "evaluation_focus": "Single red rose in a clear glass vase on a clean surface.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "orange-juice-glass",
        "title": "Morning Citrus",
        "brief": "A tall glass of fresh orange juice with ice cubes, an orange slice on the rim, and a straw on a table.",
        "visual_goals": "Tall glass of orange juice, visible ice cubes, fresh orange wheel slice on rim, striped straw, wooden table.",
        "inspiration_keywords": [
            "Orange Juice",
            "Tall Glass",
            "Orange Slice",
            "Ice Cubes",
            "Straw"
        ],
        "key_subjects": [
            "glass of orange juice",
            "ice cubes",
            "orange slice",
            "straw"
        ],
        "action": "standing on the table with ice and straw",
        "lighting_mood": "bright sunny morning light",
        "evaluation_focus": "Glass of orange juice with ice, orange slice on the rim, and straw.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "pancakes-syrup-butter",
        "title": "Golden Morning",
        "brief": "A stack of fluffy pancakes topped with melting butter and dripping maple syrup on a plate.",
        "visual_goals": "Stack of three pancakes, melting square of butter on top, dripping maple syrup, clean round plate.",
        "inspiration_keywords": [
            "Pancakes",
            "Melting Butter",
            "Maple Syrup",
            "Breakfast Plate"
        ],
        "key_subjects": [
            "stack of pancakes",
            "melting yellow butter",
            "maple syrup",
            "plate"
        ],
        "action": "stacked neatly with syrup dripping",
        "lighting_mood": "warm cheerful breakfast light",
        "evaluation_focus": "Stack of pancakes with melting butter square and syrup.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "red-telephone-desk",
        "title": "The Direct Line",
        "brief": "A classic bright red vintage rotary dial telephone sitting on a clean wooden desk.",
        "visual_goals": "Glossy red rotary dial telephone, coiled black cord, dark polished wooden desk, simple background.",
        "inspiration_keywords": [
            "Vintage Red Telephone",
            "Rotary Dial",
            "Coiled Cord",
            "Wooden Desk"
        ],
        "key_subjects": [
            "red rotary telephone",
            "coiled cord",
            "wooden desk"
        ],
        "action": "resting on the executive wooden desk",
        "lighting_mood": "warm focused indoor glow",
        "evaluation_focus": "Bright red rotary telephone on a clean wooden desk.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "vintage-red-bicycle",
        "title": "Passage of Summer",
        "brief": "A bright red vintage bicycle with a front wicker basket of yellow flowers against a clean plain white wall.",
        "visual_goals": "Bright red bicycle frame, wicker front basket with yellow sunflowers, plain white wall background.",
        "inspiration_keywords": [
            "Red Bicycle",
            "Wicker Basket",
            "Yellow Sunflowers",
            "White Wall"
        ],
        "key_subjects": [
            "red vintage bicycle",
            "wicker basket with yellow sunflowers",
            "white wall"
        ],
        "action": "parked against the plain wall",
        "lighting_mood": "warm golden daylight",
        "evaluation_focus": "Red vintage bicycle with flower basket against a plain wall.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "robot-chef-cookies",
        "title": "The Sweet Circuit",
        "brief": "A cute small metallic robot wearing a white chef hat holding a chocolate chip cookie on a table.",
        "visual_goals": "Cute metallic robot, white chef hat, holding a chocolate chip cookie, clean wooden table.",
        "inspiration_keywords": [
            "Cute Robot",
            "White Chef Hat",
            "Chocolate Chip Cookie",
            "Wooden Table"
        ],
        "key_subjects": [
            "metallic toy robot",
            "white chef hat",
            "chocolate chip cookie",
            "wooden table"
        ],
        "action": "holding a chocolate chip cookie",
        "lighting_mood": "bright clean daylight",
        "evaluation_focus": "Cute metallic robot wearing a chef hat holding a cookie.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "cozy-fireplace-cat",
        "title": "Hearthside Slumber",
        "brief": "A cute orange tabby kitten sleeping curled up on a soft knitted blanket on a wooden floor by a warm fireplace.",
        "visual_goals": "Sleeping orange kitten curled in a ball, cream knitted blanket, wooden floor, warm fireplace glow.",
        "inspiration_keywords": [
            "Orange Tabby Kitten",
            "Sleeping Cat",
            "Knitted Blanket",
            "Warm Hearth"
        ],
        "key_subjects": [
            "orange tabby kitten",
            "knitted blanket",
            "wooden floor",
            "fireplace"
        ],
        "action": "sleeping peacefully on the blanket",
        "lighting_mood": "warm cozy amber fireplace glow",
        "evaluation_focus": "Sleeping orange kitten on a knitted blanket in front of a fireplace.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "panda-eating-bamboo",
        "title": "The Verdant Sanctuary",
        "brief": "A fluffy giant panda sitting on green grass eating a fresh green bamboo stalk.",
        "visual_goals": "Fluffy giant panda sitting upright, holding green bamboo stalk, lush green grass.",
        "inspiration_keywords": [
            "Giant Panda",
            "Green Bamboo Stalk",
            "Green Grass",
            "Peaceful"
        ],
        "key_subjects": [
            "giant panda",
            "green bamboo stalk",
            "green grass"
        ],
        "action": "sitting and chewing bamboo",
        "lighting_mood": "gentle natural daylight",
        "evaluation_focus": "Panda bear sitting on grass holding and eating green bamboo.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "sailboat-turquoise-sea",
        "title": "Azure Drift",
        "brief": "A sleek white sailboat with full white sails sailing on calm clear turquoise ocean water under a sunny blue sky.",
        "visual_goals": "White hull sailboat with hoisted sails, clear turquoise water, clear blue sky.",
        "inspiration_keywords": [
            "White Sailboat",
            "Hoisted Sails",
            "Turquoise Ocean Water",
            "Sunny Blue Sky"
        ],
        "key_subjects": [
            "white sailboat",
            "full white sails",
            "turquoise ocean water",
            "blue sky"
        ],
        "action": "sailing on calm turquoise sea",
        "lighting_mood": "bright midday tropical sunshine",
        "evaluation_focus": "White sailboat with sails on calm turquoise water.",
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
        root_dir = os.path.dirname(os.path.abspath(__file__))
        root_json = os.path.join(root_dir, "challenges.json")
        if os.path.exists(root_json):
            load_candidates.append(root_json)
        if os.path.exists("challenges.json") and "challenges.json" not in load_candidates:
            load_candidates.append("challenges.json")
        if self.data_file:
            abs_data = os.path.join(root_dir, self.data_file) if not os.path.isabs(self.data_file) else self.data_file
            if os.path.exists(abs_data) and abs_data not in load_candidates:
                load_candidates.append(abs_data)
            elif os.path.exists(self.data_file) and self.data_file not in load_candidates:
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