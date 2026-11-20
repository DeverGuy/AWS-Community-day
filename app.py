"""
BUILD THE FUTURE – Imagine. Innovate. Create.
AI Prompt Battle Web Application
Inspired by the AWS Student Builder Groups philosophy
"""

import os
import time
import json
import uuid
import gzip
import base64
from datetime import datetime
import tempfile
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, Response, redirect
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

# Load environment variables
load_dotenv()

from challenges import challenge_manager, OFFICIAL_CATEGORIES
from evaluation import ai_evaluator, validate_prompt_anti_cheat
from image_generator import image_generator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400
CORS(app)

class VercelPathFixMiddleware:
    """Normalizes PATH_INFO for Vercel serverless environments when rewrites route to /app.py."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched = (
            environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_ORIGINAL_URI")
            or environ.get("HTTP_X_FORWARDED_URI")
        )
        if matched:
            matched_path = matched.split("?")[0]
            if matched_path and matched_path != "/app.py":
                environ["PATH_INFO"] = matched_path
        elif environ.get("PATH_INFO", "").startswith("/app.py"):
            rest = environ["PATH_INFO"][len("/app.py"):]
            environ["PATH_INFO"] = rest if rest else "/"
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)

@app.after_request
def optimize_http_response(response):
    """Adds aggressive browser caching headers and high-performance gzip compression."""
    # Static assets: cache in browser disk/memory cache for 24h
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=604800"
    elif request.path == "/" or request.path.startswith("/api/"):
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-cache"

    # Compress textual and JSON payloads on-the-fly with gzip
    accept_encoding = request.headers.get("Accept-Encoding", "")
    if (
        "gzip" in accept_encoding
        and response.status_code < 300
        and response.mimetype in ["text/html", "text/css", "application/javascript", "text/javascript", "application/json", "image/svg+xml"]
        and "Content-Encoding" not in response.headers
    ):
        try:
            if response.direct_passthrough:
                response.direct_passthrough = False
            data = response.get_data()
            if len(data) > 400:
                compressed = gzip.compress(data, compresslevel=5)
                response.set_data(compressed)
                response.headers["Content-Encoding"] = "gzip"
                response.headers["Content-Length"] = len(compressed)
                response.headers["Vary"] = "Accept-Encoding"
        except Exception:
            pass

    return response

# Use threading mode for Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

ADMIN_CODE = os.getenv('ADMIN_CODE', 'builder2026')
ROUND_DURATION = int(os.getenv('ROUND_DURATION_SECONDS', 180))
CHALLENGE_TIMER_SECONDS = int(os.getenv('CHALLENGE_TIMER_SECONDS', 180))

# Competition Global State
competition_state = {
    "status": "lobby",  # lobby, battle, leaderboard
    "round_number": 1,
    "round_duration": ROUND_DURATION,
    "round_start_time": None,
    "round_end_time": None,
    "theme": "BUILD THE FUTURE – Imagine. Innovate. Create.",
    "subtitle": "An AI-powered creative challenge at AWS Community Day.",
    "philosophy": "Inspired by the AWS Student Builder Groups philosophy of empowering students to explore cloud technology, develop technical skills, collaborate, and build innovative solutions."
}

# In-memory storage for active session with serverless-safe local persistence
participants = {}    # participant_id -> dict
socket_to_id = {}    # socket_id -> participant_id
submissions = {}     # submission_id -> dict

STATE_FILE = os.path.join(tempfile.gettempdir() if os.environ.get("VERCEL") else "data", "competition_runtime_state.json")

def _save_runtime_state():
    try:
        dir_name = os.path.dirname(STATE_FILE)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        ser_participants = {}
        for pid, p in participants.items():
            cp = dict(p)
            if "seen_challenges" in cp and isinstance(cp["seen_challenges"], set):
                cp["seen_challenges"] = list(cp["seen_challenges"])
            ser_participants[pid] = cp
        payload = {
            "competition_state": competition_state,
            "participants": ser_participants,
            "submissions": submissions
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception as e:
        print(f"[RuntimeState] Save error: {e}")

def _load_runtime_state():
    if not os.path.exists(STATE_FILE):
        return
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "competition_state" in data:
            competition_state.update(data["competition_state"])
        if "participants" in data:
            for pid, p in data["participants"].items():
                if "seen_challenges" in p and isinstance(p["seen_challenges"], list):
                    p["seen_challenges"] = set(p["seen_challenges"])
                participants[pid] = p
        if "submissions" in data:
            submissions.update(data["submissions"])
    except Exception as e:
        print(f"[RuntimeState] Load error: {e}")

_load_runtime_state()

def get_time_remaining():
    if competition_state["status"] != "battle" or not competition_state["round_start_time"]:
        return competition_state["round_duration"]
    elapsed = time.time() - competition_state["round_start_time"]
    remaining = max(0, int(competition_state["round_duration"] - elapsed))
    return remaining

def broadcast_state():
    """Broadcast public state to all connected clients and persist runtime state"""
    _save_runtime_state()
    state_payload = {
        "status": competition_state["status"],
        "round_number": competition_state["round_number"],
        "round_duration": competition_state["round_duration"],
        "time_remaining": get_time_remaining(),
        "participant_count": len(participants),
        "submission_count": len(submissions),
        "theme": competition_state["theme"],
        "subtitle": competition_state["subtitle"],
        "philosophy": competition_state["philosophy"]
    }
    socketio.emit("state_update", state_payload)

# -----------------------------------------------------------------------------
# WEB ROUTES
# -----------------------------------------------------------------------------

@app.route("/")
@app.route("/app.py")
def index():
    return render_template(
        "index.html",
        theme=competition_state["theme"],
        subtitle=competition_state["subtitle"],
        philosophy=competition_state["philosophy"],
        categories=OFFICIAL_CATEGORIES,
        open_admin=False
    )

@app.route("/admin")
@app.route("/admin/")
@app.route("/app.py/admin")
def admin_page():
    return render_template(
        "index.html",
        theme=competition_state["theme"],
        subtitle=competition_state["subtitle"],
        philosophy=competition_state["philosophy"],
        categories=OFFICIAL_CATEGORIES,
        open_admin=True
    )

# -----------------------------------------------------------------------------
# REST APIS - STATE & PARTICIPANTS
# -----------------------------------------------------------------------------

@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify({
        **competition_state,
        "time_remaining": get_time_remaining(),
        "participant_count": len(participants),
        "submission_count": len(submissions)
    })

@app.route("/api/join", methods=["POST"])
def join_competition():
    data = request.get_json() or {}
    name = data.get("name", "").strip() or f"Builder-{uuid.uuid4().hex[:4].upper()}"
    email = data.get("email", "").strip().lower()
    participant_id = data.get("participant_id") or str(uuid.uuid4())

    # Generate or assign a unique target challenge from agents under "BUILD THE FUTURE"
    target_challenge = challenge_manager.get_unique_target_challenge(participant_id=participant_id)
    seen_set = set([target_challenge["id"]])

    now_ts = time.time()
    participant = {
        "id": participant_id,
        "name": name,
        "email": email,
        "joined_at": now_ts,
        "timer_started_at": now_ts,
        "timer_duration": CHALLENGE_TIMER_SECONDS,
        "has_generated": False,
        "assigned_challenge": target_challenge,
        "target_challenge": target_challenge,
        "seen_challenges": seen_set,
        "generations": [],
        "submission": None,
        "status": "ready"
    }
    participants[participant_id] = participant

    broadcast_state()

    # Public client target object (strips hidden_prompt to prevent cheating)
    client_target = {k: v for k, v in target_challenge.items() if k != "hidden_prompt"}
    client_participant = dict(participant)
    client_participant["seen_challenges"] = list(participant.get("seen_challenges", []))
    client_participant["assigned_challenge"] = client_target
    client_participant["target_challenge"] = client_target

    return jsonify({
        "success": True,
        "participant": client_participant,
        "challenge": client_target,
        "target_challenge": client_target,
        "timer_duration": CHALLENGE_TIMER_SECONDS,
        "state": competition_state
    })

@app.route("/api/participant/<participant_id>", methods=["GET"])
def get_participant(participant_id):
    participant = participants.get(participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404
    client_p = dict(participant)
    client_p["seen_challenges"] = list(client_p.get("seen_challenges", []))
    if "target_challenge" in client_p and client_p["target_challenge"]:
        client_p["target_challenge"] = {k: v for k, v in client_p["target_challenge"].items() if k != "hidden_prompt"}
    if "assigned_challenge" in client_p and client_p["assigned_challenge"]:
        client_p["assigned_challenge"] = {k: v for k, v in client_p["assigned_challenge"].items() if k != "hidden_prompt"}
    return jsonify(client_p)

@app.route("/api/reroll-challenge", methods=["POST"])
@app.route("/api/target-challenge/new", methods=["POST"])
def reroll_challenge():
    """Allow participant to receive another randomized unique target challenge generated by agents"""
    data = request.get_json() or {}
    participant_id = data.get("participant_id")
    category = data.get("category")

    participant = participants.get(participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    if participant.get("has_generated") or len(participant.get("generations", [])) >= 1:
        return jsonify({
            "success": False,
            "already_generated": True,
            "error": "Your target challenge is locked because you have already finalized your generation."
        }), 403

    current_id = participant.get("assigned_challenge", {}).get("id")
    seen_set = participant.setdefault("seen_challenges", set())
    if current_id:
        seen_set.add(current_id)

    new_target = challenge_manager.get_unique_target_challenge(
        participant_id=participant_id,
        category=category,
        exclude_ids=list(seen_set)
    )
    seen_set.add(new_target["id"])
    participant["assigned_challenge"] = new_target
    participant["target_challenge"] = new_target
    participant["timer_started_at"] = time.time()

    client_target = {k: v for k, v in new_target.items() if k != "hidden_prompt"}
    return jsonify({
        "success": True,
        "challenge": client_target,
        "target_challenge": client_target,
        "timer_duration": CHALLENGE_TIMER_SECONDS
    })

# -----------------------------------------------------------------------------
# REST APIS - GENERATION & DUAL-IMAGE AI EVALUATION
# -----------------------------------------------------------------------------

def _record_submission(participant, target_challenge, prompt, image_data, eval_result):
    """Stores or updates a participant's official scored submission on the leaderboard."""
    existing = participant.get("submission")
    submission_id = existing["id"] if existing else str(uuid.uuid4())
    target_image_data = target_challenge.get("image_data")
    client_target = {k: v for k, v in target_challenge.items() if k != "hidden_prompt"}

    submission = {
        "id": submission_id,
        "participant_id": participant["id"],
        "player_name": participant["name"],
        "player_email": participant.get("email", ""),
        "challenge": client_target,
        "target_image": target_image_data,
        "prompt": prompt,
        "image_data": image_data,
        "evaluation": eval_result,
        "ai_score": eval_result["total_score"],
        "tier": eval_result["tier"],
        "tier_badge": eval_result["tier_badge"],
        "special_badges": eval_result.get("special_badges", []),
        "unbiased_critique": eval_result.get("unbiased_critique", ""),
        "submitted_at": time.time()
    }

    submissions[submission_id] = submission
    participant["submission"] = submission
    participant["status"] = "submitted"
    _save_runtime_state()

    socketio.emit("new_submission", {
        "submission_id": submission_id,
        "player_name": participant["name"],
        "category": target_challenge.get("category", "Innovation"),
        "challenge_title": target_challenge.get("title", "Visual Challenge"),
        "ai_score": eval_result["total_score"],
        "tier_badge": eval_result["tier_badge"]
    })
    broadcast_state()
    return submission


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    participant_id = data.get("participant_id")
    prompt = data.get("prompt", "").strip()
    auto_triggered = bool(data.get("auto_triggered", False))

    participant = participants.get(participant_id)

    # Single-shot enforcement: each participant gets strictly ONE generation attempt
    if participant and (participant.get("has_generated") or len(participant.get("generations", [])) >= 1):
        return jsonify({
            "success": False,
            "already_generated": True,
            "locked": True,
            "error": "Only 1 generation attempt is allowed per participant. Your final image has already been generated."
        }), 403

    if not prompt:
        if auto_triggered and participant:
            participant["has_generated"] = True
            participant["status"] = "expired"
            return jsonify({
                "success": False,
                "time_expired_empty": True,
                "already_generated": True,
                "locked": True,
                "error": "Time expired (180s) with no prompt entered. Your attempt is now locked."
            }), 400
        return jsonify({"error": "Prompt cannot be empty"}), 400

    # Anti-cheat check: Reject meta-prompts like "generate an image like the one on screen"
    is_valid, cheat_err = validate_prompt_anti_cheat(prompt)
    if not is_valid:
        if auto_triggered and participant:
            participant["has_generated"] = True
            participant["status"] = "disqualified"
        return jsonify({
            "success": False,
            "is_cheating": True,
            "already_generated": bool(auto_triggered),
            "locked": bool(auto_triggered),
            "error": cheat_err
        }), 400

    target_challenge = None
    if participant:
        target_challenge = participant.get("target_challenge") or participant.get("assigned_challenge")
    if not target_challenge:
        challenge_id = data.get("challenge_id")
        target_challenge = challenge_manager.get_challenge_by_id(challenge_id) or challenge_manager.get_unique_target_challenge(participant_id=participant_id)

    category = target_challenge.get("category", "")
    challenge_title = target_challenge.get("title", "")
    target_image_data = target_challenge.get("image_data")

    # Generate Image for user prompt AS IT IS via Cloudflare Workers AI (saurav-z/free-image-generation-api)
    test_mock_img = data.get("_test_mock_image_data")
    if test_mock_img:
        gen_result = {"success": True, "image_data": test_mock_img}
    else:
        gen_result = image_generator.generate(prompt, category=category, challenge_title=challenge_title)

    if not gen_result.get("success"):
        if gen_result.get("quota_exceeded"):
            status_code = 429
        elif gen_result.get("auth_failed"):
            status_code = 401
        else:
            status_code = 503
        return jsonify({
            "success": False,
            "quota_exceeded": bool(gen_result.get("quota_exceeded")),
            "error": gen_result.get("error", "Cloudflare Worker image generation failed")
        }), status_code

    user_image_data = gen_result.get("image_data")

    # Unbiased AI Judge comparing BOTH pics: target_image vs user_image
    eval_result = ai_evaluator.evaluate_dual_images(
        target_image_data=target_image_data,
        user_image_data=user_image_data,
        user_prompt=prompt,
        target_meta=target_challenge,
        player_name=participant.get("name", "Builder") if participant else "Builder"
    )

    generation_record = {
        "id": str(uuid.uuid4()),
        "prompt": prompt,
        "image_data": user_image_data,
        "target_image": target_image_data,
        "source": gen_result.get("source"),
        "latency": gen_result.get("latency"),
        "evaluation": eval_result,
        "auto_triggered": auto_triggered,
        "created_at": time.time()
    }

    saved_submission = None
    if participant:
        participant["generations"].append(generation_record)
        participant["has_generated"] = True
        saved_submission = _record_submission(
            participant=participant,
            target_challenge=target_challenge,
            prompt=prompt,
            image_data=user_image_data,
            eval_result=eval_result
        )

    return jsonify({
        "success": True,
        "locked": True,
        "generation": generation_record,
        "submission": saved_submission
    })

