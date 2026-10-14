"""Search the vector database for chunks relevant to a question."""
import chromadb

DB_PATH = "chroma_db"
COLLECTION = "store_kb"


def retrieve(question, top_k=4):
    client = chromadb.PersistentClient(path=DB_PATH)
    col = client.get_collection(COLLECTION)  # fails clearly if you forgot to run ingest
    res = col.query(query_texts=[question], n_results=top_k)
    results = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        results.append({
            "text": doc,
            "source": meta["source"],
            "title": meta["title"],
            "distance": dist,  # cosine distance: lower = more similar
        })
    return results
