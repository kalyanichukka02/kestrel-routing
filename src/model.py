"""Model = TF-IDF (1-2 word n-grams) + logistic regression. Chosen over a char-n-gram model (84.6%) because it is
within noise (84.0%) AND lets us show the exact words behind each decision."""
import os, joblib, numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import common

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model", "model.joblib")
META_PREFIXES = ("ch_", "pf_", "ws_")
QUESTION = ("Please ask one question: is the product faulty, do you need help using it, is it a payment problem, "
            "a delivery problem, or a warranty question?")

def make_pipeline_():
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                         LogisticRegression(C=10, max_iter=3000))

def save(pipe, handles, path=MODEL_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump({"pipe": pipe, "handles": handles, "threshold": common.THRESHOLD}, path)

def load_bundle(path=MODEL_PATH):
    if not os.path.exists(path):
        return None
    return joblib.load(path)

def predict_one(bundle, rec):
    """rec: dict with request_text (required), channel, product_family, warranty_status (optional)."""
    text = common.build_text(rec["request_text"], rec.get("channel", ""), rec.get("product_family", ""), rec.get("warranty_status", ""))
    pipe = bundle["pipe"]; vec, clf = pipe.steps[0][1], pipe.steps[1][1]
    X = vec.transform([text]); proba = clf.predict_proba(X)[0]
    order = np.argsort(proba)[::-1]; classes = clf.classes_
    team, conf = str(classes[order[0]]), float(proba[order[0]])
    # reasons: words (from the customer's message) that pushed the score toward the chosen team
    names = vec.get_feature_names_out(); row = X.tocoo()
    contrib = {names[j]: v * clf.coef_[order[0], j] for j, v in zip(row.col, row.data)}
    words = [(w, c) for w, c in sorted(contrib.items(), key=lambda kv: -kv[1]) if c > 0 and not w.startswith(META_PREFIXES)][:4]
    needs_q = conf < bundle["threshold"]
    cleaned = common.clean_text(rec["request_text"])
    notes = []
    if common.PAID_RX.search(cleaned) and not common.BILLING_PROBLEM_RX.search(cleaned) and team != "Billing":
        notes.append("Customer mentions paying, but describes no payment problem. Policy s3: Billing only when the payment itself is the problem.")
    reasons = ([f"Words in the message that point to {team}: " + ", ".join(f"'{w}'" for w, _ in words)] if words else
               ["No distinctive words in the message point clearly to one team."])
    reasons.append(f"{team} handles: {bundle['handles'].get(team, '')}")
    return {"team": team, "confidence": round(conf, 3), "needs_question": bool(needs_q),
            "suggested_question": QUESTION if needs_q else None,
            "reasons": reasons, "policy_notes": notes,
            "alternatives": [{"team": str(classes[i]), "confidence": round(float(proba[i]), 3)} for i in order[1:3]],
            "advice": ("Confidence is low: ask the customer one question before routing." if needs_q
                       else f"Route to {team}.")}
