import shutil
import pathlib
from pathlib import Path
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

class VectorDatabase:
    """
    Manages the local vector store (ChromaDB) and embedding generation.
    """
    
    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Initialize the Vector Database.
        
        Args:
            persist_directory (str): Path where the vector vectors are saved to disk.
        """
        self.persist_directory = persist_directory
        
        # 1. Initialize the Embedding Model
        # Switched to 'mxbai-embed-large' as requested.
        # This model is currently State-of-the-Art (SOTA) for open-source embeddings.
        self.embedding_function = OllamaEmbeddings(
            model="mxbai-embed-large",
        )
        
        # 2. Initialize Chroma (The Vector Store)
        # This will create the folder 'chroma_db' in your project root if it doesn't exist.
        self.db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function
        )

    def add_documents(self, documents: list[Document]):
        """
        Embeds and saves a list of Documents to the database.
        """
        if not documents:
            print("⚠️  No documents provided to add.")
            return

        print(f"📥 Adding {len(documents)} documents to ChromaDB...")
        
        # Chroma handles the batching and embedding automatically here
        self.db.add_documents(documents)
        
        print("✅ Documents indexed successfully.")

    def retrieve(self, query: str, k: int = 3) -> list[Document]:
        """
        Performs semantic search for the query.
        
        Args:
            query (str): The question or topic to search for.
            k (int): Number of matching chunks to return.
            
        Returns:
            list[Document]: The most relevant text chunks.
        """
        print(f"🔎 Searching for: '{query}'")
        
        # similarity_search returns the raw documents
        results = self.db.similarity_search(query, k=k)
        
        return results

           
    def create_txt_file_test(self,file_path) -> str:
      

        file_content_string = ""

        try:
            file_content_string = Path(file_path).read_text()
            
            print("File content successfully read into a string using pathlib:")
            #print(file_content_string)
            return file_content_string

        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        
   
def check_clear_database():
        """
        Utility to wipe the database clean (Good for testing). if the dir exists
        """
        test_db_dir = "test_chroma_db"
        db_existed_before = pathlib.Path(test_db_dir).exists()
        path = pathlib.Path(test_db_dir)
        if db_existed_before:
            # Recursively delete the directory
            shutil.rmtree(path)
            print("🧹 Database cleared (files removed).")
        else:  
            print("db did not exist before")

# --- TICKET TEST BLOCK ---
if __name__ == "__main__":
    print("🧪 STARTING TEST: Vector Database Pipeline (mxbai-embed-large)\n")
    
    #  Setup Logic
    # We clear the DB first so we don't have duplicate data from previous runs

    test_db_dir = "test_chroma_db"
  
    
        
    check_clear_database()
    # Initialize the DB
    vdb = VectorDatabase(persist_directory=test_db_dir)
    #vdb.clear_database() dont use this to avoid null db check
    

    
    
    #vdb.clear_database() dont clear before you make it
    
    # 2. Create Dummy Data
    dummy_txt1 = vdb.create_txt_file_test("data/txt_files_med_test/report1_L.txt")
    dummy_txt2 = vdb.create_txt_file_test("data/txt_files_med_test/report2_L.txt")
    dummy_txt3 = vdb.create_txt_file_test("data/txt_files_med_test/report3_L.txt")
    
    
    dummy_docs = [
        Document(
            page_content=dummy_txt1,
            metadata={"source": "report_a.txt"}
        ),
        Document(
            page_content=dummy_txt2,
            metadata={"source": "report_b.txt"}
        ),
        Document(
            page_content=dummy_txt3,
            metadata={"source": "random.txt"}
        )
    ]
    
    # 3. Test Ingestion
    vdb.add_documents(dummy_docs)
    
    # 4. Test Retrieval
    query = "What is the revenue of Apex Technologies?"
    results = vdb.retrieve(query, k=2)
    
    print("\n📊 TEST RESULTS:")
    if len(results) >= 1:
        top_match = results[0]
        print(f"   Query: '{query}'")
        #print(f"   Top Result Content: \"{top_match.page_content}\"")
        print(f"   Top Result Source: {top_match.metadata['source']}")
        
        # Verification Check
        if "Revenue" in top_match.page_content:
            print("\n✅ TICKET COMPLETE: System retrieved the correct revenue chunk using mxbai.")
        else:
            print("\n❌ FAILURE: Retrieved chunk does not contain revenue info.")
    else:
        print("\n❌ FAILURE: No results returned.")