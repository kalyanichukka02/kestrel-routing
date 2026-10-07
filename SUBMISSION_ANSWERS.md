# Submission form -  answers 

**1. What did you build, and what business decision does it support? State the number and the rupees.**
A routing service (one JSON endpoint + one screen, no paid API) that suggests which of 7 teams should handle a service request, shows the words behind the decision, and says "ask one question" when unsure. Decision: whether to retire the Rs 3.2 lakh bot. Finding: the bot's labels match where requests actually end up only 76.7% of the time (~Rs 15 lakh/year of transfers and repeat contacts), so "match the labels at 90%" would copy its mistakes. Our model is 83.7% right vs where requests end (CI 82.2-85.3%). Estimated saving: at least Rs 1.9 lakh/year in avoided transfers (up to Rs 5.3 lakh) plus the Rs 3.2 lakh licence, i.e. at least ~Rs 5.1 lakh/year. Recommended: 2-week shadow run before switching.

**2. What score do you expect on the hidden outcomes, on which metric, and why?**
Accuracy (share of requests routed to the right team), because every misroute costs the same Rs 700 regardless of team; macro-F1 as a check. I expect ~84% (range 82-85%; macro-F1 ~0.83) if the hidden outcome is the team that closed the request. If it is the bot's queue, I expect only ~77%. Estimated by fitting on Apr 2025-Mar 2026 and testing on Apr-Jun 2026 (2,135 requests the model never saw) with a bootstrap interval. Drift check: test-set confidence and unseen-word rates match the validation months. The final model is fitted on all 10,822 rows, so it may be slightly better.

**3. How do you know it works?**
Time-based split, 2,135 unseen requests. Accuracy vs real outcome 83.7% (bot 76.7%); 94.6% on the 84% of requests it is confident about (bot 85.6% on the same rows). Calibration: confidence >=0.9 -> 97% right. Per-team recall 80-88%. It gets wrong: vague messages ("someone contact me about mixer grinder", "complaint about product"; ~16% of requests, only ~25% right), and confusions of Product Advice/Returns/Installs with Repairs. Service smoke tests pass (bad input, missing model, etc.). Not tested: live traffic, the real hidden score.
Error rate: about 16% of all requests go to the wrong team (about 5% among the confident ones).

**4. Did you change, narrow, or push back on the client's ask?** (can only raise your score)
Yes. (a) Pushed back on "match the labels at 90%": the labels are the bot's output and only 76.7% right vs outcomes; I trained on where requests ended instead, accepting that it matches the bot only 77%. (b) The tool abstains on vague requests rather than always routing. (c) Recommended a 2-week shadow run instead of switching the bot off. (d) Answered Ritu's headcount question using where work ended, not bot queues.

**5. What is wrong with what you are handing us, or with the data?** (can only raise your score)
Assumption risk: I assumed the hidden score is the final team; if it is the bot label, I'd score ~77%. Team names: I predict the new names (Installs & Demo, Filters & Consumables); teams.csv lists the old ones. predictions.csv must give a team for every row, so the ~15% low-confidence rows are weak guesses (~25% right). Data: 15 months, not 18; 480 Zoho rows with garbled text (I dropped non-ASCII); Zoho resolution times are unconverted UTC (one request resolves before it was created), so I did not use them; final_team is human-recorded and noisy; texts look templated, so real messages may be harder (9.8% of test words never seen). Savings are a simulation. Service: localhost only, no authentication, no CRM integration, hosting not priced.

**6. What did you deliberately leave out, and why?**
LLM routing (I did not test one: cost grows per request and customer text would leave Kestrel); channel/time-of-day/priority features; resolution-time analysis (data unreliable); the design of the question workflow; CRM integration. I put the time into the target-label problem, honest validation, and an explainable service.

**7. Anything you built or found that nobody asked for?**
Headcount shares by where work ended (Repairs 23% not 29%, Billing 12% not 15%, Consumables 10% not 14%); the "paid for installation" pattern (86% sent to Billing, 21% belong there) with a policy note on the screen; the 15-vs-18-month discrepancy; the Zoho time-zone bug; the mojibake rows.

**8. What did you use AI for?** 
Claude (chat assistant) for planning, writing the pandas/scikit-learn code, analysis, and drafting the docs and memo. Helped: spotting that the bot's labels only match real outcomes 77% of the time, and the validation design. Wasted time / discarded: a more complex character n-gram model (dropped for a readable one), and the plan to train on the bot's own labels (dropped as the target). No AI model runs inside the product. What I did myself: checked the numbers, decided what to train on, uploaded the repo and files, and recorded the video. Cost: Rs 0 (free claude palnning). Recording: https://youtu.be/jEY6pWsRWPA

**9. Public Google Drive link:** https://drive.google.com/drive/folders/1YHbixnmcgF0owa8SjzHJ17M1V6_jZfOc?usp=drive_link

**10. Someone picks this up on Monday and you are unreachable - the three things they need to know.**
(1) `python src/train.py --data-dir data` then `python src/serve.py`; evidence is in `evidence/evaluation.txt`. (2) The key judgement: we train on where requests ended, not on the bot's label; if Ritu insists on matching the bot's labels, the result is 77%, not 90%. (3) Next steps are a 2-week shadow run and asking Tanmay about the missing 3 months.

**11. Honest hours spent:** 5 hours

**12. GitHub repo link:** https://github.com/kalyanichukka02/kestrel-routing/tree/main

**13. What does one prediction cost, and what would a month cost at ~700 orders a month?**
Rs 0 per prediction: no paid API calls; a prediction takes a few milliseconds on a laptop CPU. 700 x Rs 0 = Rs 0 per month in AI charges. Hosting (any small server) is not priced; retraining takes ~5 seconds. If an LLM were used at, say, 300 tokens per request, the bill would grow with each request, which Farhan asked to avoid.
