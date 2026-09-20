from common.llm import embed


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb)


s1 = "the agreement terminates on December 31, 2026"
s2 = "when does this contract end?"
s3 = "the MCO shall submit a staffing plan by July 1"

v1, v2, v3 = embed(s1), embed(s2), embed(s3)

print("s1 vs s2:", round(cosine(v1, v2), 3))
print("s1 vs s3:", round(cosine(v1, v3), 3))
print("s2 vs s3:", round(cosine(v2, v3), 3))