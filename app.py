import os
from flask import Flask, render_template, request, jsonify
from logic.engine import analyze_interests, generate_roadmap
from logic.extractor import init_background_job
from logic.llm import get_counselor_response

app = Flask(__name__)

# Boot the 10-hour background data extraction pipeline
init_background_job()

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/careers")
def careers():
    interests = request.args.get("q", "").strip()
    roles = analyze_interests(interests, top_n=6)
    return render_template("careers.html", roles=roles, interests=interests)


@app.route("/roadmap")
def roadmap():
    slug = request.args.get("role", "").strip()
    interests = request.args.get("q", "").strip()   # passed through for back-link
    data = generate_roadmap(slug)
    return render_template("roadmap.html", roadmap=data, interests=interests)


# ── Legacy routes (keep assessment & dashboard working) ────────────────────
@app.route("/assessment")
def assessment():
    return render_template("assessment.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    role = data.get("role", "General AI")
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    response = get_counselor_response(role, message)
    return jsonify({"response": response})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
