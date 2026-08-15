"""
Score agent output against the planted answer key.

    python eval/score.py --input runs/agent_output.md

Deliberately dumb: keyword coverage per finding, not semantic matching. The
point is a repeatable number we can watch move, not a clever grader. Workstream
G owns making this better - a second-model judge is the obvious upgrade.
"""
import argparse
import sys
import yaml


def score(text, key):
    text_l = text.lower()
    rows, earned, total = [], 0, 0
    for f in key["findings"]:
        hits = [t for t in f["must_mention"] if t.lower() in text_l]
        got = len(hits) == len(f["must_mention"])
        total += f["weight"]
        earned += f["weight"] if got else 0
        rows.append((f["id"], f["name"], "HIT" if got else "miss",
                     f"{len(hits)}/{len(f['must_mention'])}", f["weight"]))
    return rows, earned, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="file containing agent output")
    ap.add_argument("--answers", default="eval/answer_key.yaml")
    args = ap.parse_args()

    key = yaml.safe_load(open(args.answers))
    text = open(args.input).read()
    rows, earned, total = score(text, key)

    print(f"{'id':<4} {'finding':<22} {'result':<6} {'terms':<7} weight")
    print("-" * 52)
    for r in rows:
        print(f"{r[0]:<4} {r[1]:<22} {r[2]:<6} {r[3]:<7} {r[4]}")
    print("-" * 52)
    print(f"score: {earned}/{total}")
    sys.exit(0 if earned == total else 1)


if __name__ == "__main__":
    main()
