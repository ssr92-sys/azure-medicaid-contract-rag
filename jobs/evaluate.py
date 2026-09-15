import json
from collections import Counter


def load(path):
    rows = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            rows[r["source_file"]] = r
    return rows


def main():
    truth = load("data/truth.jsonl")
    pred = load("data/extracted.jsonl")

    total = 0
    wrong = 0
    by_field = Counter()

    for path in sorted(truth):
        if path not in pred:
            print(f"{path}: MISSING from extracted.jsonl")
            continue

        t, p = truth[path], pred[path]

        for field in t:
            if field == "source_file":
                continue

            total += 1
            if t[field] != p.get(field):
                wrong += 1
                by_field[field] += 1
                print(f"{path}  {field}: expected {t[field]!r}, got {p.get(field)!r}")

    print()
    print(f"{total - wrong}/{total} fields correct "
          f"({100 * (total - wrong) / total:.1f}%)" if total else "no data")

    if by_field:
        print("\nerrors by field:")
        for field, n in by_field.most_common():
            print(f"  {field}: {n}")


if __name__ == "__main__":
    main()