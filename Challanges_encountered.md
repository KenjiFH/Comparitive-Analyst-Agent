# 🚧 Project Challenges & Technical Mitigations

Building a local RAG (Retrieval-Augmented Generation) pipeline for financial reports surfaced several engineering hurdles, transitioning the project from a simple script to a robust, fault-tolerant application. Below is a summary of the primary challenges and how they were solved.

## 1. State Leakage & Vector Pollution
* **The Challenge:** When analyzing multiple companies sequentially, the agent would occasionally "hallucinate" data, returning Company A's CEO when asked about Company B. This occurred because the vector database was retrieving the absolute best mathematical match from the entire document library, regardless of the target company.
* **The Mitigation:** * **Metadata Tagging:** Implemented an enrichment step during ingestion to automatically tag every text chunk with metadata (`company`, `year`).
  * **"Clean Room" Architecture:** Refactored the application loop to destroy and re-initialize the `AnalystAgent` for every new company analyzed, guaranteeing zero variable carry-over or state leakage between iterations.

## 2. Windows File Locking (The "Zombie Process" Error)
* **The Challenge:** When attempting to clear and re-ingest data via the Streamlit UI, the application crashed with a `PermissionError: [WinError 5] Access is denied`. Streamlit's persistent background process was keeping the ChromaDB SQLite files locked, preventing the `shutil.rmtree()` command from executing.
* **The Mitigation:** * **Subprocess Pattern:** Abstracted the database deletion and ingestion logic into a completely separate script (`ingest_worker.py`). 
  * Streamlit now triggers this script via Python's `subprocess` module. When the worker script finishes, the operating system forcibly closes all file handles, safely bypassing the Streamlit lock without requiring complex garbage collection.

## 3. The "Blender" Effect (Tabular Data Loss)
* **The Challenge:** Financial documents rely heavily on tables. The standard `RecursiveCharacterTextSplitter` reads 2D tables left-to-right, blending headers (e.g., "Q3", "Q4") with values (e.g., "$10M", "$15M") into a single, contextless string.
* **The Mitigation:** * **Immediate Fix:** Manually transformed tables in the raw `.txt` files into narrative sentences. 
  * **Architectural Tradeoff:** Acknowledged that standard text splitting is 1-Dimensional. Future iterations require Layout-Aware Parsing (e.g., LlamaParse or Unstructured.io) to preserve structural integrity.

## 4. Context Bleeding (Monolithic Prompt Failure)
* **The Challenge:** Initially, the LLM was prompted to extract four different fields (Revenue, CEO, Guidance, Risks) in a single request. The high cognitive load caused the LLM's attention to decay; it frequently hallucinated the final fields or repeated previous answers.
* **The Mitigation:** * **Sequential Extraction:** Deconstructed the monolithic prompt into targeted, single-field queries. The application now loops through the requested fields (e.g., querying *only* for Revenue, then *only* for the CEO), sacrificing a bit of speed for drastically improved accuracy.

## 5. Context Flooding & "Lost in the Middle"
* **The Challenge:** To prevent the agent from missing information at the end of documents (like "Forward Guidance"), the chunk size was increased to 2000 characters and the retrieval count (`k`) was raised to 9. This resulted in feeding the LLM up to 4,500+ tokens of text. The model became overwhelmed by the noise and hallucinated numbers.
* **The Mitigation:** * **Optimized Hyperparameters:** Reduced the retrieval parameters back to a denser ratio. By prioritizing high-quality, targeted retrieval over sheer volume, the LLM maintains its attention span.
  * **Query Expansion:** Mapped generic terms like "Revenue" to specific financial synonyms ("Total Net Sales") in the prompt to force the database to pull the exact number rather than generic policy paragraphs (Semantic Drift).
