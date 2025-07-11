from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import RetrievalQA

from transformers import pipeline

# Load FAISS vectorstore
INDEX_DIR = Path(__file__).resolve().parents[2] / "faiss_index"
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = FAISS.load_local(
    str(INDEX_DIR),
    embeddings,
    allow_dangerous_deserialization=True
)

# Load local model pipeline
local_pipeline = pipeline(
    task="text2text-generation",
    model="google/flan-t5-base",
    max_length=256,
    temperature=0.3
)
llm = HuggingFacePipeline(pipeline=local_pipeline)

def get_recommendations(user_query: str, topic: str = None) -> list:
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""
You are a sustainability expert. Based on the following context, give 3 clear and actionable tips to reduce emissions.

Context:
{context}

User query: {question}

Tips:
- 
- 
- 
"""
    )

    qa_chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)

    chain = RetrievalQA(
        retriever=retriever,
        combine_documents_chain=qa_chain,
        return_source_documents=False
    )

    response = chain.run({"query": user_query})
    suggestions = [s.strip("-• ") for s in response.strip().split("\n") if s.strip()]
    return suggestions[:3]
