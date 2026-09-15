import json
import random
from datetime import date, timedelta

from common.llm import ask

VENDORS = ["Medora Solutions, LLC", "LoneStar Care Services, LLC",
           "Aurelia Health Services, LLC", "Suncoast Care Services, LLC",
           "SunCrest Health Solutions, LLC", "Bayline Clinical Partners, LLC"]
PLANS = ["Northbridge Health Plan", "GulfHealth Plan, Inc.",
         "Evergreen Health Plan, Inc.", "BayPoint Health Plan, Inc.",
         "Hudson Valley Care Plan, Inc.", "Clearwater Health Plan, Inc."]
STATES = ["California", "Texas", "Florida", "New York", "Ohio"]
LOB_SETS = [
    ["Medicare Advantage"],
    ["Medicaid"],
    ["Commercial"],
    ["Medicare Advantage", "Medicaid"],
    ["Medicare Advantage", "Medicaid", "Commercial"],
]


def make_facts():
    start = date(2025, 1, 1) + timedelta(days=random.randint(0, 600))
    years = random.choice([1, 2, 3])
    end = date(start.year + years, start.month, start.day) - timedelta(days=1)

    return {
        "vendor_name": random.choice(VENDORS),
        "plan_name": random.choice(PLANS),
        "effective_date": start.isoformat(),
        "end_date": end.isoformat(),
        "lines_of_business": random.choice(LOB_SETS),
        "payment_terms_days": random.choice([30, 45, 60]),
        "auto_renews": random.choice([True, False]),
        "termination_notice_days": random.choice([30, 60, 90, 120]),
        "governing_law_state": random.choice(STATES),
    }


def build_prompt(facts):
    renewal = (
        "Include an auto-renewal clause for successive one-year terms."
        if facts["auto_renews"]
        else "State explicitly that this Agreement does NOT automatically renew."
    )

    return f"""Write a fictional vendor services contract between a health plan
and a services vendor. About 25 lines.

Use EXACTLY these facts:
- Health plan: {facts['plan_name']}
- Vendor: {facts['vendor_name']}
- Effective date: {facts['effective_date']}
- Initial term ends: {facts['end_date']}
- Lines of business covered: {', '.join(facts['lines_of_business'])}
- Payment terms: Net {facts['payment_terms_days']}
- Termination for convenience notice: {facts['termination_notice_days']} days
- Governing law: State of {facts['governing_law_state']}

{renewal}

Write dates in normal prose style (e.g. "March 21, 2026"), not ISO format.
Vary the structure and wording. Include realistic extra clauses such as
confidentiality, indemnification, insurance, audit rights, and notices.
Output only the contract text."""


def main(n=5):
    ok = 0
    with open("data/truth.jsonl", "w") as truth_file:
        for i in range(1, n + 1):
            path = f"data/contract_{i:03d}.txt"
            try:
                facts = make_facts()
                text = ask(build_prompt(facts))

                with open(path, "w") as f:
                    f.write(text)

                facts["source_file"] = path
                truth_file.write(json.dumps(facts) + "\n")
                truth_file.flush()

                ok += 1
                print(f"[{i}/{n}] wrote {path}")

            except Exception as e:
                print(f"[{i}/{n}] FAILED {path}: {type(e).__name__}: {e}")

    print(f"generated {ok}/{n}")


if __name__ == "__main__":
    main(25)