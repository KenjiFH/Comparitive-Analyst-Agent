# ingest_worker.py
import sys
import shutil
import pathlib
import os
import stat


from src.database import VectorDatabase
from src.ingestion import *

# CONSTANTS
DB_DIR = "test_chroma_db"
DATA_DIR = "data/txt_files_med_test" 

def remove_readonly(func, path, _):
    """Helper to force delete read-only files on Windows"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def main():
    print(f"⚙️ WORKER: Starting Ingestion Process...")
    
    # 1. DELETE EXISTING DB
    # Since this is a fresh process, we can aggressively delete the folder.
    db_path = pathlib.Path(DB_DIR)
    if db_path.exists():
        print(f"🧹 WORKER: Removing old database at {DB_DIR}...")
        try:
            shutil.rmtree(db_path, onerror=remove_readonly)
            print("   ✅ Old database removed.")
        except Exception as e:
            print(f"   ❌ Error removing DB: {e}")
            sys.exit(1)

    # 2. LOAD DOCUMENTS
    print(f"📂 WORKER: Loading docs from {DATA_DIR}...")
    try:
        raw_docs = load_and_chunk_documents(DATA_DIR)
        
        if not raw_docs:
            print("   ⚠️ No documents found. Exiting.")
            sys.exit(0)
            
        print(f"   found {len(raw_docs)} chunks.")

        # 3. EMBED & STORE
        # Initialize DB (creates new folder)
        print("🧠 WORKER: Embedding data (this may take a moment)...")
        vdb = VectorDatabase(persist_directory=DB_DIR)
        vdb.add_documents(raw_docs)
        print("   ✅ Embedding complete.")
        
    except Exception as e:
        print(f"   ❌ Critical Error in Worker: {e}")
        sys.exit(1)

    print("🏁 WORKER: Task Finished.")

if __name__ == "__main__":
    main()