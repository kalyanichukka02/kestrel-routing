"""Train on ALL labelled requests, target = the team that actually closed the request (resolution_log.final_team),
NOT the bot's queue. Then write predictions.csv for test_unlabelled.csv.
  python src/train.py --data-dir data"""
import argparse, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, model

def main(data_dir, out="predictions.csv"):
    tr = common.load(data_dir, "train.csv"); rl = common.load(data_dir, "resolution_log.csv")
    d = tr.merge(rl[["request_id", "final_team"]], on="request_id", how="left")
    assert d.final_team.notna().all(), "some train requests have no final_team"
    d["final"] = d.final_team.replace(common.RENAME)
    assert set(d.final) == set(common.TEAMS), set(d.final)
    pipe = model.make_pipeline_().fit(common.build_text_df(d), d.final)
    teams = common.load(data_dir, "teams.csv"); handles = {common.RENAME.get(t, t): h for t, h in zip(teams.team, teams.handles)}
    model.save(pipe, handles)
    te = common.load(data_dir, "test_unlabelled.csv"); ss = common.load(data_dir, "sample_submission.csv")
    assert set(te.request_id) == set(ss.request_id) and not te.request_id.duplicated().any()
    proba = pipe.predict_proba(common.build_text_df(te))
    te["team"] = pipe.classes_[proba.argmax(1)]; te["confidence"] = proba.max(1).round(3)
    sub = ss[["request_id"]].merge(te[["request_id", "team"]], on="request_id", how="left")
    assert sub.team.isin(common.TEAMS).all() and len(sub) == len(ss)
    sub.to_csv(out, index=False)
    low = (te.confidence < common.THRESHOLD).mean()
    print(f"trained on {len(d)} requests; wrote {out} ({len(sub)} rows)")
    print(f"{low:.1%} of test rows are low-confidence (< {common.THRESHOLD}): the service would ask a question for these")
    print(sub.team.value_counts().to_string())

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data-dir", default="data"); ap.add_argument("--out", default="predictions.csv")
    a = ap.parse_args(); main(a.data_dir, a.out)
