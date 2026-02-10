

### **Part 1: Engineering Challenges & Solutions (Post-Mortem)**

This section details the specific technical hurdles faced while building the local RAG agent.

#### **1. The "Blender" Effect (Table Destruction)**

* **The Issue:** Financial reports often contain data in tables (e.g., Revenue by Quarter). The standard text splitter (`RecursiveCharacterTextSplitter`) reads files left-to-right, treating the table rows as continuous sentences. This "blended" the headers with the values, causing the agent to mix up Q3 and Q4 data.
* **Solution / Tradeoff:**
* *Fix:* Manually converted tables in the source `.txt` files into narrative sentences (e.g., "Q3 Revenue was $4B").
* *Tradeoff:* This manual preprocessing is not scalable. It works for a demo but fails for real-world PDFs.


* **Key Learning:** **Text Splitters are 1-Dimensional; Tables are 2-Dimensional.** Standard RAG pipelines destroy structural context unless specialized parsers are used.

#### **2. Context Fragmentation (The "Cut-Off" Bug)**

* **The Issue:** The agent consistently missed "Forward Guidance" and "Risk Factors" because they were located at the very end of the documents. The retrieval settings were too conservative, effectively "cropping" the document before reaching the end.
* **Solution / Tradeoff:**
* *Fix:* Increased `chunk_size` to **2000 characters** (to keep full sections together) and increased retrieval `k` (top-k chunks) to **6**.
* *Tradeoff:* Larger chunks mean more noise (irrelevant text) is fed to the LLM, potentially confusing it. We traded precision for recall.


* **Key Learning:** Retrieval hyperparameters (`chunk_size`, `k`) must be tuned to the *document structure*, not just set to defaults.

#### **3. Semantic Drift (Concept vs. Keyword)**

* **The Issue:** Searching for "Revenue" returned the "Revenue Recognition Policy" (legal text) instead of the actual dollar amount. The vector database found the *word* "Revenue" repeated frequently in the policy, making it a "better" mathematical match than the single line containing the number.
* **Solution / Tradeoff:**
* *Fix:* Implemented **Query Expansion** in the prompt. Instead of just "Revenue," the agent was instructed to look for "Total Net Sales," "Financial Results," and "Turnover."
* *Tradeoff:* Hardcoding synonyms is brittle. A better solution would be using a "HyDE" (Hypothetical Document Embedding) approach.


* **Key Learning:** **Vector search is literal, not logical.** It finds similar words, not necessarily the *answer*.

#### **4. Vector Pollution (State Leakage)**

* **The Issue:** When analyzing multiple companies in a loop, the agent would hallucinate "Apex Tech" data while analyzing "GreenField Power." This happened because the vector database retrieved the "best match" from the entire library, ignoring which company file it came from.
* **Solution / Tradeoff:**
* *Fix:* Implemented the **"Clean Room" Pattern**. We re-initialized the Agent and (in some versions) the Database for every single company.
* *Tradeoff:* Re-initializing the DB is slow. The better long-term fix is **Metadata Filtering** (tagging chunks with `company_id`).


* **Key Learning:** **Statelessness is critical.** You cannot rely on an LLM to "ignore" context; you must physically prevent it from seeing wrong data.

#### **5. Context Bleeding (Monolithic Prompt Failure)**

* **The Issue:** When asking for 4 fields at once (Revenue, CEO, Risks, Guidance), the agent would often skip the last field or repeat the CEO's name for "Guidance." The cognitive load of the prompt was too high.
* **Solution / Tradeoff:**
* *Fix:* Switched to **Sequential Extraction**. The script now loops through fields one by one (`analyze_single_field`), creating a fresh prompt for each data point.
* *Tradeoff:* It is 4x slower because it makes 4 separate calls to the LLM instead of one.


* **Key Learning:** **Decomposition increases reliability.** Splitting complex tasks into atomic sub-tasks drastically reduces hallucinations.

#### **6. File Locking (The "Windows" Error)**

* **The Issue:** On Windows, attempting to delete the `test_chroma_db` folder caused a `PermissionError` because the Streamlit server (or a previous Python process) was still holding the file open.
* **Solution / Tradeoff:**
* *Fix:* Implemented the **Subprocess Pattern**. The ingestion script runs as a completely separate system process (`ingest_worker.py`). When it finishes, the OS forces all file locks to release.
* *Tradeoff:* Slightly more complex code architecture.


* **Key Learning:** **Process Isolation.** When dealing with file-based databases (SQLite/Chroma) in hot-reloading apps (Streamlit), you must run DB operations in a separate process to avoid lock contention.

---

### **Part 2: Roadmap for Improvement (Next Steps)**

To move this from a "Robust Demo" to a "Production Tool," the following features must be implemented.

#### **1. Layout-Aware Ingestion (Messy Docs & Tables)**

* **Current State:** Requires clean `.txt` files with manually formatted tables.
* **Upgrade:** Integrate **LlamaParse** or **Unstructured.io**.
* *Why:* These tools render PDFs to Markdown/HTML, preserving table structures. This solves the "Blender Effect" permanently without manual work.



#### **2. Automated Metadata Tagging**

* **Current State:** We manually hope the file name contains the company name.
* **Upgrade:** Implement an **"Ingestion Agent"**.
* *How:* Before chunking, pass the first page of the document to a small LLM (Llama-3-8B) with the prompt: *"Extract the Company Name, Ticker, Fiscal Year, and Quarter as JSON."*
* *Why:* Enables precise filtering (e.g., "Compare Q3 2024 vs Q3 2025") and prevents Vector Pollution.



#### **3. Content Hashing (Prevent Duplicates)**

* **Current State:** We wipe the database clean every time to avoid duplicates. This is slow and destructive.
* **Upgrade:** Implement **Idempotent Ingestion**.
* *How:* Generate a unique hash (MD5) for every text chunk.
* *Code:* `id = hashlib.md5(text.encode()).hexdigest()`. Pass this ID to `vdb.add_documents()`.
* *Why:* If you upload the same file twice, the database sees the IDs already exist and ignores them. This allows "Incremental Updates" (adding just one new file without deleting the old ones).



#### **4. Self-Correction Loop (Evaluation)**

* **Current State:** The agent returns whatever it finds, even if it's "N/A" or wrong.
* **Upgrade:** Add a **Validator Step**.
* *How:* After extraction, feed the answer back to the LLM: *"You extracted '$50B'. Does this number appear explicitly in the text below? Answer Yes/No."*
* *Why:* Adds a layer of "Quality Assurance" to catch hallucinations before the user sees them.
