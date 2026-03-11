from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.schema import Document


# ============================================================================
# RAG ARCHITECT — Layer 2: Hybrid Retrieval (BM25 + Vectors + MMR)
# ============================================================================
#
# In Layer 1 you fixed the QUERY (Rewrite + HyDE + MultiQuery).
# In Layer 2 you fix the RETRIEVAL ENGINE itself.
#
# Problem with pure vector search:
#   - Great at semantic similarity
#   - Weak at exact keywords, rare entities, and "did you index this exact phrase?"
#
# Problem with pure keyword/BM25 search:
#   - Great at exact term matching, synonyms (via tokenization)
#   - Weak at semantic similarity and paraphrases
#
# Solution: HYBRID RETRIEVAL
#   - Combine a keyword retriever (BM25) with a vector retriever (embeddings)
#   - Optionally add MMR (Maximal Marginal Relevance) to reduce redundancy
#
# This script walks through:
#   Step 1: Baseline — pure vector search recap
#   Step 2: BM25 keyword retrieval
#   Step 3: Hybrid fusion with EnsembleRetriever
#   Step 4: MMR vs plain similarity search
#   Step 5: Putting it together — Hybrid + MMR tradeoffs
# ============================================================================


# ============================================================================
# Shared Demo Dataset (same as Layer 1)
# ============================================================================

documents = [
    Document(
        page_content=(
            "Sam Altman co-founded OpenAI in December 2015 alongside Elon Musk, "
            "Greg Brockman, Ilya Sutskever, Wojciech Zaremski, and John Schulman. "
            "The organization was initially established as a non-profit AI research lab."
        ),
        metadata={"source": "ai_companies.txt", "topic": "openai"},
    ),
    Document(
        page_content=(
            "Anthropic was founded in 2021 by Dario Amodei and Daniela Amodei, "
            "along with several former OpenAI researchers. The company focuses on AI safety "
            "and developed the Claude family of large language models."
        ),
        metadata={"source": "ai_companies.txt", "topic": "anthropic"},
    ),
    Document(
        page_content=(
            "OpenAI released ChatGPT on November 30, 2022. It reached 100 million "
            "users within two months, making it the fastest-growing consumer application "
            "in history at that time."
        ),
        metadata={"source": "ai_companies.txt", "topic": "chatgpt"},
    ),
    Document(
        page_content=(
            "Google DeepMind was formed in April 2023 by merging Google Brain and "
            "DeepMind. Demis Hassabis leads the combined organization. They developed "
            "AlphaFold, which solved protein structure prediction."
        ),
        metadata={"source": "ai_companies.txt", "topic": "deepmind"},
    ),
    Document(
        page_content=(
            "Meta AI, led by Yann LeCun, released the LLaMA family of open-source "
            "large language models. LLaMA 2 was released in July 2023 and made available "
            "for commercial use, shifting the industry toward open-weight models."
        ),
        metadata={"source": "ai_companies.txt", "topic": "meta"},
    ),
    Document(
        page_content=(
            "The transformer architecture was introduced in the 2017 paper "
            "'Attention Is All You Need' by Vaswani et al. at Google. This architecture "
            "became the foundation for all modern large language models including GPT, "
            "Claude, and LLaMA."
        ),
        metadata={"source": "ai_history.txt", "topic": "transformers"},
    ),
]


embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(documents, embeddings)


# ============================================================================
# STEP 1: Baseline — Pure Vector Retrieval (Recap)
# ============================================================================

vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

print("=" * 70)
print("STEP 1: Baseline — Pure Vector Retrieval (recap)")
print("=" * 70)

baseline_queries = [
    "Altman's company?",
    "that Google AI thing that folded proteins",
    "open source llama models",
]

for query in baseline_queries:
    results = vector_retriever.invoke(query)
    print(f"\nQuery: {query}")
    for i, doc in enumerate(results, 1):
        print(f"  Vec {i}: [{doc.metadata.get('topic')}] {doc.page_content[:80]}...")

print()


# ============================================================================
# STEP 2: BM25 — Keyword / Sparse Retrieval
# ============================================================================
#
# BM25 works on token frequencies:
#   - It loves exact matches: names, acronyms, product names, legal clauses, IDs.
#   - It does NOT understand meaning beyond terms.
#
# In LangChain, BM25Retriever is an in-memory, no-dependency sparse retriever
# perfect for prototyping hybrid pipelines.

bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 3

print("=" * 70)
print("STEP 2: BM25 Keyword Retrieval")
print("=" * 70)

