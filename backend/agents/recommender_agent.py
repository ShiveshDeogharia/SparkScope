"""
recommender_agent.py  •  SparkScope
-------------------------------------------------
Minimal Retrieval‑Augmented Generation (RAG) agent
to suggest emission‑reduction tactics drawn from
Walmart Project Gigaton™ playbooks.

✦ Dependencies (add to requirements.txt)
    langchain>=0.2
    faiss-cpu
    sentence-transformers
    openai   # only if you switch to ChatOpenAI
"""

from pathlib import Path
from typing import List, Union

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI   # ‑‑> swap out if offline
from langchain.chains import RetrievalQA
from langchain.schema import Document


# ---------- 1. Load playbook documents ----------
def load_documents(source_dir: Union[str, Path] = "backend/data/playbooks") -> List[Document]:
    """
    Reads every .txt or .md file in source_dir and returns
    a list of LangChain Document objects.
    (Convert PDFs to .txt upfront for the MVP.)
    """
    docs: List[Document] = []
    source_dir = Path(source_dir)
    for path in source_dir.glob("*.[tm][dx]t"):          # .txt or .md
        text = path.read_text(encoding="utf-8", errors="ignore")
        docs.append(Document(page_content=text, metadata={"source": path.name}))
    return docs


# ---------- 2. Build or load a FAISS vector store ----------
def build_vector_store(docs: List[Document]) -> FAISS:
    """
    Splits docs into chunks, embeds them, and returns an in‑memory FAISS store.
    For hackathon speed we rebuild each run; you can pickle later.
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_documents(chunks, embeddings)


# ---------- 3. Get recommendations ----------
def get_recommendations(
    query: str,
    supplier_profile: str = "",
    k: int = 3,
    temperature: float = 0.2,
) -> str:
    """
    Returns a bullet‑point answer with up to k actionable suggestions.
    supplier_profile can be any context (industry, size, badge level, etc.).
    """

    # (a) vector store
    docs = load_documents()
    vectordb = build_vector_store(docs)
    retriever = vectordb.as_retriever(search_kwargs={"k": k})

    # (b) LLM (swap to Ollama/Local if you prefer)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=temperature)

    # (c) Retrieval‑QA chain
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=False,
    )

    prompt = (
        f"{supplier_profile}\n\n"
        f"Supplier question: {query}\n\n"
        f"Answer with {k} concise, actionable bullet points."
    )
    return chain.run(prompt)


# ---------- 4. Quick CLI test ----------
if __name__ == "__main__":
    demo_profile = "Small apparel supplier, Bronze badge, wants to cut packaging emissions."
    demo_query = "How can we reduce packaging emissions quickly?"
    print(get_recommendations(demo_query, demo_profile))
