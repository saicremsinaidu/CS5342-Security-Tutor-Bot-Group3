"""
Build a persistent local vector index from Markdown seeds (and PDFs if present).
Usage:
  python ingest.py
Creates/updates Chroma DB under data/vectordb/
"""
import os, glob, re, uuid, textwrap
from typing import List
from pypdf import PdfReader
import chromadb
from chromadb.config import Settings
# from models import embed_texts
from embeddings import embed_texts

ROOT = os.path.dirname(__file__)
SEEDS_DIR = os.path.join(ROOT, "data", "seeds")
DB_DIR = os.path.join(ROOT, "data", "vectordb")
COLLECTION = "cs5342_kb"

def read_markdown(path:str)->str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def read_pdf(path:str)->str:
    txt = []
    try:
        pdf = PdfReader(path)
        for p in pdf.pages:
            t = p.extract_text() or ""
            txt.append(t)
    except Exception as e:
        print(f"[WARN] Failed to read {path}: {e}")
    return "\n".join(txt)

def chunk(text:str, chunk_size:int=800, overlap:int=100)->List[str]:
    # simple char-based chunking with overlap
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    chunks = []
    i = 0
    while i < len(text):
        part = text[i:i+chunk_size]
        # extend to nearest sentence end if possible
        end = part.rfind(". ")
        if end > 200:
            part = part[:end+1]
        chunks.append(part)
        i += max(1, chunk_size - overlap)
    return [c.strip() for c in chunks if c.strip()]

def collect_sources():
    data_root = os.path.join(ROOT, "data")
    paths = []
    paths += glob.glob(os.path.join(data_root, "**", "*.md"), recursive=True)
    paths += glob.glob(os.path.join(data_root, "**", "*.txt"), recursive=True)
    paths += glob.glob(os.path.join(data_root, "**", "*.pdf"), recursive=True)
    return sorted(list(dict.fromkeys(paths)))

def main():
    os.makedirs(DB_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=DB_DIR, settings=Settings(allow_reset=False))
    col = client.get_or_create_collection(COLLECTION, metadata={"hnsw:space":"cosine"})

    paths = collect_sources()
    if not paths:
        print("[INFO] No sources found. Add .md files to data/seeds/.")
        return

    print(f"[INFO] Ingesting {len(paths)} file(s)…")
    all_docs, all_metas, all_ids = [], [], []

    for p in paths:
        ext = os.path.splitext(p)[1].lower()
        text = read_markdown(p) if ext==".md" else read_pdf(p)
        for ch in chunk(text):
            all_docs.append(ch)
            all_metas.append({"source": os.path.relpath(p, ROOT)})
            all_ids.append(str(uuid.uuid4()))

    print(f"[INFO] Embedding {len(all_docs)} chunks…")
    vecs = embed_texts(all_docs).tolist()

    print("[INFO] Upserting to Chroma…")
    col.add(ids=all_ids, metadatas=all_metas, documents=all_docs, embeddings=vecs)

    print(f"[OK] Indexed {len(all_docs)} chunks from {len(paths)} file(s). DB: data/vectordb/")

if __name__ == "__main__":
    main()
