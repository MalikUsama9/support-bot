"""Score the bot on eval/questions.json.  Run:  python -m eval.run_eval"""
import json, csv, time
from collections import defaultdict
from src.answer import answer

# Free-tier Gemini limits requests per minute, so wait between questions.
DELAY_SECONDS = 7        # pause after every question
RETRY_WAIT_SECONDS = 30  # wait before retrying a question that hit an llm_error


def check(case, res):
    if case.get("expect_handoff"):
        return res["handoff"], "" if res["handoff"] else "should have handed off"
    if res["handoff"]:
        return False, f"unexpected hand-off ({res['reason']})"
    text = res["answer"].lower()
    ok = any(k.lower() in text for k in case["expected_any"])
    return ok, "" if ok else "expected fact missing"


def ask_with_retry(question):
    """Ask the bot; if the AI call failed (e.g. rate limit), wait and try once more."""
    res = answer(question, log=False)
    if res["reason"].startswith("llm_error"):
        print(f"   ...rate limit or API error, waiting {RETRY_WAIT_SECONDS}s and retrying")
        time.sleep(RETRY_WAIT_SECONDS)
        res = answer(question, log=False)
    return res


def main():
    cases = json.load(open("eval/questions.json", encoding="utf-8"))
    rows, by_type = [], defaultdict(lambda: [0, 0])
    for c in cases:
        t0 = time.time()
        res = ask_with_retry(c["question"])
        secs = round(time.time() - t0, 1)
        ok, note = check(c, res)
        by_type[c["type"]][0] += int(ok)
        by_type[c["type"]][1] += 1
        rows.append([c["id"], c["type"], c["question"], res["answer"], res["reason"],
                     "PASS" if ok else "FAIL", note, secs])
        print(f"{'PASS' if ok else 'FAIL'}  {c['id']}  {c['question'][:55]:55}  {note}")
        time.sleep(DELAY_SECONDS)

    print("\n=== RESULTS ===")
    total_ok = sum(v[0] for v in by_type.values())
    total = sum(v[1] for v in by_type.values())
    for t, (ok, n) in by_type.items():
        print(f"{t:12} {ok}/{n}")
    print(f"{'OVERALL':12} {total_ok}/{total} ({round(100*total_ok/total)}%)")

    with open("eval/results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "question", "answer", "reason", "result", "note", "seconds"])
        w.writerows(rows)
    print("Details saved to eval/results.csv")


if __name__ == "__main__":
    main()