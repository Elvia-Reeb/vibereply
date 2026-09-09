"""
🌟 VIBEREPLY BACKEND 🌟
------------------------
This turns VibeReply into a real "waiter" (a web server) that other apps
(a website, a mobile app, anything) can send requests to.

Think of each function below as a "counter" at a restaurant:
  - Someone walks up (sends a request)
  - We take their order (read what they sent)
  - We ask the chef (our AI functions) to make it
  - We hand back the food (send back the answer)

We're using a tool called "Flask" — it's the easiest way in Python to build
a backend, especially for beginners.
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # 🔓 This lets webpages (like our frontend) talk to this backend safely

BUSINESS_NAME = "VibeReply Demo Co."
PERSONALITY = "friendly and casual, like chatting with a helpful friend"

# -------------------------------------------------------------------
# 💾 SAVING DATA — a simple "notebook" file to remember every review
# -------------------------------------------------------------------
# We're using the SIMPLEST possible way to save data: a plain file called
# "saved_reviews.json". Think of it like a notebook — every time someone
# submits a review, we open the notebook, add a new entry, and close it.
#
# This is perfect for learning! Later, once you have real clients, you'd
# upgrade to a proper database (like SQLite) — but the IDEA is the same.

SAVE_FILE = "saved_reviews.json"


def load_saved_reviews():
    # Open the notebook and read everything in it.
    # If the notebook doesn't exist yet, just start with an empty list.
    if not os.path.exists(SAVE_FILE):
        return []
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_review_entry(entry):
    # Read what's already saved, add our new entry, then write it all back.
    all_reviews = load_saved_reviews()
    all_reviews.append(entry)
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, indent=2)

# -------------------------------------------------------------------
# 🎈 PRACTICE MODE — no API key, no cost, just pretend replies!
# -------------------------------------------------------------------
# Set this to True to practice for FREE with fake AI answers.
# Set it to False later (once you have an API key) to use the real AI.

PRACTICE_MODE = True


# -------------------------------------------------------------------
# 🧠 Same "ask the AI" helper from before — the engine behind everything
# -------------------------------------------------------------------

def ask_ai(prompt):
    # 🎈 PRACTICE MODE: skip the real AI completely, return a pretend answer
    if PRACTICE_MODE:
        if "ONLY one word" in prompt:
            return "Happy"  # pretend mood
        elif "weekly recap" in prompt:
            return "This week had a nice mix of praise and a couple of complaints about support speed. Overall, customers love the automation itself — just keep an eye on response times!"
        elif "REPEATED issues" in prompt:
            return "Heads up: a couple of reviews mentioned slow support response times. Everything else looks great — customers really like how the automation saves them time!"
        else:
            return "Thank you so much for your feedback! We're really glad to hear from you, and we're always working to make things even better. 😊 (this is a PRACTICE MODE pretend reply)"

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return "⚠️ No API key found — set ANTHROPIC_API_KEY first!"

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    data = response.json()
    return data["content"][0]["text"]


# -------------------------------------------------------------------
# 🚪 ROUTE 1: "Are you alive?" — a simple test door
# -------------------------------------------------------------------
# This is the easiest possible check. If this works, your backend is running!

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": f"👋 {BUSINESS_NAME} backend is alive and running!"})


# -------------------------------------------------------------------
# 🚪 ROUTE 2: Analyze ONE review (mood + reply)
# -------------------------------------------------------------------
# Someone sends us ONE review, we send back the mood + a suggested reply.

@app.route("/analyze-review", methods=["POST"])
def analyze_review():
    # This reads the data someone sent us (like an order slip)
    data = request.get_json()
    customer = data.get("customer", "Customer")
    stars = data.get("stars", 3)
    text = data.get("text", "")

    # 🎈 PRACTICE MODE: use simple RULES based on stars instead of calling
    # the real AI, so different ratings give different pretend answers.
    if PRACTICE_MODE:
        stars_num = int(stars)

        if stars_num <= 2:
            mood = "Frustrated"
            reply = (
                f"Hi {customer}, we're really sorry to hear this didn't meet your "
                f"expectations. We'd love the chance to make it right — please reach "
                f"out so we can help. (this is a PRACTICE MODE pretend reply)"
            )
        elif stars_num == 3:
            mood = "Neutral"
            reply = (
                f"Thanks for your honest feedback, {customer}! We're glad it worked "
                f"okay and we're always looking for ways to make it even better. "
                f"(this is a PRACTICE MODE pretend reply)"
            )
        else:
            mood = "Happy"
            reply = (
                f"Thank you so much, {customer}! We're really glad to hear you had "
                f"a great experience. 😊 (this is a PRACTICE MODE pretend reply)"
            )

        # 💾 Save this to our notebook file before sending the answer back
        save_review_entry({
            "customer": customer,
            "stars": stars_num,
            "text": text,
            "mood": mood,
            "suggested_reply": reply,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        return jsonify({
            "customer": customer,
            "mood": mood,
            "suggested_reply": reply
        })
    mood_prompt = f"""
