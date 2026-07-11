"""
Loads the trained pipeline (preprocessor + classifier) and threshold,
converts a feature dict into model input, runs prediction, and computes
SHAP values for explainability.
"""

import os
import joblib
import shap
import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ===============================================
# Module-level singletons — loaded once at startup
# ===============================================

_model = None        # full sklearn Pipeline (preprocessor + classifier)
_threshold = None    # tuned decision threshold (float)
_explainer = None    # shap.TreeExplainer fitted on the classifier step


# ===============================================
# Feature order must exactly match training
# (numeric first, then binary flags, then owner_type one-hot)
# ===============================================

NUMERIC_FEATURES = [
    "author_account_age_years",
    "author_public_repos_at_creation",
    "commits",
    "contributors",
    "commits_m1_m3",
    "commits_m4_m6",
    "commit_concentration",
    "bus_factor",
    "active_weeks",
    "days_to_first_commit",
    "issues_opened",
    "issues_closed",
    "prs_opened",
    "prs_closed",
    "issue_comments",
    "days_to_first_issue",
    "stars",
    "forks",
    "releases",
    "commit_momentum",
    "commit_per_contributor",
    "issue_resolution_rate",
    "pr_merge_rate",
    "interest_density",
    "comments_per_issue_pr",
    "engagement_score",
]

BINARY_FEATURES = [
    "is_organization",
    "has_readme",
    "has_license",
    "has_contributing",
    "has_ci_cd",
    "has_setup_cfg_or_pyproject",
    "has_changelog",
    "has_dockerfile",
    "has_tests_dir",
    "has_docs_dir",
    "has_docs_config",
    "has_issues",
    "has_prs",
    "has_releases",
    "has_external_contributors",
    "has_community_engagement",
    "zero_commit_activity",
    "single_contributor_no_engagement",
]

CATEGORICAL_FEATURES = ["owner_type"]

ALL_INPUT_FEATURES = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES


# ===============================================
# Startup
# ===============================================

def load_model():
    """
    Load the saved sklearn Pipeline and threshold from disk.
    Must be called once before any predict() call.
    """
    global _model, _threshold, _explainer

    model_path = os.getenv("MODEL_PATH", "./models/random_forest_model.pkl")
    threshold_path = os.getenv("THRESHOLD_PATH", "./models/random_forest_threshold.pkl")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found: '{model_path}'. "
            "Check MODEL_PATH in your .env file."
        )

    _model = joblib.load(model_path)

    if os.path.exists(threshold_path):
        _threshold = float(joblib.load(threshold_path))
    else:
        _threshold = 0.52   # matches the RF tuned threshold from my training run
        print(f"Threshold file not found — using default {_threshold}")

    # Fit SHAP explainer on the classifier step of the pipeline
    classifier = _model.named_steps["classifier"]
    _explainer = shap.TreeExplainer(classifier)

    print(f"[predictor] Model loaded — threshold: {_threshold:.3f}")


# ===============================================
# Feature dict → DataFrame
# ===============================================

def features_to_dataframe(features: dict) -> pd.DataFrame:
    """
    Convert the raw feature dict from feature_extractor into a single-row
    DataFrame whose columns match exactly what the training pipeline expects.
    Missing keys default to 0 / 'Unknown'.
    """
    row = {}
    for col in NUMERIC_FEATURES + BINARY_FEATURES:
        row[col] = features.get(col, 0)
    row["owner_type"] = features.get("owner_type", "Unknown")
    return pd.DataFrame([row])


# ===============================================
# Prediction
# ===============================================

def predict(features: dict) -> dict:
    """
    Run prediction and SHAP explanation for one repo's feature dict.

    Returns:
    {
        "risk_score":  float   — P(abandoned), 0–1
        "label":       int     — 0 active / 1 abandoned
        "verdict":     str     — "Low risk" | "Medium risk" | "High risk"
        "threshold":   float
        "shap_values": [
            { "feature": str, "feature_value": float|int, "shap": float },
            ...  top 12 by |shap|, sorted descending
        ]
    }
    """
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() at startup.")

    X_df = features_to_dataframe(features)

    preprocessor = _model.named_steps["preprocessor"]
    classifier    = _model.named_steps["classifier"]

    X_transformed = preprocessor.transform(X_df)
    prob  = float(classifier.predict_proba(X_transformed)[0][1])
    label = int(prob >= _threshold)

    if prob < 0.40:
        verdict = "Low risk"
    elif prob < 0.70:
        verdict = "Medium risk"
    else:
        verdict = "High risk"

    # ===========================
    # SHAP
    # =============================
    shap_vals = _explainer.shap_values(X_transformed)
    
    if isinstance(shap_vals, list):
        sv = np.array(shap_vals[1]).flatten()
    elif isinstance(shap_vals, np.ndarray):
        if shap_vals.ndim == 3:
            sv = shap_vals[0, :, 1]
        elif shap_vals.ndim == 2:
            sv = shap_vals[0]
        else:
            sv = shap_vals
    else:
        sv = np.array(shap_vals).flatten()

    sv = np.array(sv).flatten()

    # Recover clean feature names from the fitted preprocessor
    try:
        raw_names  = list(preprocessor.get_feature_names_out())
        clean_names = [n.replace("num__", "").replace("cat__", "").replace("bin__", "") for n in raw_names]
    except Exception:
        clean_names = [f"feature_{i}" for i in range(len(sv))]

    # Pair names with SHAP values, sort by |shap|, take top 12
    pairs = sorted(zip(clean_names, sv), key=lambda x: abs(x[1]), reverse=True)[:12]

    shap_output = []
    for name, shap_val in pairs:
        # Retrieve the original (pre-transform) value for display
        feat_val = features.get(name, 0)
        shap_output.append({
            "feature":       name,
            "feature_value": feat_val,
            "shap":          round(float(shap_val), 4),
        })

    return {
        "risk_score":  round(prob, 4),
        "label":       label,
        "verdict":     verdict,
        "threshold":   round(_threshold, 3),
        "shap_values": shap_output,
    }