@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    participant_id = data.get("participant_id")
    user_image_data = data.get("image_data")
    player_name = data.get("player_name", "Builder")

    participant = participants.get(participant_id)
    target_challenge = None
    if participant:
        target_challenge = participant.get("target_challenge") or participant.get("assigned_challenge")
    if not target_challenge:
        target_challenge = challenge_manager.get_unique_target_challenge(participant_id=participant_id)

    target_image_data = target_challenge.get("image_data")

    eval_result = ai_evaluator.evaluate_dual_images(
        target_image_data=target_image_data,
        user_image_data=user_image_data,
        user_prompt=prompt,
        target_meta=target_challenge,
        player_name=player_name
    )
    return jsonify({
        "success": True,
        "evaluation": eval_result
    })

@app.route("/api/submit", methods=["POST"])
def submit_masterpiece():
    """Lock in final masterpiece submission for the AI battle"""
    data = request.get_json() or {}
    participant_id = data.get("participant_id")
    prompt = data.get("prompt", "").strip()
    image_data = data.get("image_data")

    participant = participants.get(participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404

    # If already finalized & auto-submitted on single-shot generation, return it directly
    if participant.get("submission"):
        return jsonify({
            "success": True,
            "submission": participant["submission"]
        })

    target_challenge = participant.get("target_challenge") or participant.get("assigned_challenge")
    if not target_challenge:
        return jsonify({"error": "No target challenge assigned"}), 400

    if not prompt or not image_data:
        return jsonify({"error": "Both prompt and generated image are required to submit"}), 400

    target_image_data = target_challenge.get("image_data")

    # Final definitive AI evaluation comparing both images
    eval_result = ai_evaluator.evaluate_dual_images(
        target_image_data=target_image_data,
        user_image_data=image_data,
        user_prompt=prompt,
        target_meta=target_challenge,
        player_name=participant["name"]
    )

    submission = _record_submission(
        participant=participant,
        target_challenge=target_challenge,
        prompt=prompt,
        image_data=image_data,
        eval_result=eval_result
    )

    return jsonify({
        "success": True,
        "submission": submission
    })

# -----------------------------------------------------------------------------
# REST APIS - LEADERBOARD & SUBMISSIONS
# -----------------------------------------------------------------------------

@app.route("/api/submissions", methods=["GET"])
def get_submissions():
    category = request.args.get("category")
    items = list(submissions.values())
    if category:
        items = [s for s in items if s.get("challenge", {}).get("category") == category]
    # Sort by AI score
    items.sort(key=lambda s: s.get("ai_score", 0), reverse=True)
    return jsonify(items)

@app.route("/api/vote", methods=["POST"])
def vote():
    # Voting disabled per event specifications
    return jsonify({
        "success": True,
        "message": "Voting has been disabled for this competition",
        "votes": 0
    })

@app.route("/api/submission/<submission_id>/image", methods=["GET"])
def get_submission_image(submission_id):
    """Serves high-performance cached binary image for leaderboard replicas instead of sending massive base64 JSON."""
    sub = submissions.get(submission_id)
    if not sub or not sub.get("image_data"):
        return ("Image not found", 404)
    img_raw = sub["image_data"]
    if isinstance(img_raw, str) and img_raw.startswith("data:image/"):
        try:
            header, b64_str = img_raw.split(",", 1)
            mime = header.split(";")[0].replace("data:", "")
            binary = base64.b64decode(b64_str)
            resp = Response(binary, mimetype=mime)
            resp.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=604800"
            return resp
        except Exception:
            return redirect(img_raw)
    return redirect(img_raw)

@app.route("/api/submission/<submission_id>/target", methods=["GET"])
def get_submission_target_image(submission_id):
    """Serves high-performance cached binary image for target reference scenes."""
    sub = submissions.get(submission_id)
    if not sub:
        return ("Submission not found", 404)
    target_raw = sub.get("target_image") or sub.get("challenge", {}).get("image_data")
    if not target_raw:
        return ("Target image not found", 404)
    if isinstance(target_raw, str) and target_raw.startswith("data:image/"):
        try:
            header, b64_str = target_raw.split(",", 1)
            mime = header.split(";")[0].replace("data:", "")
            binary = base64.b64decode(b64_str)
            resp = Response(binary, mimetype=mime)
            resp.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=604800"
            return resp
        except Exception:
            return redirect(target_raw)
    return redirect(target_raw)

@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    category = request.args.get("category")
    include_full = request.args.get("full") == "true"
    board = []

    for s in submissions.values():
        if category and s.get("challenge", {}).get("category") != category:
            continue

        ai_score = s.get("ai_score", 0)
        composite_score = round(ai_score, 1)

        target_img = (s.get("target_image") or s.get("challenge", {}).get("image_data")) if include_full else f"/api/submission/{s['id']}/target"
        user_img = s["image_data"] if include_full else f"/api/submission/{s['id']}/image"

        board.append({
            "id": s["id"],
            "participant_id": s["participant_id"],
            "player_name": s["player_name"],
            "player_email": s.get("player_email", ""),
            "category": s.get("challenge", {}).get("category"),
            "challenge_title": s.get("challenge", {}).get("title"),
            "prompt": s["prompt"],
            "target_image": target_img,
            "image_data": user_img,
            "ai_score": ai_score,
            "votes": 0,
            "composite_score": composite_score,
            "tier": s.get("tier"),
            "tier_badge": s.get("tier_badge"),
            "special_badges": s.get("special_badges", []),
            "unbiased_critique": s.get("unbiased_critique") or s.get("evaluation", {}).get("unbiased_critique", ""),
            "evaluation_breakdown": s.get("evaluation", {}).get("breakdown", {})
        })

    # Sort descending by composite score
    board.sort(key=lambda x: x["composite_score"], reverse=True)

    # Assign rank
    for rank, entry in enumerate(board, start=1):
        entry["rank"] = rank

    return jsonify({
        "theme": competition_state["theme"],
        "category_filter": category or "All Categories",
        "leaderboard": board
    })

# -----------------------------------------------------------------------------
# REST APIS - CHALLENGE MANAGEMENT (ADMIN)
# -----------------------------------------------------------------------------

def verify_admin(req):
    auth_header = req.headers.get("X-Admin-Code")
    if auth_header and auth_header == ADMIN_CODE:
        return True
    if req.is_json:
        data = req.get_json(silent=True) or {}
        if data.get("admin_code") == ADMIN_CODE:
            return True
    return False

@app.route("/api/admin/auth", methods=["POST"])
def auth_admin():
    data = request.get_json() or {}
    code = data.get("admin_code", "").strip()
    if code == ADMIN_CODE:
        return jsonify({"success": True, "message": "Admin authenticated"})
    return jsonify({"success": False, "error": "Invalid admin access code"}), 401

@app.route("/api/challenges", methods=["GET"])
def list_challenges():
    category = request.args.get("category")
    active_only = request.args.get("active") == "true"
    if active_only:
        items = challenge_manager.get_active_challenges(category=category)
    else:
        items = challenge_manager.get_all_challenges()
        if category:
            items = [c for c in items if c.get("category") == category]
    return jsonify({
        "categories": OFFICIAL_CATEGORIES,
        "stats": challenge_manager.get_stats(),
        "challenges": items
    })

@app.route("/api/challenges/add", methods=["POST"])
def add_challenge():
    if not verify_admin(request):
        return jsonify({"error": "Admin authorization required"}), 403

    data = request.get_json() or {}
    category = data.get("category", "") or "General"
    title = data.get("title")
    brief = data.get("brief")
    visual_goals = data.get("visual_goals", "")
    inspiration_keywords = data.get("inspiration_keywords", "")
    evaluation_focus = data.get("evaluation_focus", "")
    is_active = data.get("is_active", True)
    image_data = data.get("image_data")

    if not title or not brief:
        return jsonify({"error": "Title and brief are required"}), 400

    new_item = challenge_manager.add_challenge(
        title=title,
        brief=brief,
        category=category,
        visual_goals=visual_goals,
        inspiration_keywords=inspiration_keywords,
        evaluation_focus=evaluation_focus,
        is_active=is_active,
        created_by="admin",
        image_data=image_data
    )

    socketio.emit("challenges_updated", {"action": "added", "challenge": new_item})
    return jsonify({"success": True, "challenge": new_item})

@app.route("/api/challenges/<challenge_id>/image", methods=["POST"])
def upload_challenge_image(challenge_id):
    if not verify_admin(request):
        return jsonify({"error": "Admin authorization required"}), 403

    image_data = None
    if "file" in request.files:
        file = request.files["file"]
        if file and file.filename:
            image_data = file.read()
    elif request.is_json:
        image_data = (request.get_json() or {}).get("image_data")

    if not image_data:
        return jsonify({"error": "No image data or file provided"}), 400

    static_url = challenge_manager.save_challenge_image(challenge_id, image_data)
    if not static_url:
        return jsonify({"error": "Failed to save image"}), 500

    socketio.emit("challenges_updated", {"action": "image_updated", "challenge_id": challenge_id, "static_url": static_url})
    return jsonify({"success": True, "static_url": static_url})

@app.route("/api/challenges/<challenge_id>/toggle", methods=["POST"])
def toggle_challenge(challenge_id):
    if not verify_admin(request):
        return jsonify({"error": "Admin authorization required"}), 403

    data = request.get_json() or {}
    is_active = data.get("is_active")  # True, False, or None to toggle

    updated = challenge_manager.toggle_challenge_active(challenge_id, is_active=is_active)
    if not updated:
        return jsonify({"error": "Challenge not found"}), 404

    socketio.emit("challenges_updated", {"action": "toggled", "challenge": updated})
    return jsonify({"success": True, "challenge": updated})

@app.route("/api/challenges/<challenge_id>", methods=["DELETE"])
def delete_challenge(challenge_id):
    if not verify_admin(request):
        return jsonify({"error": "Admin authorization required"}), 403

    removed = challenge_manager.remove_challenge(challenge_id)
    if not removed:
        return jsonify({"error": "Challenge not found"}), 404

    socketio.emit("challenges_updated", {"action": "deleted", "challenge_id": challenge_id})
    return jsonify({"success": True, "challenge_id": challenge_id})

@app.route("/api/challenges/reset", methods=["POST"])
def reset_challenges():
    if not verify_admin(request):
        return jsonify({"error": "Admin authorization required"}), 403

    defaults = challenge_manager.reset_to_defaults()
    socketio.emit("challenges_updated", {"action": "reset", "count": len(defaults)})
    return jsonify({"success": True, "count": len(defaults)})

@app.route("/api/challenges/stats", methods=["GET"])
def challenge_stats():
    return jsonify(challenge_manager.get_stats())

# -----------------------------------------------------------------------------
# REST APIS - COMPETITION PHASE CONTROL (ADMIN)
# -----------------------------------------------------------------------------

@app.route("/api/admin/phase", methods=["POST"])
def set_competition_phase():
    if not verify_admin(request):
        return jsonify({"error": "Admin authorization required"}), 403

    data = request.get_json() or {}
    new_phase = data.get("phase")
    duration = data.get("duration")

    if new_phase not in ["lobby", "battle", "leaderboard"]:
        return jsonify({"error": f"Invalid phase: {new_phase}. Allowed: lobby, battle, leaderboard"}), 400

    competition_state["status"] = new_phase

    if new_phase == "battle":
        competition_state["round_duration"] = int(duration) if duration else ROUND_DURATION
        competition_state["round_start_time"] = time.time()
        competition_state["round_end_time"] = competition_state["round_start_time"] + competition_state["round_duration"]
    else:
        competition_state["round_start_time"] = None
        competition_state["round_end_time"] = None

    state_payload = {
        **competition_state,
        "time_remaining": get_time_remaining(),
        "participant_count": len(participants),
        "submission_count": len(submissions)
    }

    broadcast_state()
    socketio.emit("phase_changed", {"phase": new_phase, "state": state_payload})
    return jsonify({"success": True, "state": state_payload})

@app.route("/api/admin/reset", methods=["POST"])
def reset_competition():
    """Reset the competition (clears participants, generations, and submissions)"""
    if not verify_admin(request):
        return jsonify({"error": "Admin authorization required"}), 403

    participants.clear()
    submissions.clear()
    competition_state["status"] = "lobby"
    competition_state["round_start_time"] = None
    competition_state["round_end_time"] = None
    competition_state["round_number"] = 1

    broadcast_state()
    socketio.emit("competition_reset", {"message": "Competition has been reset by administrator"})
    return jsonify({"success": True, "message": "Competition reset complete"})

# -----------------------------------------------------------------------------
# SOCKET.IO REAL-TIME EVENTS
# -----------------------------------------------------------------------------

@socketio.on("connect")
def handle_connect():
    sid = request.sid
    # Send current state immediately on connect
    emit("state_update", {
        "status": competition_state["status"],
        "round_number": competition_state["round_number"],
        "round_duration": competition_state["round_duration"],
        "time_remaining": get_time_remaining(),
        "participant_count": len(participants),
        "submission_count": len(submissions),
        "theme": competition_state["theme"],
        "subtitle": competition_state["subtitle"],
        "philosophy": competition_state["philosophy"]
    })

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    participant_id = socket_to_id.pop(sid, None)
    broadcast_state()

@socketio.on("register_client")
def handle_register(data):
    sid = request.sid
    participant_id = (data or {}).get("participant_id")
    if participant_id:
        socket_to_id[sid] = participant_id

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print("=" * 70)
    print("BUILD THE FUTURE – Imagine. Innovate. Create.")
    print("An AI-powered creative challenge at AWS Community Day.")
    print(f"Starting server on http://localhost:{port}")
    print("Admin Code:", ADMIN_CODE)
    print("=" * 70)
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
