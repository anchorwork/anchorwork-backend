import os
import openai
import faiss
import pickle
from tqdm import tqdm
import tiktoken

EMBED_MODEL = "text-embedding-3-small"  # Or your preferred model
ROOT_DIR = "clean_md"
VSTORE_PATH = "anchorwork_vector_store.faiss"
META_PATH = "anchorwork_vector_store_meta.pkl"
CHUNK_SIZE = 2000  # Number of tokens per chunk (adjust as needed)

openai.api_key = os.getenv("OPENAI_API_KEY")

def load_docs(root_dir):
    docs, paths = [], []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.md'):
                fpath = os.path.join(subdir, file)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                    docs.append(content)
                    paths.append(fpath)
    return docs, paths

def chunk_text(text, chunk_size=CHUNK_SIZE):
    # Uses tiktoken to count tokens; splits by word boundaries
    enc = tiktoken.encoding_for_model(EMBED_MODEL)
    words = text.split()
    chunks = []
    cur_chunk = []
    cur_count = 0
    for word in words:
        token_count = len(enc.encode(word + ' '))
        if cur_count + token_count > chunk_size:
            chunks.append(' '.join(cur_chunk))
            cur_chunk = []
            cur_count = 0
        cur_chunk.append(word)
        cur_count += token_count
    if cur_chunk:
        chunks.append(' '.join(cur_chunk))
    return chunks

def embed_texts(texts, batch_size=16):
    vectors = []
    metadata = []
    for doc_idx, text in tqdm(list(enumerate(texts)), desc="Chunking and Embedding"):
        doc_chunks = chunk_text(text)
        for chunk_idx, chunk in enumerate(doc_chunks):
            # Safety: skip empty chunks
            if not chunk.strip():
                continue
            response = openai.embeddings.create(
                input=[chunk],
                model=EMBED_MODEL
            )
            vectors.append(response.data[0].embedding)
            metadata.append({"doc_idx": doc_idx, "chunk_idx": chunk_idx, "chunk": chunk[:100] + "..."} )
    return vectors, metadata

def main():
    print(f"Scanning {ROOT_DIR} for .md files...")
    docs, paths = load_docs(ROOT_DIR)
    print(f"Found {len(docs)} documents.")

    print("Creating embeddings with chunking...")
    vectors, meta = embed_texts(docs)

    print("Saving FAISS index and metadata...")
    import numpy as np
    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors).astype('float32'))

    faiss.write_index(index, VSTORE_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump({"paths": paths, "meta": meta}, f)

    print(f"\nVector store created!")
    print(f"Index: {VSTORE_PATH}")
    print(f"Metadata: {META_PATH}")
    print(f"Vector store ID (for .env): anchorwork_vector_store")

if __name__ == "__main__":
    main()