from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts):
    """Generate embeddings for a list of texts."""
    return np.array(model.encode(texts, show_progress_bar=True))

def cosine_sim(a, b):
    """Compute cosine similarity between two vectors or matrices."""
    if len(a.shape) == 1:
        a = a.reshape(1, -1)
    if len(b.shape) == 1:
        b = b.reshape(1, -1)
    return np.dot(a, b.T) / (np.linalg.norm(a, axis=1, keepdims=True) * np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)