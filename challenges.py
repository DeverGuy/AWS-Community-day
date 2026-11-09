"""
Challenge Management for BUILD THE FUTURE - AI Prompt Battle
Official Categories:
- Future of Education
- Smart Cities and Sustainable Living
- Artificial Intelligence and Humanity
- Space Exploration and Future Civilizations
- Technology for Social Impact
- Future of Work
- Cloud-Powered Innovation
- Robotics and Automation
"""

import os
import json
import random
import uuid

OFFICIAL_CATEGORIES = [
    "Future of Education",
    "Smart Cities and Sustainable Living",
    "Artificial Intelligence and Humanity",
    "Space Exploration and Future Civilizations",
    "Technology for Social Impact",
    "Future of Work",
    "Cloud-Powered Innovation",
    "Robotics and Automation"
]

DEFAULT_CHALLENGES = [
    # 1. Future of Education
    {
        "id": "edu-biosphere-campus",
        "category": "Future of Education",
        "title": "The Biosphere Hyper-Campus 2050",
        "brief": "Envision an open-air, nature-integrated university campus where AI holographic mentors, floating interactive quantum diagrams, and collaborative student pods harmonize with a living botanical ecosystem. Show students exploring microscopic wonders or cosmic physics in real-time.",
        "visual_goals": "Bioluminescent flora, floating interactive volumetric projections, solar-canopy glass pavilions, collaborative student builder circles, ambient warm sunrise illumination.",
        "inspiration_keywords": ["Biophilic Architecture", "Volumetric Holograms", "Quantum Visualizations", "Solar Domes", "Collaborative Discovery"],
        "evaluation_focus": "Integration of biological nature with advanced pedagogical tech; student collaboration atmosphere; visual clarity of learning tools.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "edu-neural-library",
        "category": "Future of Education",
        "title": "The Infinite Neural Archive",
        "brief": "Design the futuristic reincarnation of the Library of Alexandria: an ethereal knowledge cathedral where students walk through visualized historical eras, touch streams of human thought rendered as glowing starlight nebulae, and co-create new scientific models.",
        "visual_goals": "Towering crystalline archives, streams of data particles like floating golden dust, students walking inside holographic simulations of ancient and future worlds, soft ethereal lighting.",
        "inspiration_keywords": ["Infinite Knowledge Cathedral", "Data Nebulae", "Time-Travel Learning", "Crystalline Data Shards", "Deep Immersion"],
        "evaluation_focus": "Evocative scale of knowledge architecture; poetic balance of scholarship and futuristic vision.",
        "is_active": True,
        "created_by": "system"
    },

    # 2. Smart Cities and Sustainable Living
    {
        "id": "smart-floating-megacity",
        "category": "Smart Cities and Sustainable Living",
        "title": "Oceanic Solarpunk Archipelago",
        "brief": "Imagine a zero-carbon, floating city floating on coastal waters. Powered by wave kinetic energy and transparent solar towers, the city features vertical permaculture gardens, drone-tended kelp forests, and clean magnetic pod transit across turquoise reefs.",
        "visual_goals": "Terraced vertical gardens cascading into pristine ocean waters, transparent spiraling solar towers, silent maglev tube bridges, glowing underwater biosensors, vibrant solarpunk color palette.",
        "inspiration_keywords": ["Solarpunk", "Floating Eco-Metropolis", "Kelp Carbon Sinks", "Wave Kinetic Dynamos", "Clean Maglev Pods"],
        "evaluation_focus": "Harmony between oceanic ecosystem and urban engineering; believable renewable energy motifs; rich environmental details.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "smart-vertical-forest-city",
        "category": "Smart Cities and Sustainable Living",
        "title": "Hyper-Vertical Oxygen Spire",
        "brief": "Visualize a kilometer-tall eco-skyscraper designed to purify urban air. The exterior is wrapped in millions of genetic air-scrubbing ferns and mist cascades, connected by skybridges with autonomous electric sky-trams gliding between misty cloud layers.",
        "visual_goals": "Massive biophilic tower rising through low clouds, cascading waterfall air purifiers, luminous skybridge walkways, airborne pollinator drones, atmospheric sunset glow.",
        "inspiration_keywords": ["Hyper-Tower", "Cascading Water Mists", "Urban Reforestation", "Skybridges", "Clean Atmospheric Glow"],
        "evaluation_focus": "Grand sense of architectural verticality; vivid texture of living vegetation integrated into engineering structures.",
        "is_active": True,
        "created_by": "system"
    },

    # 3. Artificial Intelligence and Humanity
    {
        "id": "ai-symbiotic-atelier",
        "category": "Artificial Intelligence and Humanity",
        "title": "The Symbiotic Art & Code Atelier",
        "brief": "Portray a creative studio where a human builder and an ambient, light-woven sentient AI co-sculpt an impossible four-dimensional sculpture. The boundary between human intuition and machine intelligence blurs into a shared dance of sparks, thought-forms, and creative harmony.",
        "visual_goals": "Flowing streams of neural thought ribbons connecting human hands to glowing AI entities, kinetic light sculptures, warm tactile wooden workspace contrasted with digital lattices, studio lighting.",
        "inspiration_keywords": ["Symbiotic Creation", "Neural Light-Weaving", "Human-AI Partnership", "Kinetic Sculpture", "Warm Studio Ambient"],
        "evaluation_focus": "Emotional warmth and mutual respect in human-AI collaboration; visual representation of non-threatening, collaborative intelligence.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "ai-planetary-guardian",
        "category": "Artificial Intelligence and Humanity",
        "title": "The Earth Monitoring Synthesis Center",
        "brief": "Depict a global sanctuary where Indigenous ecologists and planetary AI models analyze living Earth telemetry: real-time climate pulses, migratory bird paths, and tectonic shifts visualized on an enormous liquid-light planetary globe.",
        "visual_goals": "Giant levitating holographic Earth pulsing with living climate data, diverse researchers interacting with fluid light gestures, serene high-tech glass sanctuary overlooking a protected wilderness valley.",
        "inspiration_keywords": ["Planetary AI", "Ecological Stewardship", "Liquid-Light Globe", "Climate Telemetry", "Wisdom & Tech Unity"],
        "evaluation_focus": "Sublime balance of technical planetary data and earth reverence; sense of stewardship rather than domination.",
        "is_active": True,
        "created_by": "system"
    },

    # 4. Space Exploration and Future Civilizations
    {
        "id": "space-martian-canyon-habitat",
        "category": "Space Exploration and Future Civilizations",
        "title": "The Terraforming Citadel of Valles Marineris",
        "brief": "Design a permanent human civilization hub carved into the rust-red canyon walls of Mars. Massive pressurized geodesic canyon roof shields a thriving interior forest, while atmospheric ozone towers shoot blue ionization beams into the Martian night sky.",
        "visual_goals": "Dramatic contrast between red Martian canyon cliffs and lush green pressurized biomes inside, soaring ionization laser beams, twin moons Phobos and Deimos visible, industrial rover tracks, cinematic wide angle.",
        "inspiration_keywords": ["Martian Habitat", "Valles Marineris", "Geodesic Canyon Canopy", "Terraforming Beams", "Cosmic Frontier"],
        "evaluation_focus": "Epic scale; geological realism of Mars merged with human architectural ingenuity; lighting contrasts.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "space-europa-subsurface-outpost",
        "category": "Space Exploration and Future Civilizations",
        "title": "Europa Sub-Oceanic Research Haven",
        "brief": "Envision an expedition outpost anchored beneath the kilometers-thick ice shell of Jupiter's moon Europa. Thermal siphon engines illuminate alien hydro-thermal vent ecosystems where bioluminescent deep-sea life drifts past geodesic observation spheres.",
        "visual_goals": "Deep abyssal teal and sapphire hues, glowing golden geothermal chimneys, submersible drones with high-beam projectors, towering overhead ice ceilings with luminous stress fractures.",
        "inspiration_keywords": ["Europa Abyss", "Subsurface Ocean", "Bioluminescent Vent Life", "Submersible Explorers", "Ice Canopy Fractures"],
        "evaluation_focus": "Underwater extraterrestrial mood; convincing hydrostatic pressure design language; striking color contrast.",
        "is_active": True,
        "created_by": "system"
    },

    # 5. Technology for Social Impact
    {
        "id": "impact-solar-water-restoration",
        "category": "Technology for Social Impact",
        "title": "The Atmospheric Water & Bloom Harvester",
        "brief": "Showcase a breakthrough distributed water generation station in an arid desert community. Sculptural solar-powered condensation petals draw water directly from morning desert air, irrigating community orchards and providing clean drinkable mineral water to cheering villagers.",
        "visual_goals": "Graceful petal-shaped condensing structures glistening with dew drops, thriving desert permaculture gardens, radiant smiling community members harvesting fresh crops, golden desert hour light.",
        "inspiration_keywords": ["Atmospheric Water Generation", "Clean Water Justice", "Desert Greening", "Community Empowerment", "Golden Hour Hope"],
        "evaluation_focus": "Human dignity and community triumph; elegant design of humanitarian technology; warm emotional storytelling.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "impact-remote-mobile-clinic",
        "category": "Technology for Social Impact",
        "title": "Autonomous Healthcare Pods for Island Communities",
        "brief": "Depict solar-electric hydrofoil clinic vessels arriving at remote archipelago shores, deploying AI diagnostic pods and surgical 3D printers that deliver world-class medical care and vaccines to underserved coastal families.",
        "visual_goals": "Futuristic white-and-teal medical catamaran gliding over emerald shallows, deployable solar medical canopy on white sand beach, children and elders welcoming healthcare workers, lens flare, pristine natural environment.",
        "inspiration_keywords": ["Solar Hydrofoil Clinic", "Telemedicine Pods", "Global Health Equity", "Emerald Lagoon", "Healing Technology"],
        "evaluation_focus": "Clear humanitarian utility; compassionate interaction between technology and underserved populations.",
        "is_active": True,
        "created_by": "system"
    },

    # 6. Future of Work
    {
        "id": "work-holographic-cloud-collective",
        "category": "Future of Work",
        "title": "The Distributed Cloud Maker Commons",
        "brief": "Visualize the workplace of 2040: a borderless collective of engineers, designers, and artisans collaborating in a hyper-flexible open space. Team members from five continents appear as life-sized photorealistic light holograms, assembling complex clean-energy turbine prototypes in shared space.",
        "visual_goals": "Luminous life-sized volumetric telepresence colleagues, exploding 3D schematic blueprints of clean machinery, ergonomic bamboo modular desks, panoramic view of a mountain valley outside floor-to-ceiling windows.",
        "inspiration_keywords": ["Volumetric Telepresence", "Global Collaboration", "Exploded CAD Hologram", "Ergonomic Eco-Office", "Borderless Teamwork"],
        "evaluation_focus": "Seamless collaboration across physical and virtual realities; realistic future work tools; positive human work-life balance.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "work-bionic-craftsman",
        "category": "Future of Work",
        "title": "The Bionic Master Builder Workshop",
        "brief": "Portray a master craftsperson wearing lightweight neural-assisted bionic gauntlets, hand-carving next-generation composite structures with nanometer precision. The workshop blends traditional woodworking tools with micro-plasma cutters and hovering drafting drones.",
        "visual_goals": "Fine sawdust and glowing plasma sparks illuminated by focused workbench lamps, intricate carbon-fiber and reclaimed timber textures, neural haptic interface glowing on builder's arm, deep artisanal focus.",
        "inspiration_keywords": ["Bionic Craftsmanship", "Neural Haptics", "Micro-Plasma Carving", "Artisan Meets Tech", "Intense Focus"],
        "evaluation_focus": "Dignity of physical craftsmanship augmented rather than replaced by tech; rich tactile texture and lighting.",
        "is_active": True,
        "created_by": "system"
    },

    # 7. Cloud-Powered Innovation
    {
        "id": "cloud-planetary-nervous-system",
        "category": "Cloud-Powered Innovation",
        "title": "The Serverless Planetary Pulse",
        "brief": "Create an artistic visualization of the global cloud infrastructure operating at sub-millisecond edge latency: underwater fiber cables pulsing with emerald light across oceanic trenches, satellite constellation mesh networks twinkling in orbit, and serverless edge data nodes powered by geothermal geysers.",
        "visual_goals": "View from low Earth orbit showing illuminated global neural network data grid, fiber optic pulses rippling through deep blue oceans, orbital relay satellites, vibrant data stream ribbons, cinematic space photography style.",
        "inspiration_keywords": ["Planetary Mesh Grid", "Subsea Light Fibers", "Geothermal Edge Compute", "Serverless Architecture", "Global Constellation"],
        "evaluation_focus": "Abstract yet visceral representation of cloud architecture; planetary scale; dynamic energy and flow.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "cloud-digital-twin-earth",
        "category": "Cloud-Powered Innovation",
        "title": "Real-Time Digital Twin Control Deck",
        "brief": "Depict a student developer command room orchestrating a cloud-native digital twin of a continent's renewable energy grid. Thousands of wind turbines, hydro dams, and smart battery storage nodes synchronize in real-time, preventing blackouts through predictive serverless algorithms.",
        "visual_goals": "Young builder teams standing around an interactive 3D illuminated topography table, graphs of real-time clean power flows, glowing blue-and-gold grid lines, focused collaborative energy, cutting-edge telemetry screens.",
        "inspiration_keywords": ["Digital Twin", "Renewable Grid Telemetry", "Predictive Cloud AI", "Student Builders", "Control Deck Hologram"],
        "evaluation_focus": "Builder mindset inspired by AWS Student Builders; tangible application of cloud compute to real-world infrastructure.",
        "is_active": True,
        "created_by": "system"
    },

    # 8. Robotics and Automation
    {
        "id": "robotics-autonomous-coral-reef-restorer",
        "category": "Robotics and Automation",
        "title": "Autonomous Bio-Reef Restoration Swarm",
        "brief": "Envision an underwater fleet of autonomous biomimetic manta-ray robots carefully 3D-printing calcium carbonate reef foundations and planting resilient coral larvae in bleaching marine zones, bringing back vibrant aquatic life.",
        "visual_goals": "Graceful robotic manta drones with glowing turquoise sonar sensors, micro-manipulator arms delicately placing baby coral polyps, curious schools of tropical reef fish swimming alongside, dappled underwater sunlight.",
        "inspiration_keywords": ["Biomimetic Robotics", "Coral Restoration", "Underwater Swarm", "Turquoise Sonar", "Marine Regeneration"],
        "evaluation_focus": "Robotics in service of ecological healing; biomimetic grace; rich marine lighting and texture.",
        "is_active": True,
        "created_by": "system"
    },
    {
        "id": "robotics-search-rescue-exosuit",
        "category": "Robotics and Automation",
        "title": "Disaster Response Aerial Rescue Mech",
        "brief": "Design a quadruped and biped transformable rescue robot navigating a mountain landslide zone in severe weather. The robotic guardian extends a protective thermo-insulated medical shelter while deploying micro-drone swarms to locate survivors.",
        "visual_goals": "Rugged all-weather carbon-fiber robotic rescue chassis, piercing searchlight beams through stormy rain, deployable micro-drones buzzing like glowing fireflies, heroic posture, rescue team operator observing via telemetry.",
        "inspiration_keywords": ["Search & Rescue Mech", "Micro-Drone Swarm", "Rugged Autonomous Chassis", "Heroic Shield", "Stormy Alpine Drama"],
        "evaluation_focus": "Functional engineering believability; dramatic weather and light contrast; protective, heroic narrative.",
        "is_active": True,
        "created_by": "system"
    }
]

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "challenges.json")

