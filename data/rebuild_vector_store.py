#!/usr/bin/env python3
"""
Rebuilds anchorwork_vector_store.faiss + anchorwork_vector_store_meta.pkl
so the index and metadata list are perfectly in sync.

• Embeds every file matching SOURCE_GLOB patterns
• Supports .py, .md, .txt, and .pdf (requires pypdf)
• Uses OpenAI text-embedding-3-small
"""

import os, pathlib, pickle, textwrap, tqdm, openai, numpy as np, faiss

# ── configuration ──────────────────────────────────────────────────
EMBED_MODEL = "text-embedding-3-small"

SOURCE_GLOB = [
    # backend code
    "src/**/*.py",
    "routes/**/*.py",

    # documentation
    "docs/**/*.md",
    "*.md",

    # guides (folder from your screenshot)
    "Guides/**/*.md",

    # everything inside data/clean/  (any extension)
    "data/clean/**/*"
]

VEC_PATH  = "data/anchorwork_vector_store.faiss"
META_PATH = "data/anchorwork_vector_store_meta.pkl"

# ── helper for PDF (optional) ──────────────────────────────────────
def extract_text(path: pathlib.Path) -> str:
    """Return plain text from given file. Supports .pdf via pypdf."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            print(f"⚠️  PDF extract failed for {path.name}: {e}")
            return ""
    # treat everything else as text
    return path.read_text(encoding="utf-8", errors="ignore")

# ── gather files ───────────────────────────────────────────────────
files = []
for pattern in SOURCE_GLOB:
    files.extend(pathlib.Path().glob(pattern))
files = [p for p in files if p.is_file()]

if not files:
    raise SystemExit("No files matched SOURCE_GLOB patterns.")

print(f"Embedding {len(files)} files with {EMBED_MODEL} …")

embeddings, meta = [], []
for p in tqdm.tqdm(files, unit="file"):
    text = extract_text(p)[:8192]        # truncate very large docs
    if not text.strip():
        continue                         # skip empty extracts
    vec  = openai.embeddings.create(model=EMBED_MODEL, input=[text]).data[0].embedding
    embeddings.append(vec)
    meta.append({
        "path": str(p),
        "preview": textwrap.shorten(text.replace('\n', ' '), 180)
    })

# ── build FAISS index (cosine via normalized vectors) ──────────────
arr = np.array(embeddings, dtype="float32")
faiss.normalize_L2(arr)
index = faiss.IndexFlatIP(arr.shape[1])
index.add(arr)

# ── write to disk ──────────────────────────────────────────────────
pathlib.Path("data").mkdir(exist_ok=True)
faiss.write_index(index, VEC_PATH)
pickle.dump(meta, open(META_PATH, "wb"))

print(f"✅  Rebuilt index ({index.ntotal} vectors) and metadata ({len(meta)} rows).")