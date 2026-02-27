




# 🤖 Local AI Financial Analyst

A local RAG (Retrieval-Augmented Generation) tool designed to ingest unstructured financial reports (`.txt` files) and extract structured, actionable business intelligence (Revenue, CEO, Risks, Guidance). 

By leveraging **Llama 3**, **LangChain**, and **ChromaDB**, this tool allows users to perform comparative analysis on multiple companies locally, ensuring complete data privacy.



---

## 🚀 Features

* **Local & Private:** Runs entirely on your local machine using Ollama. No data is sent to external APIs, and no API keys are required.
* **Structured Extraction:** Automatically converts dense, unstructured financial text into clean, structured CSV data for easy analysis.
* **Interactive UI:** Built with Streamlit, providing a user-friendly dashboard for uploading data, monitoring processing progress, and downloading results.
* **Robust Error Handling:** Specifically engineered to bypass "Read-Only" file locks common with local SQLite/ChromaDB databases on Windows systems.

---

## 🛠️ Tech Stack

* **Frontend UI:** [Streamlit](https://streamlit.io/)
* **Orchestration:** [LangChain](https://www.langchain.com/)
* **Local Inference:** [Ollama](https://ollama.com/) (Running `llama3.2`)
* **Vector Database:** [ChromaDB](https://www.trychroma.com/)
* **Language:** Python 3.10+

---

## ⚡️ Setup & Usage

Follow these steps to get the agent running on your local machine.

### 1. Prerequisites
* Ensure you have **Python 3.10+** installed.
* Download and install **[Ollama](https://ollama.com/download)** for your operating system.

### 2. Pull the Local Model
Open your terminal or command prompt and download the Llama 3.2 model:
```bash
ollama pull llama3.2

```

### 3. Clone the Repository

Clone this project to your local machine and navigate into the directory:

```bash

git clone [https://github.com/KenjiFH/Comparitive-Analyst-Agent](https://github.com/KenjiFH/Comparitive-Analyst-Agent)

cd Comparitive-Analyst-Agent

```

### 4. Set Up a Virtual Environment (Recommended)

Create and activate an isolated Python environment to manage dependencies:

```bash
# Create the virtual environment
python -m venv venv

# Activate on Mac/Linux:
source venv/bin/activate  

# Activate on Windows:
venv\Scripts\activate

```

### 5. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt

```

### 6. Run the Application

Launch the Streamlit dashboard:

```bash
streamlit run app.py

```



## 📦 Project Structure

```text
├── app.py                 # Main Streamlit dashboard and UI logic
├── ingest_worker.py       # Subprocess script for safe DB deletion & ingestion
├── requirements.txt       # Python package dependencies
├── data/                  # Drop your .txt financial reports here
│   └── txt_files_med/     # Default directory for test data
└── src/
    ├── agent.py           # Core logic for prompting and LLM interaction
    ├── database.py        # ChromaDB connection and configuration
    └── ingestion.py       # Text chunking and metadata tagging logic

```

```

***

```



