# rag.py
"""
Retrieval + answer composition + robust quiz generator/grader (CPU only).
"""

import os
import re
import random
import itertools
from typing import List, Tuple, Dict, Any

import chromadb
from chromadb.config import Settings
import numpy as np

# from models import embed_texts, cosine_sim
from embeddings import embed_texts, cosine_sim

ROOT = os.path.dirname(__file__)
DB_DIR = os.path.join(ROOT, "data", "vectordb")
COLLECTION = "cs5342_kb"

# =========================
# Retrieval
# =========================
def _collection():
    client = chromadb.PersistentClient(path=DB_DIR, settings=Settings(allow_reset=False))
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space":"cosine"})

def retrieve(query: str, k: int = 6) -> List[Tuple[str, Dict[str, str]]]:
    col = _collection()
    qv = embed_texts([query])[0].tolist()
    out = col.query(query_embeddings=[qv], n_results=k, include=["documents","metadatas"])
    docs = out.get("documents", [[]])[0]
    metas = out.get("metadatas", [[]])[0]
    return list(zip(docs, metas))

# =========================
# Tutor (Q&A)
# =========================
def make_answer(query: str, k: int = 4) -> Tuple[str, List[Dict[str, str]]]:
    hits = retrieve(query, k=max(k, 8))
    if not hits:
        return ("I don't have any indexed materials yet. Add notes in data/ and run ingest.", [])
    ctx = " ".join([d for d,_ in hits[:k]])
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', ctx) if s.strip()]
    if not sentences:
        return ("I found related material but could not extract a concise answer.", [])
    svecs = embed_texts(sentences)
    qvec = embed_texts([query])
    sims = cosine_sim(svecs, qvec).ravel()
    top_idx = np.argsort(-sims)[:5]
    chosen = [sentences[i] for i in top_idx if 0 <= i < len(sentences)]
    sources = []
    for _, m in hits[:k]:
        src = m.get("source","local")
        if src not in sources:
            sources.append(src)
    cite_str = " ".join(f"[{i+1}: {s}]" for i, s in enumerate(sources, start=1))
    answer = (" ".join(chosen) or "I found related material but could not extract a concise answer.") + f"\n\nSources: {cite_str}"
    return answer, [{"source": s} for s in sources]

# =========================
# Quiz (robust generator)
# =========================

# Keep sentences in a sensible range
_SENT_MIN, _SENT_MAX = 55, 200
_WORDS_MIN = 10

# Domain vocabulary for MCQs (mask one of these if present)
SEC_TERMS = [
    # concepts
    "firewall","proxy","vpn","ids","ips","waf","nat","segmentation","zero trust",
    "encryption","decryption","cipher","key","nonce","salt","handshake","certificate",
    "authentication","authorization","accounting","auditing","integrity","availability","confidentiality",
    "hash","mac","signature","tls","ssl","https","ipsec","ssh","kerberos","saml","oauth",
    "ddos","dos","phishing","malware","ransomware","botnet","mitm","replay",
    "sandbox","honeypot","siem","soar","edr","xdr","antivirus","whitelisting","blacklisting",
    "aaa","radius","tacacs","bastion","dmz","subnet","vlan","qos","spoofing"
]

SEC_KEYWORDS = set([
    "security","secure","attack","attacks","threat","risk","firewall","vpn","ids","ips","waf",
    "encryption","cipher","key","certificate","tls","https","ipsec","ssh",
    "authentication","authorization","integrity","availability","confidentiality","hash","mac",
    "malware","phishing","ddos","mitm","proxy","segmentation","dmz","siem","edr","xdr"
])

def _normalize(text: str) -> str:
    # squash newlines, fix OCR leftovers like "1We", de-hyphenate broken words
    t = text.replace("\n", " ")
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)             # hyphen line break
    t = re.sub(r"\b\d+(?=[A-Za-z])", "", t)             # "1We" -> "We"
    t = t.replace("\u2013", "-").replace("\u2014", "-")  # dashes
    return t

def _has_verb(s: str) -> bool:
    # heuristic: sentence contains a common verb/aux
    return bool(re.search(r"\b(is|are|was|were|be|being|been|has|have|had|can|could|should|would|may|might|must|do|does|did|provide|use|include|supports?)\b", s, flags=re.I))

def _contains_keyword(s: str) -> bool:
    return any(k in s.lower() for k in SEC_KEYWORDS)

def _clean_sentences(text: str) -> List[str]:
    """Split and filter to avoid headings, tables, fragments, etc."""
    text = _normalize(text)
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text)]
    out = []
    for s in sents:
        if not s:
            continue
        # drop headings/labels/figures/tables/bullets
        if s.startswith(("#","*","-")): 
            continue
        if re.match(r"^(table|figure|fig\.|chapter|section)\b", s, flags=re.I):
            continue
        if re.match(r"^\d+[\).\- ]", s):  # numbered bullets
            continue
        if len(s) < _SENT_MIN or len(s) > _SENT_MAX:
            continue
        if not _has_verb(s):
            continue
        if not _contains_keyword(s):
            continue
        out.append(s)
    return out

def _extract_terms_from_sentence(s: str) -> List[str]:
    lower = s.lower()
    return [t for t in SEC_TERMS if t in lower]

