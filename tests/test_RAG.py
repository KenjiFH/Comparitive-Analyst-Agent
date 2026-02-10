import os
import shutil
import pathlib
import re
from typing import List, Dict

# --- LIBRARIES ---

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- CONFIGURATION ---
DATA_DIR = "data/txt_files_med_test"  # <--- POINT THIS TO YOUR DATA FOLDER
DB_DIR = "tests/test_chroma_db_isolated"
MODEL_NAME = "llama3.2"
EMBEDDING_MODEL = "llama3.2" 

# ---------------------------------------------------------
# 1. VECTOR DATABASE CLASS (Simplified)
# ---------------------------------------------------------
class VectorDatabase:
    def __init__(self, persist_directory: str = DB_DIR):
        self.persist_directory = persist_directory
        self.embedding_function = OllamaEmbeddings(model=EMBEDDING_MODEL)
        
        # Initialize Client
        self.db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function
        )
        
    def add_documents(self, docs: List[Document]):
        """Ingest documents into the DB."""
        if not docs:
            print("⚠️ No documents to add.")
            return
        print(f"🧠 Embedding {len(docs)} chunks into ChromaDB...")
        self.db.add_documents(docs)
        print("✅ Data persisted.")

    def retrieve(self, query: str, k: int = 9, filter: dict = None) -> List[Document]:
        """Retrieve similar chunks."""
        print(f"🔎 Searching for: '{query}' (k={k})...")
        return self.db.similarity_search(query, k=k, filter=filter)
    
    def clear(self):
        """Nuclear option to wipe the DB."""
        if os.path.exists(self.persist_directory):
            try:
                shutil.rmtree(self.persist_directory)
                print("🧹 Database wiped clean.")
            except Exception as e:
                print(f"❌ Error wiping DB (File Lock?): {e}")

# ---------------------------------------------------------
# 2. INGESTION LOGIC (With Metadata Tagging)
# ---------------------------------------------------------
def load_and_chunk_documents(data_path: str) -> List[Document]:
    path = pathlib.Path(data_path)
    if not path.exists():
        print(f"❌ Data directory '{data_path}' not found.")
        return []

    documents = []
    
    # YOUR SETTINGS: Large chunks to keep "Forward Guidance" together
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,     # <--- Your setting
        chunk_overlap=400,   # <--- Your setting
        separators=["\n\n", "\n", ".", " "]
    )

    print(f"📂 Scanning {path}...")
    for file_path in path.glob("*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        # Basic Metadata Extraction (Regex)
        meta = {"source": file_path.name}
        
        # Simple Logic to tag the company for filtering
        if "Apex" in text: meta["company"] = "Apex Technologies"
        elif "GreenField" in text: meta["company"] = "GreenField Power"
        elif "Omni" in text: meta["company"] = "OmniMarkets Global Group"
        
        raw_doc = Document(page_content=text, metadata=meta)
        chunks = splitter.split_documents([raw_doc])
        documents.extend(chunks)
        print(f"   - Loaded {file_path.name}: {len(chunks)} chunks.")

    return documents

# ---------------------------------------------------------
# 3. ANALYST AGENT (The Brain)
# ---------------------------------------------------------
class AnalystAgent:
    def __init__(self, vector_db: VectorDatabase):
        self.db = vector_db
        # temperature=0 makes it strictly factual
        self.llm = OllamaLLM(model=MODEL_NAME, temperature=0)

    def analyze_company(self, company: str, fields: List[str]) -> dict:
        # 1. RETRIEVE
        # Note: We use the 'company' name as the query to get relevant docs
        # We perform a "Filtered" retrieval if we trusted our tags, but here we do raw search
        # to match your request.
        docs = self.db.retrieve(query=company, k=3) # <--- Your Requested K=9
        
        if not docs:
            return {f: "N/A" for f in fields}

        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 2. PROMPT
        field_list_str = "\n".join([f"- {f}" for f in fields])
        
        template = """
        You are an expert financial analyst. Extract the following fields for the company '{company}' 
        based ONLY on the context provided.

        Fields to Extract:
        {field_list}

        Context:
        {context}

        --- INSTRUCTIONS ---
        1. Return the output as a simple Python Dictionary string (JSON format).
        2. If a field is not found, use "N/A".
        3. Do NOT add any markdown formatting or explanation. Just the raw JSON string.
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        # 3. GENERATE
        print(f"🤖 Agent analyzing {company}...")
        response = chain.invoke({
            "company": company,
            "field_list": field_list_str,
            "context": context_text
        })
        
        # 4. PARSE (Simple cleanup)
        return response.strip()

# ---------------------------------------------------------
# 4. MAIN EXECUTION LOOP
# ---------------------------------------------------------
if __name__ == "__main__":
    # A. Setup
    print("--- 🚀 STARTING ISOLATED RAG TEST ---")
    
    # Initialize DB & Wipe it for a fresh test
    vdb = VectorDatabase()

    
    # B. Ingest
    docs = load_and_chunk_documents(DATA_DIR)
    if docs:
        vdb.add_documents(docs)
    else:
        print("❌ No docs found. Exiting.")
        exit()

    # C. Run Analysis
    agent = AnalystAgent(vdb)
    
    # Test Data
    target_company = "Apex Technologies" # Change this to test others
    target_fields = ["Revenue", "CEO", "Forward Guidance", "Primary Risks"]
    
    print(f"\n--- 📊 ANALYZING: {target_company} ---")
    result = agent.analyze_company(target_company, target_fields)
    
    print("\n--- ✅ FINAL OUTPUT ---")
    print(result)