class ChallengeManager:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.challenges = []
        self._load()

    def _load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.challenges = json.load(f)
                    return
            except Exception as e:
                print(f"[ChallengeManager] Error loading {self.data_file}: {e}")
        # Default fallback
        self.challenges = [dict(c) for c in DEFAULT_CHALLENGES]
        self._save()

    def _save(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.challenges, f, indent=2)
        except Exception as e:
            print(f"[ChallengeManager] Error saving {self.data_file}: {e}")

    def get_categories(self):
        return list(OFFICIAL_CATEGORIES)

    def get_all_challenges(self):
        return list(self.challenges)

    def get_active_challenges(self, category=None):
        active = [c for c in self.challenges if c.get("is_active", True)]
        if category:
            active = [c for c in active if c.get("category") == category]
        return active

    def get_challenge_by_id(self, challenge_id):
        for c in self.challenges:
            if c.get("id") == challenge_id:
                return c
        return None

    def get_random_challenge(self, category=None, exclude_ids=None):
        active = self.get_active_challenges(category=category)
        if exclude_ids:
            candidates = [c for c in active if c.get("id") not in exclude_ids]
            if candidates:
                return random.choice(candidates)
        if active:
            return random.choice(active)
        # If no active challenges in specified category, return any active challenge
        all_active = self.get_active_challenges()
        if all_active:
            return random.choice(all_active)
        # Fallback to default
        return random.choice(DEFAULT_CHALLENGES)

    def get_unique_target_challenge(self, participant_id: str = None, category: str = None, exclude_ids: list = None) -> dict:
        """
        Retrieves a challenge and generates a unique target reference image synthesized by the AI agent.
        Ensures each participant receives a unique visual challenge.
        """
        import time
        from image_generator import image_generator

        base_ch = self.get_random_challenge(category=category, exclude_ids=exclude_ids)
        target = dict(base_ch)

        # Ensure a distinct seed per user session
        user_seed = abs(hash(f"{participant_id or uuid.uuid4().hex}-{base_ch.get('id')}-{time.time()}")) % 999999
        target["seed"] = user_seed
        target["target_id"] = f"target-{uuid.uuid4().hex[:8]}"

        # Synthesize target image prompt
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
        if category not in OFFICIAL_CATEGORIES:
            # Allow custom category if needed, but official ones are preferred
            pass
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
            "evaluation_focus": evaluation_focus.strip() or f"Creative and futuristic interpretation of {category}.",
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

    def update_challenge(self, challenge_id, **kwargs):
        for c in self.challenges:
            if c.get("id") == challenge_id:
                for k, v in kwargs.items():
                    if k in ["title", "brief", "visual_goals", "category", "evaluation_focus", "is_active", "inspiration_keywords"]:
                        c[k] = v
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

