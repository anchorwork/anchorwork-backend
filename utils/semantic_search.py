import openai
import numpy as np
import faiss
import pickle
import os
import logging
from typing import List, Union, Dict, Any

# ---- Configuration ----
EMBED_MODEL = "text-embedding-3-small"

# Absolute paths based on your setup, overridden by environment variables if set
VECTOR_PATH = os.getenv("VECTOR_PATH", "/Users/rebeccamorris/Desktop/anchorwork/data/anchorwork_vector_store.faiss")
META_PATH = os.getenv("META_PATH", "/Users/rebeccamorris/Desktop/anchorwork/data/anchorwork_vector_store_meta.pkl")

# ---- Load FAISS index and metadata ----
faiss_index = None
vector_meta = None

try:
    with open(META_PATH, "rb") as f:
        vector_meta = pickle.load(f)
except Exception as e:
    logging.warning(f"Failed to load metadata from {META_PATH}: {e}")

try:
    faiss_index = faiss.read_index(VECTOR_PATH)
except Exception as e:
    logging.warning(f"Failed to load FAISS index from {VECTOR_PATH}: {e}")

# ---- Embedding Function ----
def embed_query(text: str) -> np.ndarray:
    """
    Generate an embedding vector for the given text using OpenAI's embedding API.
    
    Args:
        text (str): The input text to embed.
        
    Returns:
        np.ndarray: The embedding vector as a numpy array of float32.
                    Returns a zero vector if embedding fails.
    """
    try:
        response = openai.embeddings.create(
            input=[text],
            model=EMBED_MODEL
        )
        # Convert to numpy array (float32) for FAISS
        return np.array(response.data[0].embedding, dtype="float32")
    except Exception as e:
        logging.warning(f"Embedding API call failed: {e}")
        # Return zero vector of appropriate size (assuming 1536 dim typical for OpenAI embeddings)
        return np.zeros(1536, dtype="float32")

# ---- Main Semantic Search ----
def semantic_search(query: str, k: int = 5) -> Union[List[Dict[str, Any]], str]:
    """
    Perform a semantic search over the FAISS index using the query.
    
    Args:
        query (str): The search query string.
        k (int): Number of top results to return.
        
    Returns:
        List[Dict[str, Any]]: List of metadata entries corresponding to top-k matches.
        str: User-friendly error message if index or metadata failed to load.
    """
    if faiss_index is None or vector_meta is None:
        return "Error: Vector index or metadata failed to load. Semantic search unavailable."
    
    # Embed the query
    query_vec = embed_query(query)
    # Search FAISS index for top-k similar vectors
    D, I = faiss_index.search(np.expand_dims(query_vec, axis=0), k)
    # Get matching metadata/results
    results = []
    for idx in I[0]:
        if idx < len(vector_meta):
            results.append(vector_meta[idx])
    return results

# ---- Example usage ----
if __name__ == "__main__":
    test_query = "What are the core principles of Anchorwork?"
    matches = semantic_search(test_query, k=3)
    print("Top matches:", matches)
