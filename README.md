# BUILD THE FUTURE – AI Prompt Battle

> **"BUILD THE FUTURE – Imagine. Innovate. Create."**
> 
> Inspired by the **AWS Student Builder Groups** philosophy of empowering students to explore cloud technology, develop technical skills, collaborate, and build innovative solutions.
> 
> *An AI-powered creative challenge at AWS Community Day.*

---

## ⚡ Overview

**BUILD THE FUTURE** is an interactive, real-time AI Prompt Battle application built for hackathons, community events, and AWS Community Day. Every participant receives one randomly assigned creative challenge drawn from the active pool of the 8 frontier categories under the overarching theme: **BUILD THE FUTURE – Imagine. Innovate. Create.**

Participants craft descriptive generative prompts, synthesize futuristic digital art, receive immediate AI judge feedback, and submit their masterpieces to the community showcase and global leaderboard.

---

## 🌐 The 8 Official Challenge Categories

1. **Future of Education** – Biophilic campuses, quantum learning, neural knowledge cathedrals, and immersive pedagogical tech.
2. **Smart Cities and Sustainable Living** – Zero-carbon solarpunk archipelagos, vertical oxygen forest spires, clean transit, and circular ecology.
3. **Artificial Intelligence and Humanity** – Symbiotic creative ateliers, planetary climate guardians, and collaborative human-AI co-creation.
4. **Space Exploration and Future Civilizations** – Martian canyon habitats, Europa abyssal research outposts, and terraforming civilizational hubs.
5. **Technology for Social Impact** – Atmospheric desert water harvesters, autonomous hydrofoil healthcare clinics, and community empowerment.
6. **Future of Work** – Volumetric telepresence maker commons, bionic craft workshops, and borderless student collaboration.
7. **Cloud-Powered Innovation** – Serverless planetary mesh grids, real-time digital twins of renewable grids, and edge compute.
8. **Robotics and Automation** – Biomimetic coral restoration swarms, alpine disaster response mechs, and autonomous guardians.

---

## 🎯 Key Features & Rules

- **Overarching Theme**: All participants compete under the same official theme: `BUILD THE FUTURE – Imagine. Innovate. Create.`
- **Randomized Challenge Assignment**: Each builder is randomly assigned an active challenge from the 8 categories upon joining, with a re-roll capability.
- **AI Evaluation Engine**: Evaluates submissions specifically against the assigned challenge across 4 standardized pillars:
  - **Thematic Relevance & Challenge Alignment** (25 pts)
  - **Creativity & Originality / Imagination** (25 pts)
  - **Prompt Engineering & Technical Quality** (25 pts)
  - **Visual & Future Impact / Builder Ethos** (25 pts)
  - **Total**: 100 points with consistent scoring standards across all categories.
- **Multi-Tier Resilient Image Generation**:
  - **Tier 1**: NVIDIA NIM API (`black-forest-labs/flux.1-dev`) using `NVIDIA_API_KEY`.
  - **Tier 2**: High-speed Cloud Generative AI (Pollinations AI) fallback.
  - **Tier 3**: Offline Procedural Futuristic Synth (Pillow) fallback for zero-downtime reliability.
- **Admin Command Center**:
  - Add new challenges with category selection, vision brief, visual cues, and keywords.
  - Toggle challenges active/inactive in real time.
  - Delete or reset challenges to official defaults.
  - Competition phase controls: Lobby, Active Battle Round (with timer countdown), Showcase & Voting, and Final Leaderboard.
  - Protected by admin access code (`builder2026`).
- **Community Battle Showcase & Peer Voting**: Real-time gallery with one-click applause voting.
- **Leaderboard**: Real-time rankings filterable by overall score or individual category.
- **Compliance**: Respects community guidelines — no official AWS logos or unauthorized endorsements.

---

## 🚀 Quick Start Guide

### 1. Installation

A dedicated virtual environment is already configured in `.venv`:

```bash
# If running for the first time:
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)

The `.env` file contains:

```env
# NVIDIA NIM API (Flux.1-dev)
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_MODEL=black-forest-labs/flux.1-dev

# Admin Authentication Code
ADMIN_CODE=builder2026

# Competition Settings
ROUND_DURATION_SECONDS=300
PORT=8000
```

### 3. Launch the Application

Run the server with Python:

```bash
.\.venv\Scripts\python app.py
```

Or on Linux/Mac:
```bash
python3 app.py
```

Open your browser to:
**http://localhost:8000**

---

## 🔒 Admin Controls

1. Click **Admin Console** in the top navigation.
2. Enter the Admin Code: `builder2026`.
3. You can now:
   - Create, edit, toggle, and delete challenges across the 8 categories.
   - Switch competition phases (Lobby → Start Battle → Showcase → Leaderboard).
   - Adjust round duration and reset scores.

