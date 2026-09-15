import glob
import json

from common.llm import ask_json

SCHEMA_PROMPT = """Extract the following fields from the contract below.
Return JSON with exactly these keys:

- vendor_name: the vendor company name
- plan_name: the health plan company name
- effective_date: start date, format YYYY-MM-DD
- end_date: end of the initial term, format YYYY-MM-DD
- lines_of_business: list, using only these values: "Medicare Advantage", "Medicaid", "Commercial"
- payment_terms_days: integer, days to pay an undisputed invoice
- auto_renews: true or false
- termination_notice_days: integer, days notice to terminate FOR CONVENIENCE
- governing_law_state: US state name

If a field is not stated in the contract, use null.

CONTRACT:
{contract}
"""


def main():
    paths = sorted(glob.glob("data/contract_*.txt"))
    ok = 0

    with open("data/extracted.jsonl", "w") as out:
        for i, path in enumerate(paths, 1):
            try:
                with open(path) as f:
                    contract = f.read()

                result = ask_json(SCHEMA_PROMPT.format(contract=contract))
                result["source_file"] = path

                out.write(json.dumps(result) + "\n")
                out.flush()

                ok += 1
                print(f"[{i}/{len(paths)}] extracted {path}")

            except Exception as e:
                print(f"[{i}/{len(paths)}] FAILED {path}: {type(e).__name__}: {e}")

    print(f"extracted {ok}/{len(paths)}")


if __name__ == "__main__":
    main()