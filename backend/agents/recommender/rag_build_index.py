from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader

import os
from dotenv import load_dotenv
load_dotenv()


DATA_DIR = Path(__file__).resolve().parents[3] / "recommender_data"
INDEX_DIR = Path(__file__).resolve().parents[2] / "faiss_index"

def build_faiss_index():
    print(f"📂 Loading text files from: {DATA_DIR}")

    # 1. Load all .txt files
    loaders = [
        TextLoader(str(file), encoding="utf-8")
        for file in DATA_DIR.glob("*.txt")
    ]
    documents = []
    for loader in loaders:
        documents.extend(loader.load())

    print(f"📄 Loaded {len(documents)} documents")

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    print(f"🧩 Split into {len(chunks)} chunks")

    # 3. Embed + index
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # 4. Save index
    vectorstore.save_local(str(INDEX_DIR))
    print(f"✅ FAISS index saved to: {INDEX_DIR}")

if __name__ == "__main__":
    build_faiss_index()
