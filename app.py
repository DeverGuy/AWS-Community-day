"""
BUILD THE FUTURE – Imagine. Innovate. Create.
AI Prompt Battle Web Application
Inspired by the AWS Student Builder Groups philosophy
"""

import os
import time
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

# Load environment variables
load_dotenv()

from challenges import challenge_manager, OFFICIAL_CATEGORIES
from evaluation import ai_evaluator, validate_prompt_anti_cheat
from image_generator import image_generator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
CORS(app)

# Use threading mode for Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

ADMIN_CODE = os.getenv('ADMIN_CODE', 'builder2026')
ROUND_DURATION = int(os.getenv('ROUND_DURATION_SECONDS', 300))

# Competition Global State
competition_state = {
    "status": "lobby",  # lobby, battle, showcase, leaderboard
    "round_number": 1,
    "round_duration": ROUND_DURATION,
    "round_start_time": None,
    "round_end_time": None,
    "theme": "BUILD THE FUTURE – Imagine. Innovate. Create.",
    "subtitle": "An AI-powered creative challenge at AWS Community Day.",
    "philosophy": "Inspired by the AWS Student Builder Groups philosophy of empowering students to explore cloud technology, develop technical skills, collaborate, and build innovative solutions."
}

# In-memory storage for active session
participants = {}    # participant_id -> dict
socket_to_id = {}    # socket_id -> participant_id
submissions = {}     # submission_id -> dict
votes = {}           # submission_id -> set of participant_ids

def get_time_remaining():
    if competition_state["status"] != "battle" or not competition_state["round_start_time"]:
        return competition_state["round_duration"]
    elapsed = time.time() - competition_state["round_start_time"]
    remaining = max(0, int(competition_state["round_duration"] - elapsed))
    return remaining