def _distinct_opts(correct: str, pool: List[str]) -> List[str]:
    """3 unique, domain-relevant distractors; ensure 4 total options."""
    seen = {correct.lower()}
    distractors = []
    for cand in pool:
        if cand.lower() in seen: 
            continue
        if cand.lower() == correct.lower():
            continue
        if len(cand.split()) > 3:  # keep short
            continue
        distractors.append(cand)
        seen.add(cand.lower())
        if len(distractors) == 3:
            break
    # fill with generic domain terms if needed
    fallback = ["firewall","vpn","ids","ips","tls","hash","cipher","nonce","dmz","proxy","waf"]
    for f in fallback:
        if len(distractors) == 3: break
        if f.lower() not in seen:
            distractors.append(f); seen.add(f.lower())
    opts = [correct] + distractors[:3]
    # guarantee uniqueness and shuffle
    opts = list(dict.fromkeys(opts))
    while len(opts) < 4:
        extra = random.choice(fallback)
        if extra.lower() not in {o.lower() for o in opts}:
            opts.append(extra)
    random.shuffle(opts)
    # capitalise acronyms nicely
    def nice(o: str) -> str:
        return o.upper() if o.isalpha() and len(o) <= 4 else o
    return [nice(o) for o in opts]

def _pick_mask_span(sentence: str) -> Tuple[str, str]:
    """Prefer masking a known security term; otherwise return (None, None)."""
    terms = _extract_terms_from_sentence(sentence)
    if not terms:
        return None, None
    correct = random.choice(terms)
    # Replace only one occurrence (case-insensitive)
    pattern = re.compile(re.escape(correct), re.I)
    stem = pattern.sub("_____", sentence, count=1)
    # Avoid leading placeholder or ending with blank punctuation
    return correct, stem

def _negate_sentence(s: str) -> str:
    """Create a readable false variant occasionally (optional)."""
    m = re.search(r"\b(is|are|was|were|can|could|should|would|do|does|did|has|have|had)\b", s, re.I)
    if m:
        i = m.end()
        return s[:i] + " not" + s[i:]
    return "It is not true that " + s[0].lower() + s[1:]

def generate_quiz(topic: str = "", n: int = 5) -> Dict[str, Any]:
    """Balanced quiz with valid TF/MCQ/Open; per-question sources; no junk options."""
    query = topic if topic else "network security"
    hits = retrieve(query, k=max(16, n*5))
    if not hits:
        return {"topic": topic or "general", "items": []}

    per_source, global_text = [], []
    for doc, meta in hits:
        source = meta.get("source","local")
        sents = _clean_sentences(doc)
        if sents:
            per_source.append((source, sents))
            global_text.append(doc)
    if not per_source:
        return {"topic": topic or "general", "items": []}

    # distractor pool: unique, domain-relevant terms seen in the corpus + SEC_TERMS
    corpus_terms = set()
    for _, sents in per_source:
        for s in sents:
            corpus_terms.update(_extract_terms_from_sentence(s))
    pool = list(dict.fromkeys(list(corpus_terms) + SEC_TERMS))

    rr = itertools.cycle(range(len(per_source)))  # diversify sources
    items, seen = [], set()

    while len(items) < n and len(seen) < 500:
        sidx = next(rr)
        source, sents = per_source[sidx]
        s = random.choice(sents)
        if s in seen:
            continue
        seen.add(s)

        tmod = len(items) % 3  # rotate types: tf, mcq, open

        if tmod == 0:
            # 80% true, 20% readable false
            make_true = random.random() < 0.8
            qtext = s if make_true else _negate_sentence(s)
            items.append({"type":"tf","q": qtext,"answer": make_true,"sources":[source]})

        elif tmod == 1:
            correct, stem = _pick_mask_span(s)
            if not correct or not stem:
                # fallback to TF to avoid junk MCQ
                items.append({"type":"tf","q": s,"answer": True,"sources":[source]})
                continue
            options = _distinct_opts(correct, pool)
            
            if correct not in options:
                options[0] = correct
                random.shuffle(options)
            items.append({
                "type":"mcq",
                "q": stem,
                "options": options,
                "answer": correct.upper() if correct.isalpha() and len(correct)<=4 else correct,
                "sources":[source]
            })

        else:
            items.append({
                "type":"open",
                "q": f"Briefly explain: {s}",
                "answer": s,
                "sources":[source]
            })

    return {"topic": topic or "general", "items": items[:n]}

# =========================
# Grader
# =========================
def grade_quiz(items: List[Dict[str, Any]], responses: List[Any]) -> Dict[str, Any]:
    score = 0
    details = []
    for it, resp in zip(items, responses):
        correct = False
        rationale = ""
        if it["type"] == "tf":
            correct = (resp is not None) and (bool(resp) == bool(it["answer"]))
            rationale = "True/False comparison"
        elif it["type"] == "mcq":
            # normalise short acronyms to match (TLS, IDS, IPS etc.)
            gold = it.get("answer","")
            mine = resp if resp is not None else ""
            if gold.isalpha() and len(gold) <= 4:
                gold = gold.upper()
                mine = str(mine).upper()
            correct = (str(mine).strip() == str(gold).strip())
            rationale = "Exact option match"
        else:
            ref = it.get("answer","")
            if resp is None or str(resp).strip() == "":
                sim = 0.0
            else:
                sim = float(cosine_sim(embed_texts([ref]), embed_texts([str(resp)])).ravel()[0])
            correct = sim >= 0.45
            rationale = f"Semantic similarity {sim:.2f} (threshold 0.58)"
        score += 1 if correct else 0
        details.append({
            "question": it["q"],
            "your_answer": resp,
            "expected": it.get("answer",""),
            "correct": correct,
            "sources": it.get("sources",[]),
            "rationale": rationale
        })
    return {"score": score, "total": len(items), "details": details}
