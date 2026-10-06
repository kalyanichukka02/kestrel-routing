# Decisions (what was unclear, what I decided, why)

| # | Question | Decision | Evidence / reason |
|---|---|---|---|
| 1 | Train on the bot's label (`team_label`) or the team that closed the request (`final_team`)? | **`final_team`.** | Bot label == final team only 76.7% (valid months). A model copying the bot reaches 95.0% on the bot's labels but only 76.2% on where requests end, i.e. no better than the bot. Ours: 83.7%. The brief says it is scored "against outcomes you do not have", which I read as real outcomes. **Risk:** if the hidden score is the bot label, ours scores ~77% and the alternative would score ~95%. |
| 2 | Ritu's 90% bar | Pushed back: do not use "90% match to the bot" as the acceptance test. | Matching the bot at 90% is easy (95%) and leaves ~Rs 15 lakh/year of misroutes untouched. Proposed bar: accuracy vs where requests end, measured in a 2-week shadow run. |
| 3 | Team names (two renamed 15 Jan 2026) | Merge old into new names in training; predict **new** names (Installs & Demo, Filters & Consumables). | Test set is Jul-Sep 2026, all after the rename. **Risk:** teams.csv `team` column still lists the old names; if the scorer expects them, 2 of 7 team names will mismatch. |
| 4 | Garbled Zoho text (480 rows, 11% of Zoho rows, 0% of CRM) | Drop non-ASCII characters; remove reg-no / order ids. | They carry no meaning for routing. |
| 5 | Zoho resolution times in UTC, not converted (policy s9) | **Not used.** | Routing needs only `final_team` and `transfers`. Evidence the times are off: SR500001 "resolved" before it was created. |
| 6 | Validation split | Time-based: fit Apr25-Mar26, validate Apr-Jun26. | Test is the most recent quarter, so a random split would flatter us (random 5-fold: 83.5%, similar here, but time split is the honest one). |
| 7 | Model type | Word 1-2-gram TF-IDF + logistic regression. Dropped character n-grams. | 84.0-84.6% (char+word) vs 83.7-84.0% (word only): within noise. Word model lets the screen show the exact words behind a decision. |
| 8 | LLM / paid API? | **Not used.** | Short templated texts; per-request cost grows with volume (Farhan); customer text would leave Kestrel (policy s10); no gain shown that would justify it. I did not test an LLM, so I cannot claim it would be worse. |
| 9 | Confidence threshold | 0.60: below it, "ask a question". | Calibration table: >=0.9 -> 97% right (77% of requests); 0.5-0.6 -> 44%; <0.5 -> <26%. Not tuned on the test set. At <0.6 the model is right 25% of the time and the bot 28%. |
| 10 | predictions.csv needs a team on every row | Use the model's best guess even for low-confidence rows. | Format requirement. These ~15% of rows are weak (~25% right); the service flags them, the CSV cannot. |
| 11 | "Paid for installation" requests | Model handles it; the screen also shows a rule-based policy note. | 681 requests mention paying with no billing problem; bot sent 86% to Billing, 24% ended there. Policy s3: Billing only when the payment is the problem. The note explains; it does not change the routing. |
| 12 | Money | Misroute cost = Rs 305 x transfers + Rs 260 per misrouted request (policy s4). Savings simulated on the 3 validation months, scaled x4. | Conservative case: rows where the tool asks a question cost Rs 260 extra. Confident-but-wrong rows cost the average Rs 701. |
| 13 | Privacy | `data/`, `model/`, `predictions.csv` git-ignored; evidence has aggregates only; predictions.csv goes to Drive. | Policy s10: no customer/operational data in public repos. |
| 14 | "Eighteen months" | Data is 15 months (Apr 2025-Jun 2026). Flagged, not fixed. | Ask Tanmay whether 3 months are missing. |

## Version history (for the screen recording)
- **v1 plan (client's):** train on bot label -> 95.0% vs bot, 76.2% vs outcome. Dropped as the target.
- **v2:** char+word n-gram model on final team: ~84.6%. Dropped for the readable word-only model (83.7%).
- **Not built:** LLM routing, channel/time-of-day features, priority features, a question workflow.
