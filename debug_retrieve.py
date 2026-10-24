from src.retrieve import retrieve   # change if your function has a different name

results = retrieve("How long does standard shipping take in the US?", top_k=4)
print("Number of results:", len(results))
for r in results:
    print(r)
    print("-----")