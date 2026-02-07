
import re
import pathlib
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document




def load_and_chunk_documents(data_dir: str = "data/txt_files_med_test") -> list[Document]:
    """
    Loads .txt files from the specified directory and splits them into chunks.
    
    Args:
        data_dir (str): Relative path to the directory containing text files.
        
    Returns:
        list[Document]: A list of LangChain Document objects ready for embedding.
    """
    
    # 1. Setup Pathlib for OS-agnostic path handling
    # This automatically handles Windows ('\') vs Mac/Linux ('/') backslashes
    path = pathlib.Path(data_dir)
    
    if not path.exists():
        raise FileNotFoundError(f"The directory '{path}' does not exist. Please create it and add .txt files.")
    
    documents = []
    
    # 2. Define the Splitter
    # 1000/200 is a standard "Goldilocks" zone for keeping context intact
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    
    print(f"📂 Scanning directory: {path.resolve()}")

    # 3. Iterate through all .txt files
    for file_path in path.glob("*.txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
            
            # Skip empty files
            if not text_content.strip():
                print(f"⚠️  Skipping empty file: {file_path.name}")
                continue

            # 4. Create Documents and Split
            # We explicitly add the 'source' metadata so we know which file came from where
            #TODO update to tag fy, quarter etc
            raw_doc = Document(
                page_content=text_content,
                metadata={"source": file_path.name} 
            )
            
            # Split the single large document into smaller chunks
            chunks = splitter.split_documents([raw_doc])
            documents.extend(chunks)
            
            print(f"✅ Loaded {file_path.name}: {len(chunks)} chunks created.")
            
        except Exception as e:
            print(f"❌ Error loading {file_path.name}: {e}")

    return documents

def load_and_chunk_documents_MD_tagging(data_dir: str) -> list[Document]:
    """
    Loads .txt files from the specified directory and splits them into chunks
    with enriched metadata tags.
    """
    
    # 1. Setup Pathlib
    path = pathlib.Path(data_dir)
    
    if not path.exists():
        raise FileNotFoundError(f"The directory '{path}' does not exist.")
    
    documents = []
    
    # 2. Define the Splitter
    # Keeping your larger chunk settings to prevent context fragmentation
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=400,
        length_function=len,
        separators=["\n\n", "\n", ".", " "],
        is_separator_regex=False,
    )
    
    print(f"📂 Scanning directory: {path.resolve()}")

    # 3. Iterate through all .txt files
    for file_path in path.glob("*.txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
            
            if not text_content.strip():
                print(f"⚠️  Skipping empty file: {file_path.name}")
                continue

            # --- NEW METADATA ENRICHMENT LOGIC ---
            # We look at the first 1000 chars to identify the company/date
            header_text = text_content[:1000]
            
            # Default metadata
            meta = {"source": file_path.name}
            
            # A. Detect Company
            if "Apex Technologies" in header_text:
                meta["company"] = "Apex Technologies"
                meta["ticker"] = "APX"
            elif "GreenField Power" in header_text:
                meta["company"] = "GreenField Power"
                meta["ticker"] = "GPWR"
            elif "OmniMarkets" in header_text:
                meta["company"] = "OmniMarkets Global Group"
                meta["ticker"] = "OMG"
            else:
                meta["company"] = "Unknown"
            
            # B. Detect Year (looks for 2024, 2025, etc.)
            year_match = re.search(r"\b(202[4-9])\b", header_text)
            if year_match:
                meta["year"] = year_match.group(1)
            
            # C. Detect Doc Type
            if "Quarterly" in header_text or "10-Q" in header_text:
                meta["doc_type"] = "10-Q"
            elif "Annual" in header_text or "10-K" in header_text:
                meta["doc_type"] = "10-K"
            
            # -------------------------------------

            # 4. Create Document with Rich Metadata
            # The splitter will automatically copy this metadata to every chunk!
            raw_doc = Document(
                page_content=text_content,
                metadata=meta
            )
            
            # Split the single large document into smaller chunks
            chunks = splitter.split_documents([raw_doc])
            
            documents.extend(chunks)
            
            print(f"✅ Loaded {file_path.name}: {len(chunks)} chunks. Tags: {meta}")
            
        except Exception as e:
            print(f"❌ Error loading {file_path.name}: {e}")

    return documents



# --- TICKET TEST BLOCK ---

if __name__ == "__main__":
    print("🧪 STARTING TEST: Document Ingestion Pipeline\n")
    
    # 1. Setup Test Environment
    test_dir = pathlib.Path("data/txt_files_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Create Dummy Files for Testing
    dummy_data = {
        "apple_test.txt": "Apple Inc. reported revenue of $50B. The CEO is Tim Cook. Risks include supply chain issues.",
        "tesla_test.txt": "Tesla reported revenue of $25B. The CEO is Elon Musk. Risks include regulatory changes." * 50, # Long file to test splitting
        "empty_test.txt": ""
    }
    
    for filename, content in dummy_data.items():
        with open(test_dir / filename, "w", encoding="utf-8") as f:
            f.write(content)
            
    # 3. Run the Function
    try:
        final_docs = load_and_chunk_documents(str(test_dir))
        
        for i, doc in enumerate(final_docs):
             print(f"--- Document {i+1} ---")
             print(f"Content: {doc.page_content[:200]}...") # Print a snippet of the content
             print(f"Metadata: {doc.metadata}")
        
        # 4. Verification
        print(f"\n📊 TEST RESULTS:")
        print(f"   Total Chunks Generated: {len(final_docs)}")
        
        if len(final_docs) > 0:
            print(f"   Sample Chunk: '{final_docs[0].page_content[:50]}...'")
            print(f"   Metadata: {final_docs[0].metadata}")
            print("\n✅ TICKET COMPLETE: Function returns valid Document objects.")
        else:
            print("\n❌ FAILURE: No documents returned.")
            
    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE: {e}")