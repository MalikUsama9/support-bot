"""Load documents -> split into chunks -> embed -> store in Chroma.
Run:  python -m src.ingest
"""
from pathlib import Path
import chromadb

DATA_DIR = Path("data")
DB_PATH = "chroma_db"
COLLECTION = "store_kb"
MAX_CHARS = 1200  # max size of one chunk


def load_documents(path=DATA_DIR):
    docs = []
    for f in sorted(Path(path).glob("*")):
        if f.suffix.lower() in (".md", ".txt"):
            docs.append((f.name, f.read_text(encoding="utf-8")))
    return docs


def split_by_headings(text):
    """Return (doc_title, [(section_title, body), ...]). Splits on markdown headings."""
    doc_title, sections = None, []
    title, buf = "General", []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            sections.append((title, body))

    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            heading = line.lstrip("#").strip()
            if doc_title is None:
                doc_title = heading
            title, buf = heading, []
        else:
            buf.append(line)
    flush()
    return doc_title or "Document", sections


def pack_paragraphs(body, max_chars=MAX_CHARS):
    """If a section is too long, split it on blank lines into pieces under max_chars."""
    if len(body) <= max_chars:
        return [body]
    pieces, current = [], ""
    for para in body.split("\n\n"):
        if current and len(current) + len(para) > max_chars:
            pieces.append(current.strip())
            current = ""
        current += para + "\n\n"
    if current.strip():
        pieces.append(current.strip())
    return pieces


def build_chunks(docs):
    chunks = []
    for filename, text in docs:
        doc_title, sections = split_by_headings(text)
        for sec_title, body in sections:
            for piece in pack_paragraphs(body):
                chunks.append({
                    # Adding titles to the chunk text helps search find the right chunk
                    "text": f"{doc_title} - {sec_title}\n{piece}",
                    "source": filename,
                    "title": sec_title,
                })
    return chunks


def main():
    docs = load_documents()
    chunks = build_chunks(docs)
    print(f"Loaded {len(docs)} documents -> {len(chunks)} chunks")

    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        client.delete_collection(COLLECTION)  # start fresh so we never get duplicates
    except Exception:
        pass
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    col.add(
        ids=[f"chunk-{i}" for i in range(len(chunks))],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"], "title": c["title"]} for c in chunks],
    )
    print("Done. Knowledge base stored in", DB_PATH)


if __name__ == "__main__":
    main()
