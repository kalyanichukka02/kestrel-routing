"""Evidence script. Writes evidence/evaluation.txt (aggregate numbers only - no customer text, policy s10).
  python src/evaluate.py --data-dir data"""
import argparse, os, sys
import numpy as np, pandas as pd
from sklearn.model_selection import cross_val_predict, StratifiedKFold
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, model

TRANSFER, CONTACT = 305, 260   # policy s4

def main(data_dir, out_dir="evidence"):
    os.makedirs(out_dir, exist_ok=True); L = []
    P = lambda *a: L.append(" ".join(str(x) for x in a))
    tr = common.load(data_dir, "train.csv"); rl = common.load(data_dir, "resolution_log.csv"); te = common.load(data_dir, "test_unlabelled.csv")
    d = tr.merge(rl[["request_id", "final_team", "transfers"]], on="request_id")
    d["bot"] = d.team_label.replace(common.RENAME); d["final"] = d.final_team.replace(common.RENAME)
    d["text"] = common.build_text_df(d); d["month"] = d.created_at_ist.str[:7]
    A, B = d[d.month < "2026-04"], d[d.month >= "2026-04"].copy()
    P(f"DATA: {len(d)} train requests, {d.month.min()}..{d.month.max()} ({d.month.nunique()} months, not 18); test {len(te)} rows")
    P(f"Time split: fit on {d.month.min()}..2026-03 ({len(A)} rows), validate on 2026-04..2026-06 ({len(B)} rows) - never seen in fitting\n")
    # 1. The bot itself
    P(f"1. THE BOT vs where requests actually ended: label==final {np.mean(d.bot==d.final):.1%} on all train, {np.mean(B.bot==B.final):.1%} on validation months")
    for t, g in d.groupby("bot"): P(f"   bot queue {t:24s} n={len(g):5d}  ended there {np.mean(g.bot==g.final):.1%}")
    # 2. target comparison
    P("\n2. WHICH TARGET TO TRAIN ON (valid months)         acc vs BOT label | acc vs FINAL team")
    for tgt in ["bot", "final"]:
        m = model.make_pipeline_().fit(A.text, A[tgt]); p = m.predict(B.text)
        P(f"   model trained on {tgt.upper():5s}                          {np.mean(p==B.bot):6.1%}          | {np.mean(p==B.final):6.1%}")
        if tgt == "final": mf, pf = m, p; proba = m.predict_proba(B.text)
    P(f"   (reference: the bot itself vs FINAL team = {np.mean(B.bot==B.final):.1%})")
    # 3. headline accuracy with CI
    ok = (pf == B.final.values).astype(int); rng = np.random.default_rng(0)
    bs = [ok[rng.integers(0, len(ok), len(ok))].mean() for _ in range(2000)]
    P(f"\n3. EXPECTED SCORE (accuracy vs final team, final-target model): {ok.mean():.1%}, bootstrap 95% CI {np.percentile(bs,2.5):.1%}-{np.percentile(bs,97.5):.1%}")
    okb = (pf == B.bot.values).astype(int); P(f"   same model vs BOT label: {okb.mean():.1%}")
    from sklearn.metrics import f1_score; P(f"   macro-F1 vs final team: {f1_score(B.final, pf, average='macro'):.3f}")
    oof = cross_val_predict(model.make_pipeline_(), d.text, d.final, cv=StratifiedKFold(5, shuffle=True, random_state=0))
    P(f"   (random 5-fold on all train, for comparison: {np.mean(oof==d.final):.1%} - time split is the honest one)")
    # 4. confidence
    B["pred"] = pf; B["conf"] = proba.max(1)
    P("\n4. CONFIDENCE (valid months)  bin: share of requests | accuracy vs final | bot accuracy on same rows")
    B["bin"] = pd.cut(B.conf, [0, .4, .5, .6, .7, .8, .9, 1.0])
    for b, g in B.groupby("bin", observed=True): P(f"   {str(b):12s} {len(g)/len(B):6.1%} | {np.mean(g.pred==g.final):6.1%} | {np.mean(g.bot==g.final):6.1%}")
    conf = B.conf >= common.THRESHOLD
    P(f"   threshold {common.THRESHOLD}: routes {conf.mean():.1%} of requests at {np.mean(B.pred[conf]==B.final[conf]):.1%} accuracy (bot on those rows: {np.mean(B.bot[conf]==B.final[conf]):.1%});"
      f" asks a question on {(~conf).mean():.1%} (model {np.mean(B.pred[~conf]==B.final[~conf]):.1%}, bot {np.mean(B.bot[~conf]==B.final[~conf]):.1%} right there)")
    P("\n5. PER-TEAM (valid months): team | recall | precision")
    for t in common.TEAMS:
        P(f"   {t:24s} {np.mean(B.pred[B.final==t]==t):6.1%} | {np.mean(B.final[B.pred==t]==t):6.1%}")
    P("   most common confusions (final -> predicted):", {k: int(v) for k, v in pd.Series(list(zip(B.final[B.pred != B.final], B.pred[B.pred != B.final]))).value_counts().head(5).items()})
    # 6. money
    mis = d.transfers > 0
    cost_mis = (d.transfers.sum() * TRANSFER + mis.sum() * CONTACT) / mis.sum()
    P(f"\n6. MONEY (policy s4: transfer Rs {TRANSFER}, extra contact Rs {CONTACT})")
    tot = d.transfers.sum() * TRANSFER + mis.sum() * CONTACT; months = d.month.nunique()
    P(f"   bot's misroutes, whole train: {mis.sum()} requests needed >=1 transfer ({mis.mean():.1%}); {d.transfers.sum()} transfers -> Rs {tot:,.0f} over {months} months = Rs {tot/months*12:,.0f}/year; avg Rs {cost_mis:,.0f} per misrouted request")
    bot_cost = B.transfers * TRANSFER + (B.transfers > 0) * CONTACT
    wrong = (B.pred != B.final)
    base = np.where(conf, np.where(wrong, cost_mis, 0.0), bot_cost)                   # abstained rows cost what they cost today
    cons = np.where(conf, np.where(wrong, cost_mis, 0.0), bot_cost + CONTACT)          # asking a question costs one extra contact
    nm = B.month.nunique(); scale = 12 / nm
    P(f"   validation months: bot cost Rs {bot_cost.sum():,.0f}; model (abstain rows cost same as today) Rs {base.sum():,.0f}; model (abstain rows +Rs {CONTACT} for the question) Rs {cons.sum():,.0f}")
    P(f"   => saving per year, scaled from {nm} months: Rs {(bot_cost.sum()-base.sum())*scale:,.0f} (base) / Rs {(bot_cost.sum()-cons.sum())*scale:,.0f} (conservative)")
    P(f"   plus bot licence Rs 320,000/year. Requests per month in data: {len(d)/months:.0f}")
    # 7. headcount
    P("\n7. BUSIEST TEAMS (share of requests): team | by bot label | where it actually ended")
    for t in common.TEAMS: P(f"   {t:24s} {np.mean(d.bot==t):6.1%} | {np.mean(d.final==t):6.1%}")
    # 8. drift
    vec = mf.steps[0][1]; vocab = set(vec.get_feature_names_out())
    def unseen(texts): 
        toks = [w for t in texts for w in t.split() if not w.startswith(model.META_PREFIXES)]; return np.mean([w not in set(w2 for v in vocab for w2 in v.split()) for w in toks])
    te["text"] = common.build_text_df(te); pt = mf.predict_proba(te.text)
    P(f"\n8. DRIFT CHECK, test (Jul-Sep 2026) vs validation: share of test rows with confidence >= {common.THRESHOLD}: {np.mean(pt.max(1)>=common.THRESHOLD):.1%} (valid {conf.mean():.1%}); "
      f"mean confidence {pt.max(1).mean():.3f} (valid {B.conf.mean():.3f}); words never seen in fitting: {unseen(te.text):.1%} (valid {unseen(B.text):.1%})")
    P("   predicted team mix on test:", {k: round(v, 3) for k, v in pd.Series(mf.classes_[pt.argmax(1)]).value_counts(normalize=True).items()})
    open(os.path.join(out_dir, "evaluation.txt"), "w").write("\n".join(L)); print("\n".join(L))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data-dir", default="data"); a = ap.parse_args(); main(a.data_dir)
