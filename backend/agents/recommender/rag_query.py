# backend/agents/recommender/rag_query.py

from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

INDEX_DIR = Path(__file__).resolve().parents[2] / "faiss_index"

# Load the same embedding model used during indexing
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def get_recommendations(query: str, k: int = 3) -> list[str]:
    """
    Search the FAISS index for relevant documents based on a user query.
    Returns the top `k` text chunks.
    """
    # Load the index
    vectorstore = FAISS.load_local(str(INDEX_DIR), embeddings, allow_dangerous_deserialization=True)

    # Search the index
    docs = vectorstore.similarity_search(query, k=k)

    return [doc.page_content for doc in docs]


# ✅ Test it standalone
if __name__ == "__main__":
    sample_query = "How do I reduce packaging emissions?"
    results = get_recommendations(sample_query)
    print("🔍 Recommendations:")
    for i, text in enumerate(results, 1):
        print(f"\n--- Result {i} ---\n{text}")