Read this customer review and reply with ONLY one word describing the
customer's true emotional mood: Happy, Frustrated, Angry, Disappointed,
Neutral, or Excited.

Review: "{text}"
"""
    mood = ask_ai(mood_prompt).strip()

    # Step 2: write a reply matching our personality
    reply_prompt = f"""
You are replying to a customer review for "{BUSINESS_NAME}".
Your reply's tone/personality should be: {PERSONALITY}.

Customer: {customer}
Star rating: {stars}/5
Detected mood: {mood}
Review: "{text}"

Write a short reply (2-4 sentences) matching that personality.
If the mood is negative, apologize sincerely and offer to fix it.
If the mood is positive, thank them and mention something specific.
"""
    reply = ask_ai(reply_prompt)

    # 💾 Save this to our notebook file before sending the answer back
    save_review_entry({
        "customer": customer,
        "stars": stars,
        "text": text,
        "mood": mood,
        "suggested_reply": reply,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Send the answer back as a nice, organized package (JSON)
    return jsonify({
        "customer": customer,
        "mood": mood,
        "suggested_reply": reply
    })


# -------------------------------------------------------------------
# 🚪 ROUTE: View everything saved so far (like opening the notebook)
# -------------------------------------------------------------------

@app.route("/saved-reviews", methods=["GET"])
def saved_reviews():
    return jsonify(load_saved_reviews())


# -------------------------------------------------------------------
# 🚪 ROUTE 3: Trend Spotter — heads-up from a LIST of reviews
# -------------------------------------------------------------------

@app.route("/trends", methods=["POST"])
def trends():
    data = request.get_json()
    reviews = data.get("reviews", [])

    combined_text = "\n".join(
        f"- ({r.get('stars', 3)} stars) {r.get('text', '')}" for r in reviews
    )
    prompt = f"""
Here are recent customer reviews for "{BUSINESS_NAME}":

{combined_text}

Look for any REPEATED issues or patterns. Write a short, friendly heads-up
(2-3 sentences) for the business owner. If nothing repeats, say everything
looks good and mention one strength instead.
"""
    result = ask_ai(prompt)
    return jsonify({"trend_alert": result})


# -------------------------------------------------------------------
# 🚪 ROUTE 4: Review Story — weekly recap from a LIST of reviews
# -------------------------------------------------------------------

@app.route("/review-story", methods=["POST"])
def review_story():
    data = request.get_json()
    reviews = data.get("reviews", [])

    combined_text = "\n".join(
        f"- ({r.get('stars', 3)} stars) {r.get('text', '')}" for r in reviews
    )
    prompt = f"""
Here are recent customer reviews for "{BUSINESS_NAME}":

{combined_text}

Write a short, warm "weekly recap" story (4-5 sentences) summarizing how
things went overall, mentioning the good and the areas to improve.
"""
    result = ask_ai(prompt)
    return jsonify({"review_story": result})


# -------------------------------------------------------------------
# ▶️ START THE SERVER
# -------------------------------------------------------------------

if __name__ == "__main__":
    print(f"🌟 Starting {BUSINESS_NAME} backend...")
    print("👉 Open http://127.0.0.1:5000 in your browser to test it!")
    app.run(debug=True, port=5000)


# -------------------------------------------------------------------
# 📝 HOW TO RUN THIS (baby steps!)
# -------------------------------------------------------------------
# 1. Install the extra tool this needs:
#      pip install flask requests
#
# 2. Set your API key (same as before):
#      Mac/Linux:   export ANTHROPIC_API_KEY="your-key-here"
#      Windows:     set ANTHROPIC_API_KEY=your-key-here
#
# 3. Run the backend:
#      python vibereply_backend.py
#
# 4. You'll see a message saying it's running on http://127.0.0.1:5000
#    Open that link in your browser — you should see a friendly hello message!
#
# That's it — your backend is officially "alive" and waiting for requests. 🎉
