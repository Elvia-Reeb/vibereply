"""
🕸️ THREADWISE BACKEND 🕸️
--------------------------
This turns Threadwise into a real "waiter" (a web server) that a website
or app can send requests to — same idea as the VibeReply backend.

Routes (doors) available:
  /                  -> simple "are you alive?" check
  /rank-prospects     -> get ALL prospects ranked by warmth (GET)
  /prospect/<name>    -> get warm path details for ONE prospect (GET)
  /write-opener       -> get an AI-written opener message for a prospect (POST)
"""

import os
import json
from datetime import date
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # 🔓 lets a webpage frontend talk to this backend safely

PRACTICE_MODE = True  # 🎈 Free testing mode — no API key needed

# -------------------------------------------------------------------
# 💾 SAVING REAL DATA — a "notebook" file, just like VibeReply
# -------------------------------------------------------------------
# Your REAL prospects get saved here so they don't disappear when the
# backend restarts. The pretend ones below are only used the very
# first time, before you've added any real ones.

PROSPECTS_FILE = "saved_prospects.json"


def load_prospects():
    if os.path.exists(PROSPECTS_FILE):
        with open(PROSPECTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # First time ever running — start with the pretend demo prospects
    return list(default_prospects)


def save_all_prospects(prospect_list):
    with open(PROSPECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(prospect_list, f, indent=2)


# -------------------------------------------------------------------
# 👤 YOUR BACKGROUND (pretend data for now)
# -------------------------------------------------------------------

my_background = {
    "past_companies": ["Acme Corp", "BrightBot AI", "Nova Systems"],
    "connections": {
        "Sarah Malik": {"last_talked": date(2026, 8, 20)},
        "James Cho": {"last_talked": date(2024, 3, 10)},
        "Fatima Noor": {"last_talked": date(2026, 7, 1)},
        "David Lee": {"last_talked": date(2023, 5, 15)},
    },
    "skills_you_offer": ["AI automation", "workflow automation", "review management tools"]
}


# -------------------------------------------------------------------
# 🎯 PRETEND PROSPECTS
# -------------------------------------------------------------------

default_prospects = [
    {
        "name": "Emma Whitfield",
        "company": "Lumen Analytics",
        "past_companies": ["Acme Corp", "Lumen Analytics"],
        "connections": ["Priya Shah", "Tom Reilly"],
        "recent_signal": "Posted about drowning in manual customer feedback review"
    },
    {
        "name": "Marcus Webb",
        "company": "Ironclad Systems",
        "past_companies": ["Orbit Media", "Ironclad Systems"],
        "connections": ["Sarah Malik", "Lena Ortiz"],
        "recent_signal": "Hiring for a role focused on internal workflow automation"
    },
    {
        "name": "Aisha Karim",
        "company": "Nimbus Cloud",
        "past_companies": ["Nova Systems", "Nimbus Cloud"],
        "connections": ["Fatima Noor", "Omar Siddiqui"],
        "recent_signal": "Mentioned team is overwhelmed replying to customer reviews"
    },
    {
        "name": "Chris Donovan",
        "company": "Vertex Retail",
        "past_companies": ["Vertex Retail"],
        "connections": ["George Kim", "Nina Patel"],
        "recent_signal": "No recent public activity found"
    },
    {
        "name": "Olivia Grant",
        "company": "Skyline Partners",
        "past_companies": ["Skyline Partners", "BrightBot AI"],
        "connections": ["David Lee", "Ravi Kumar"],
        "recent_signal": "Shared an article about scaling operations efficiently"
    },
]

# 📂 Load real saved prospects (or the pretend ones, the very first time)
prospects = load_prospects()


# -------------------------------------------------------------------
# 🔋 HELPER: how stale is a connection?
# -------------------------------------------------------------------

def months_since(past_date):
    today = date.today()
    return (today.year - past_date.year) * 12 + (today.month - past_date.month)


# -------------------------------------------------------------------
# 🧠 THE MATCHING ENGINE
# -------------------------------------------------------------------

def find_warm_path(prospect):
    shared_companies = list(
        set(my_background["past_companies"]) & set(prospect["past_companies"])
    )
    shared_connections = list(
        set(my_background["connections"].keys()) & set(prospect["connections"])
    )

    warmth_score = (len(shared_companies) * 2) + (len(shared_connections) * 3)

    reasons = []
    freshness_warning = None

    if shared_companies:
        reasons.append(f"you both worked at {', '.join(shared_companies)}")

    if shared_connections:
        reasons.append(f"you both know {', '.join(shared_connections)}")
        for name in shared_connections:
            months_ago = months_since(my_background["connections"][name]["last_talked"])
            if months_ago > 12:
                freshness_warning = (
                    f"⚠️ You haven't talked to {name} in {months_ago} months — "
                    f"reconnect with them first before using this path!"
                )
                warmth_score -= 2

    explanation = (
        "Warm path found: " + " and ".join(reasons) + "."
        if reasons else "No warm path found — this would be a cold outreach."
    )

    give_first_match = None
    for skill in my_background["skills_you_offer"]:
        if skill.lower() in prospect["recent_signal"].lower() or any(
            word in prospect["recent_signal"].lower() for word in skill.lower().split()
        ):
            give_first_match = (
                f"🎁 Give-first opportunity: they mentioned \"{prospect['recent_signal']}\" "
                f"— you could genuinely open by offering help with {skill}, instead of asking for anything."
            )
            break

    return {
        "name": prospect["name"],
        "company": prospect["company"],
        "warmth_score": warmth_score,
        "explanation": explanation,
        "freshness_warning": freshness_warning,
        "give_first_match": give_first_match
    }


# -------------------------------------------------------------------
# ✍️ AI OPENER WRITER (with Mode Selector)
# -------------------------------------------------------------------

MODE_INSTRUCTIONS = {
    "lead_gen": "The goal is to offer genuine help/value related to their situation, not to sell aggressively.",
    "job_referral": "The goal is to ask warmly for a quick chat or referral regarding opportunities at their company.",
    "recruiting": "The goal is to gauge interest in a role you're hiring for, in a low-pressure way.",
    "partnership": "The goal is to propose exploring a potential collaboration between you two."
}


def write_opener_message(prospect, mode="lead_gen"):
    warm_path = find_warm_path(prospect)

    if PRACTICE_MODE:
        opener = f"Hi {prospect['name']}, "
        if warm_path["give_first_match"]:
            opener += (
                f"I noticed you mentioned \"{prospect['recent_signal']}\" — "
                f"I've actually built tools in that exact space and would love to share some thoughts, no strings attached. "
            )
        elif "worked at" in warm_path["explanation"]:
            opener += "I saw we're both connected through our time in similar circles — small world! "
        else:
            opener += "I came across your profile and wanted to reach out. "

        if mode == "job_referral":
            opener += "I'm exploring opportunities and would love a quick chat if you're open to it."
        elif mode == "recruiting":
            opener += "I'm working on a role I think you could be a great fit for, open to a quick chat?"
        elif mode == "partnership":
            opener += "I think there could be a great opportunity for us to collaborate."
        else:
            opener += "Happy to share more if it's useful!"

        return opener + " (this is a PRACTICE MODE pretend message)"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "⚠️ No API key found — set ANTHROPIC_API_KEY first!"

    prompt = f"""
Write a short, warm LinkedIn opening message (3-4 sentences max) to {prospect['name']}
at {prospect['company']}.

Context: {warm_path['explanation']}
Their recent signal: {prospect['recent_signal']}
{MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS['lead_gen'])}

Do not sound salesy or robotic. Reference the real context naturally.
"""
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    data = response.json()
    return data["content"][0]["text"]


# -------------------------------------------------------------------
# 🚪 ROUTE 1: "Are you alive?" test door
# -------------------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "👋 Threadwise backend is alive and running!"})


# -------------------------------------------------------------------
# 🚪 ROUTE 2: Rank ALL prospects by warmth
# -------------------------------------------------------------------

@app.route("/rank-prospects", methods=["GET"])
def rank_prospects():
    results = [find_warm_path(p) for p in prospects]
    results.sort(key=lambda r: r["warmth_score"], reverse=True)
    return jsonify(results)


# -------------------------------------------------------------------
# 🚪 ROUTE 3: Get warm path for ONE prospect by name
# -------------------------------------------------------------------

@app.route("/prospect/<name>", methods=["GET"])
def get_prospect(name):
    for prospect in prospects:
        if prospect["name"].lower() == name.lower():
            return jsonify(find_warm_path(prospect))
    return jsonify({"error": f"No prospect found with the name '{name}'"}), 404


# -------------------------------------------------------------------
# 🚪 ROUTE 4: Write an AI opener message for a prospect + mode
# -------------------------------------------------------------------

@app.route("/write-opener", methods=["POST"])
def write_opener():
    data = request.get_json()
    name = data.get("name", "")
    mode = data.get("mode", "lead_gen")

    for prospect in prospects:
        if prospect["name"].lower() == name.lower():
            message = write_opener_message(prospect, mode=mode)
            return jsonify({
                "name": prospect["name"],
                "mode": mode,
                "message": message
            })
    return jsonify({"error": f"No prospect found with the name '{name}'"}), 404


# -------------------------------------------------------------------
# 🚪 ROUTE 5: Add a REAL prospect (saved permanently)
# -------------------------------------------------------------------

@app.route("/add-prospect", methods=["POST"])
def add_prospect():
    data = request.get_json()

    new_prospect = {
        "name": data.get("name", ""),
        "company": data.get("company", ""),
        # These come in as comma-separated text from the form, so we split them into lists
        "past_companies": [c.strip() for c in data.get("past_companies", "").split(",") if c.strip()],
        "connections": [c.strip() for c in data.get("connections", "").split(",") if c.strip()],
        "recent_signal": data.get("recent_signal", "No recent public activity found")
    }

    if not new_prospect["name"]:
        return jsonify({"error": "A name is required"}), 400

    global prospects
    prospects.append(new_prospect)
    save_all_prospects(prospects)

    return jsonify({"message": f"✅ Added {new_prospect['name']}", "prospect": new_prospect})


# -------------------------------------------------------------------
# 🚪 ROUTE: Delete a prospect by name
# -------------------------------------------------------------------

@app.route("/delete-prospect/<name>", methods=["DELETE"])
def delete_prospect(name):
    global prospects
    original_count = len(prospects)
    prospects = [p for p in prospects if p["name"].lower() != name.lower()]

    if len(prospects) == original_count:
        return jsonify({"error": f"No prospect found with the name '{name}'"}), 404

    save_all_prospects(prospects)
    return jsonify({"message": f"🗑️ Deleted {name}"})


# -------------------------------------------------------------------
# 🚪 ROUTE 6: Update YOUR background (real companies/connections)
# -------------------------------------------------------------------

@app.route("/update-background", methods=["POST"])
def update_background():
    data = request.get_json()

    global my_background
    if "past_companies" in data:
        my_background["past_companies"] = [
            c.strip() for c in data["past_companies"].split(",") if c.strip()
        ]
    if "connections" in data:
        names = [c.strip() for c in data["connections"].split(",") if c.strip()]
        my_background["connections"] = {
            name: {"last_talked": date.today()} for name in names
        }
    if "skills_you_offer" in data:
        my_background["skills_you_offer"] = [
            s.strip() for s in data["skills_you_offer"].split(",") if s.strip()
        ]

    return jsonify({"message": "✅ Background updated"})


# -------------------------------------------------------------------
# ▶️ START THE SERVER
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("🕸️ Starting Threadwise backend...")
    port = int(os.environ.get("PORT", 5001))
    print(f"👉 Running on port {port}")
    app.run(debug=True, host="0.0.0.0", port=port)


# -------------------------------------------------------------------
# 📝 HOW TO RUN THIS (baby steps!)
# -------------------------------------------------------------------
# 1. Install what this needs:
#      pip install flask flask-cors requests
#
# 2. Run it:
#      python threadwise_backend.py
#
# 3. Open http://127.0.0.1:5001 in your browser — you should see a
#    friendly "backend is alive" message!
#
# NOTE: This uses port 5001 (not 5000) so it can run at the same time
# as your VibeReply backend without clashing.