for query in baseline_queries:
    results = bm25_retriever.invoke(query)
    print(f"\nQuery: {query}")
    for i, doc in enumerate(results, 1):
        print(f"  BM25 {i}: [{doc.metadata.get('topic')}] {doc.page_content[:80]}...")

print()


# ============================================================================
# STEP 3: Hybrid Retrieval — BM25 + Vectors with EnsembleRetriever
# ============================================================================
#
# EnsembleRetriever:
#   - Takes multiple retrievers (e.g., BM25 + vector)
#   - Scores each document from each retriever
#   - Normalizes scores and combines them (default: weighted average)
#   - Returns a single ranked list
#
# This gives you:
#   - The semantic power of vectors
#   - The exact match strength of BM25

hybrid_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.5, 0.5],  # tune this: tilt toward BM25 or vectors
)

print("=" * 70)
print("STEP 3: Hybrid Retrieval — BM25 + Vectors")
print("=" * 70)

for query in baseline_queries:
    results = hybrid_retriever.invoke(query)
    print(f"\nQuery: {query}")
    for i, doc in enumerate(results, 1):
        print(f"  Hybrid {i}: [{doc.metadata.get('topic')}] {doc.page_content[:80]}...")

print()


# ============================================================================
# STEP 4: MMR — Maximal Marginal Relevance on the Vector Side
# ============================================================================
#
# Problem: Plain similarity search returns redundant chunks:
#   - Top 3 results might all be about the SAME paragraph.
#   - You waste context window on near-duplicates.
#
# MMR trades a bit of similarity for diversity:
#   - Still relevant to the query
#   - But encourages covering different aspects / topics

mmr_retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,
        "lambda_mult": 0.5,  # 0.0 = max diversity, 1.0 = max similarity
    },
)

print("=" * 70)
print("STEP 4: MMR — Diverse Vector Retrieval")
print("=" * 70)

mmr_queries = [
    "history of modern AI models",
    "major AI labs and what they did",
]

for query in mmr_queries:
    print(f"\nQuery: {query}")
    sim_results = vector_retriever.invoke(query)
    mmr_results = mmr_retriever.invoke(query)

    print("  Plain similarity:")
    for i, doc in enumerate(sim_results, 1):
        print(f"    Sim {i}: [{doc.metadata.get('topic')}] {doc.page_content[:80]}...")

    print("  MMR (more diverse):")
    for i, doc in enumerate(mmr_results, 1):
        print(f"    MMR {i}: [{doc.metadata.get('topic')}] {doc.page_content[:80]}...")

print()


# ============================================================================
# STEP 5: Putting It Together — When to Use What
# ============================================================================
#
# In a production stack, you typically:
#   - Use HYBRID retrieval as your default retriever:
#       hybrid = EnsembleRetriever([bm25, vector], weights=[w_bm25, w_vec])
#   - Optionally use MMR on the vector side BEFORE fusion
#       mmr_vec = vectorstore.as_retriever(search_type="mmr", ...)
#       hybrid = EnsembleRetriever([bm25, mmr_vec], ...)
#   - Tune weights and k using evaluation metrics (Layer 5)
#
# Here we just show the combined hybrid+MMR pattern so you see the shape.

mmr_vector_retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "lambda_mult": 0.5},
)

hybrid_mmr_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, mmr_vector_retriever],
    weights=[0.4, 0.6],
)

print("=" * 70)
print("STEP 5: Combined — Hybrid (BM25 + MMR Vector)")
print("=" * 70)

final_queries = [
    "How has AI leadership changed?",
    "Tell me about open-source AI model families",
]

for query in final_queries:
    results = hybrid_mmr_retriever.invoke(query)
    print(f"\nQuery: {query}")
    print(f"  Documents retrieved: {len(results)}")
    for i, doc in enumerate(results, 1):
        print(f"    {i}. [{doc.metadata.get('topic')}] {doc.page_content[:80]}...")

print()
print("=" * 70)
print("LAYER 2 COMPLETE — You now understand Hybrid Retrieval!")
print("=" * 70)
print(
    """
Summary of what you learned:

  1. Pure vector retrieval is great for semantics but can miss exact terms.
  2. BM25 keyword retrieval is great for exact matches but misses paraphrases.
  3. Hybrid retrieval (BM25 + vectors) gives you the best of both worlds.
  4. MMR reduces redundancy and increases diversity in retrieved docs.
  5. You can combine BM25 + MMR vectors and tune weights for your domain.

Next up: Layer 3 — Post-Retrieval Intelligence (Reranking + Compression)
"""
)

