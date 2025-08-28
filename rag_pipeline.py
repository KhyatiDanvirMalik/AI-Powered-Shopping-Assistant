import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Prefer maintained Chroma package; fall back if unavailable
try:
    from langchain_chroma import Chroma  # pip install langchain-chroma
    _CHROMA_IMPORT = "langchain_chroma.Chroma"
except Exception:
    from langchain_community.vectorstores import Chroma
    _CHROMA_IMPORT = "langchain_community.vectorstores.Chroma"

ROOT = Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT / ".env")
if not os.getenv("GOOGLE_API_KEY"):
    load_dotenv(dotenv_path=ROOT.parent / ".env")

CSV_FILE_PATH = ROOT / "products.csv"
DB_PATH = ROOT / "chroma_db"
COLLECTION_NAME = "products"

def build_vector_store():
    """Build (or rebuild) the Chroma vector DB from products.csv."""
    if not CSV_FILE_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_FILE_PATH}")

    # sanity check CSV readable
    _ = pd.read_csv(CSV_FILE_PATH, nrows=3)

    loader = CSVLoader(file_path=str(CSV_FILE_PATH), csv_args={"delimiter": ",", "quotechar": '"'})
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=100,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
    )
    chunks = splitter.split_documents(docs)

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(DB_PATH),
        collection_name=COLLECTION_NAME,
    )

    # Chroma >=0.5 persists automatically when using PersistentClient.
    # Older versions expose .persist(); call it only if present.
    if hasattr(vectordb, "persist"):
        try:
            vectordb.persist()
        except Exception:
            pass

    print(f"✔ Built vector store using {_CHROMA_IMPORT}")
    print(f"✔ Persist dir : {DB_PATH}")
    print(f"✔ Chunks      : {len(chunks)}")

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY not found. Create a .env with GOOGLE_API_KEY=...")
    build_vector_store()
