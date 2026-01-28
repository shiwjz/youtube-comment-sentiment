from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    max_comments = data.get("maxComments")

    if not url:
        return jsonify({"ok": False, "error": "url is required"}), 400
    if max_comments is None:
        return jsonify({"ok": False, "error": "maxComments is required"}), 400

    try:
        max_comments = int(max_comments)
    except:
        return jsonify({"ok": False, "error": "maxComments must be a number"}), 400

    return jsonify({
        "ok": True,
        "received": {
            "url": url,
            "maxComments": max_comments
        },
        "message": "M1 success!"
    }), 200

if __name__ == "__main__":
    app.run(debug=True)
