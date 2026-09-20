import json

from common.azsearch import retrieve


def main():
    rows = [json.loads(l) for l in open("data/eval_questions.jsonl")]

    hits_at_1 = 0
    hits_at_5 = 0
    mrr = 0.0

    for row in rows:
        results = retrieve(row["question"], top_k=5, main_only=row.get("main_only", False))
        got = [r["chunk_id"] for r in results]
        expected = set(row["expected_chunks"])

        rank = next((i for i, cid in enumerate(got) if cid in expected), None)

        if rank == 0:
            hits_at_1 += 1
        if rank is not None:
            hits_at_5 += 1
            mrr += 1 / (rank + 1)

        mark = "MISS" if rank is None else f"@{rank + 1}"
        print(f"  {mark:5} {row['question'][:55]}")

    n = len(rows)
    print(f"\nrecall@1: {hits_at_1}/{n} ({100*hits_at_1/n:.0f}%)")
    print(f"recall@5: {hits_at_5}/{n} ({100*hits_at_5/n:.0f}%)")
    print(f"MRR:      {mrr/n:.3f}")


if __name__ == "__main__":
    main()