import os
import traceback
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from feature_extractor import resolve_repo_from_input, extract_features
from predictor import load_model, predict

load_dotenv()

app = Flask(__name__)

# Handle cross origin resource sharing
CORS(app, origins=[os.getenv("FRONTEND_URL")])

# ==============================
# Routes
# ==============================

@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/predict")
def predict_endpoint():
    body = request.get_json(silent=True)

    if not body or not body.get("input"):
        return jsonify({
            "error": (
                "Request body must be JSON with an 'input' field containing "
                "a GitHub URL or PyPI package name."
            )
        }), 400

    user_input = str(body["input"]).strip()

    # 1. Resolve input to a GitHub owner/repo string
    try:
        repo, repo_url = resolve_repo_from_input(user_input)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    # 2. Extract 6-month features via GitHub API
    extraction = extract_features(repo)
    if extraction["error"]:
        return jsonify({"error": extraction["error"]}), 422

    # 3. Predict + SHAP
    try:
        result = predict(extraction["features"])
    except RuntimeError as e:
        # Model not loaded (file missing at startup)
        return jsonify({"error": str(e)}), 503
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Prediction failed — check server logs."}), 500

    return jsonify({
        "repo":       repo,
        "repo_url":   repo_url,
        "meta":       extraction["meta"],
        "prediction": result,
    })


# =================================================
# Startup — load model once when Flask starts
# =================================================

try:
    load_model()
except FileNotFoundError as e:
    print(f"WARNING: {e}")
    print("Place your .pkl files in backend/models/ and restart.")


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
        port=3000,
    )
