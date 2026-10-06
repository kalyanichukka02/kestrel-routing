# Kestrel Home - service-request routing

Suggests which of the 7 teams a new service request should go to, **shows the words behind the decision**, and says
"ask the customer one question" instead of guessing when it is unsure.
**No paid API, no API key, no internet needed. Python standard library + scikit-learn.**

## Run it (clean machine, Python 3.10+)

```bash
git clone <this repo> && cd kestrel-routing
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# copy the pack's CSVs into ./data : train.csv, test_unlabelled.csv, resolution_log.csv, teams.csv, sample_submission.csv
python src/train.py --data-dir data         # ~5 s: trains the model, writes predictions.csv
python src/serve.py                         # then open http://localhost:8000
python src/evaluate.py --data-dir data      # regenerates evidence/evaluation.txt
python tests/test_service.py                # smoke tests
```

Endpoint:

```bash
curl -s -X POST localhost:8000/route -H 'Content-Type: application/json' -d '{
  "request_text": "hi, i already paid for the installation, when will the technician come",
  "channel": "chat", "product_family": "Air Fryer", "warranty_status": "in_warranty"}'
```
Returns `team`, `confidence`, `needs_question` (+ `suggested_question`), `reasons` (plain English), `policy_notes`, `alternatives`.
If the model has not been trained the service still starts and answers `503 {"error": "Model not trained yet..."}`.
Customer data is **not** in this repo (policy s10): `data/`, `model/` and `predictions.csv` are git-ignored.

## What it does and why

The brief asks for a model that matches the bot's labels at 90%+. We found the bot's labels are only **76.7% right** about where
requests actually end up (Billing 65%, Repairs 64%, Filters & Consumables 60% of the time), so copying them copies the mistakes.
We train on the **team that actually closed the request** (`resolution_log.final_team`) instead.

| Model trained on | matches bot label | matches where it really ended |
|---|---|---|
| bot label (client's plan) | 95.0% | 76.2% |
| **final team (ours)** | 77.4% | **83.7%** (95% CI 82.2-85.3%) |
| the bot itself | - | 76.7% |

(Fit on Apr 2025-Mar 2026, tested on Apr-Jun 2026, 2,135 requests the model never saw.)
Where the model is confident (>=0.6, 84% of requests) it is right **94.6%** of the time vs 85.6% for the bot on the same rows.
The other 15.6% are vague ("please call me about my purifier"): nobody, human or model, can route them from the text, so the tool asks for one question.

Model: TF-IDF word 1-2-grams + logistic regression. An LLM was deliberately not used (see DECISIONS.md): cost grows with every request (Farhan's concern), customer text would leave Kestrel (policy s10), and the text is short and templated.

## What is wrong / not done
- Hidden score target is unknown. If it is the **bot's label**, a model trained on the bot's label would score higher (95%) than ours (77%). We chose where requests actually ended (see DECISIONS #1).
- `final_team` is human-recorded and itself noisy. Only 15 months of data, not 18. Many texts look templated; real messages may differ (9.8% of test words never seen in fitting).
- Predictions for the 15% low-confidence rows are a best guess (the file needs a team on every row); they are ~25% right.
- No integration with Kestrel's CRM, no authentication, no logging, localhost only. Hosting cost not priced.
- Savings are a simulation from historical transfers, not a measured result.

See `DECISIONS.md`, `evidence/evaluation.txt`, `memo_to_ritu.md`.