def broadcast_state():
    """Broadcast public state to all connected clients"""
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
def index():
    return render_template(
        "index.html",
        theme=competition_state["theme"],
        subtitle=competition_state["subtitle"],
        philosophy=competition_state["philosophy"],
        categories=OFFICIAL_CATEGORIES
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

    participant = {
        "id": participant_id,
        "name": name,
        "email": email,
        "joined_at": time.time(),
        "assigned_challenge": target_challenge,
        "target_challenge": target_challenge,
        "generations": [],
        "submission": None,
        "status": "ready"
    }
    participants[participant_id] = participant

    broadcast_state()

    # Public client target object (strips hidden_prompt to prevent cheating)
    client_target = {k: v for k, v in target_challenge.items() if k != "hidden_prompt"}
    client_participant = dict(participant)
    client_participant["assigned_challenge"] = client_target
    client_participant["target_challenge"] = client_target

    return jsonify({
        "success": True,
        "participant": client_participant,
        "challenge": client_target,
        "target_challenge": client_target,
        "state": competition_state
    })

@app.route("/api/participant/<participant_id>", methods=["GET"])
def get_participant(participant_id):
    participant = participants.get(participant_id)
    if not participant:
        return jsonify({"error": "Participant not found"}), 404
    client_p = dict(participant)
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

    current_id = participant.get("assigned_challenge", {}).get("id")
    new_target = challenge_manager.get_unique_target_challenge(
        participant_id=participant_id,
        category=category,
        exclude_ids=[current_id] if current_id else None
    )
    participant["assigned_challenge"] = new_target
    participant["target_challenge"] = new_target

    client_target = {k: v for k, v in new_target.items() if k != "hidden_prompt"}
    return jsonify({
        "success": True,
        "challenge": client_target,
        "target_challenge": client_target
    })

# -----------------------------------------------------------------------------
# REST APIS - GENERATION & DUAL-IMAGE AI EVALUATION
# -----------------------------------------------------------------------------

@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    participant_id = data.get("participant_id")
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    # Anti-cheat check: Reject meta-prompts like "generate an image like the one on screen"
    is_valid, cheat_err = validate_prompt_anti_cheat(prompt)
    if not is_valid:
        return jsonify({
            "success": False,
            "is_cheating": True,
            "error": cheat_err
        }), 400

    participant = participants.get(participant_id)
    target_challenge = None
    if participant:
        target_challenge = participant.get("target_challenge") or participant.get("assigned_challenge")
    if not target_challenge:
        challenge_id = data.get("challenge_id")
        target_challenge = challenge_manager.get_challenge_by_id(challenge_id) or challenge_manager.get_unique_target_challenge(participant_id=participant_id)

    category = target_challenge.get("category", "")
    challenge_title = target_challenge.get("title", "")
    target_image_data = target_challenge.get("image_data")

    # Generate Image for user prompt AS IT IS via multi-tier generator
    gen_result = image_generator.generate(prompt, category=category, challenge_title=challenge_title)

    if not gen_result.get("success"):
        if gen_result.get("rate_limited") and gen_result.get("client_url"):
            return jsonify({
                "success": False,
                "fallback_to_client": True,
                "client_url": gen_result.get("client_url"),
                "message": "Server IP limit reached. Direct client fetch initiated."
            }), 200
        return jsonify({
            "success": False,
            "error": gen_result.get("error", "Image generation failed")
        }), 500

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
        "created_at": time.time()
    }

    if participant:
        participant["generations"].append(generation_record)

    return jsonify({
        "success": True,
        "generation": generation_record
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

    submission_id = str(uuid.uuid4())
    client_target = {k: v for k, v in target_challenge.items() if k != "hidden_prompt"}
    submission = {
        "id": submission_id,
        "participant_id": participant_id,
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
        "votes": 0,
        "submitted_at": time.time()
    }

    submissions[submission_id] = submission
    participant["submission"] = submission
    participant["status"] = "submitted"
    votes[submission_id] = set()

    # Broadcast new submission to all clients
    socketio.emit("new_submission", {
        "submission_id": submission_id,
        "player_name": participant["name"],
        "category": target_challenge.get("category", "Innovation"),
        "challenge_title": target_challenge.get("title", "Visual Challenge"),
        "ai_score": eval_result["total_score"],
        "tier_badge": eval_result["tier_badge"]
    })
    broadcast_state()

    return jsonify({
        "success": True,
        "submission": submission
    })

# -----------------------------------------------------------------------------
# REST APIS - SHOWCASE, VOTING & LEADERBOARD
# -----------------------------------------------------------------------------

@app.route("/api/submissions", methods=["GET"])
def get_submissions():
    category = request.args.get("category")
    items = list(submissions.values())
    if category:
        items = [s for s in items if s.get("challenge", {}).get("category") == category]
    # Sort by total points (AI score + vote bonus)
    items.sort(key=lambda s: (s.get("ai_score", 0) + s.get("votes", 0) * 2), reverse=True)
    return jsonify(items)

@app.route("/api/vote", methods=["POST"])
def vote():
    data = request.get_json() or {}
    submission_id = data.get("submission_id")
    voter_id = data.get("voter_id", str(uuid.uuid4()))

    submission = submissions.get(submission_id)
    if not submission:
        return jsonify({"error": "Submission not found"}), 404

    # Prevent voting for one's own submission
    if submission.get("participant_id") == voter_id:
        return jsonify({"error": "You cannot vote for your own creation"}), 400

    voter_set = votes.setdefault(submission_id, set())
    if voter_id in voter_set:
        voter_set.remove(voter_id)
        action = "unvoted"
    else:
        voter_set.add(voter_id)
        action = "voted"

    submission["votes"] = len(voter_set)
    total_score = round(submission["ai_score"] + submission["votes"] * 2, 1)

    socketio.emit("vote_update", {
        "submission_id": submission_id,
        "votes": submission["votes"],
        "total_score": total_score
    })

    return jsonify({
        "success": True,
        "action": action,
        "votes": submission["votes"],
        "total_score": total_score
    })

@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    category = request.args.get("category")
    board = []

    for s in submissions.values():
        if category and s.get("challenge", {}).get("category") != category:
            continue

        ai_score = s.get("ai_score", 0)
        vote_count = s.get("votes", 0)
        composite_score = round(ai_score + (vote_count * 2.0), 1)

        board.append({
            "id": s["id"],
            "participant_id": s["participant_id"],
            "player_name": s["player_name"],
            "player_email": s.get("player_email", ""),
            "category": s.get("challenge", {}).get("category"),
            "challenge_title": s.get("challenge", {}).get("title"),
            "prompt": s["prompt"],
            "target_image": s.get("target_image") or s.get("challenge", {}).get("image_data"),
            "image_data": s["image_data"],
            "ai_score": ai_score,
            "votes": vote_count,
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
    category = data.get("category")
    title = data.get("title")
    brief = data.get("brief")
    visual_goals = data.get("visual_goals", "")
    inspiration_keywords = data.get("inspiration_keywords", "")
    evaluation_focus = data.get("evaluation_focus", "")
    is_active = data.get("is_active", True)

    if not category or not title or not brief:
        return jsonify({"error": "Category, title, and brief are required"}), 400

    if category not in OFFICIAL_CATEGORIES:
        return jsonify({"error": f"Category must be one of: {', '.join(OFFICIAL_CATEGORIES)}"}), 400

    new_item = challenge_manager.add_challenge(
        category=category,
        title=title,
        brief=brief,
        visual_goals=visual_goals,
        inspiration_keywords=inspiration_keywords,
        evaluation_focus=evaluation_focus,
        is_active=is_active,
        created_by="admin"
    )

    socketio.emit("challenges_updated", {"action": "added", "challenge": new_item})
    return jsonify({"success": True, "challenge": new_item})

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

    if new_phase not in ["lobby", "battle", "showcase", "leaderboard"]:
        return jsonify({"error": "Invalid phase"}), 400

    competition_state["status"] = new_phase

    if new_phase == "battle":
        competition_state["round_duration"] = int(duration) if duration else ROUND_DURATION
        competition_state["round_start_time"] = time.time()
        competition_state["round_end_time"] = competition_state["round_start_time"] + competition_state["round_duration"]
    elif new_phase == "lobby":
        competition_state["round_start_time"] = None
        competition_state["round_end_time"] = None

    broadcast_state()
    return jsonify({"success": True, "state": competition_state})

@app.route("/api/admin/reset", methods=["POST"])
def reset_competition():
    """Reset the competition (clears participants, generations, and submissions)"""
    if not verify_admin(request):
        return jsonify({"error": "Admin authorization required"}), 403

    participants.clear()
    submissions.clear()
    votes.clear()
    competition_state["status"] = "lobby"
    competition_state["round_start_time"] = None
    competition_state["round_end_time"] = None
    competition_state["round_number"] = 1

    broadcast_state()
    socketio.emit("competition_reset", {})
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
