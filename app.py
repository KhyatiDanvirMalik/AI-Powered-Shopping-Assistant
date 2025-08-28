import os
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# Prefer maintained Chroma, fall back if unavailable
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

DB_PATH = str(ROOT / "chroma_db")
COLLECTION_NAME = "products"

PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a helpful shopping assistant. Answer the user's question and act as a natural salesperson and greet customer if they greet you \\n"
        "If the answer is not in the context, say you don't have that information.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
)

def make_llm(model_name: str):
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.3,
        max_output_tokens=256,
        max_retries=2,
        timeout=60,
    )

def setup_rag():
    """Return (qa_chain, retriever) so fallback can reuse retriever."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 3})

    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    qa = RetrievalQA.from_chain_type(
        llm=make_llm(model_name),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT},
    )
    return qa, retriever

app = Flask(__name__, static_folder="static", template_folder="templates")
rag_chain, retriever = setup_rag()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"response": "Please enter a message."}), 200

    try:
        result = rag_chain.invoke({"query": user_message})
        answer = result.get("result") or "I couldn't generate an answer."
        return jsonify({"response": answer}), 200

    except Exception as e:
        msg = str(e)
        if "429" in msg or "ResourceExhausted" in msg or "quota" in msg.lower():
         
            try:
                fallback = make_llm("gemini-1.5-flash-8b")
                tmp_chain = RetrievalQA.from_chain_type(
                    llm=fallback,
                    chain_type="stuff",
                    retriever=retriever,
                    return_source_documents=False,
                    chain_type_kwargs={"prompt": PROMPT},
                )
                out = tmp_chain.invoke({"query": user_message})
                return jsonify({"response": out.get("result", "I'm currently rate-limited.")}), 200
            except Exception:
                pass
            return jsonify({
                "response": (
                    "I'm out of free quota for the selected model. "
                    "Switch to a lighter model (e.g., gemini-1.5-flash) or enable billing."
                )
            }), 200

        print("Server error:", e)
        return jsonify({"response": "Sorry, something went wrong while processing your request."}), 200

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY not found. Create a .env with GOOGLE_API_KEY=...")
    print(f"Using Chroma import: {_CHROMA_IMPORT}")
    app.run(debug=True)
