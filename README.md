# 🤖 Local AI Financial Analyst

A local RAG (Retrieval-Augmented Generation) tool that ingests financial reports and extracts structured data (Revenue, CEO, Risks, Guidance) using **Llama 3**, **LangChain**, and **ChromaDB**.



## 🚀 Features

* **Local & Private:** Runs entirely on your machine using Ollama (no API keys required).
* **Structured Extraction:** Converts unstructured text into structured CSV data.
* **Streamlit UI:** Interactive dashboard for uploading data, monitoring progress, and downloading results.
* **Robust Error Handling:** Automatically handles "Read-Only" file locks common with local databases on Windows.

## 🛠️ Tech Stack

* **UI:** Streamlit
* **LLM Orchestration:** LangChain
* **Local LLM:** Ollama (Llama 3.2)
* **Vector Database:** ChromaDB
* **Language:** Python 3.10+



## ⚡️Setup & Usage
Prerequisites
Python 3.10+ installed.

Ollama installed and running.

Pull the model: ollama pull llama3.2

# Clone repository
git clone https://github.com/KenjiFH/Comparitive-Analyst-Agent
cd financial-analyst-agent

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt


streamlit run app.py

## 📦 Project Structure

![Architecture diagram](https://github.com/user-attachments/files/25308976/Architecture.diagram.pdf)


```text
├── app.py                 # Main Streamlit dashboard
├── ingest_worker.py       # Subprocess for safe DB deletion & ingestion
├── requirements.txt       # Python dependencies
├── data/                  # Drop your .txt financial reports here
│   └── txt_files_med/     
└── src/
    ├── agent.py           # Logic for prompting the LLM
    ├── database.py        # ChromaDB connection & settings
    └── ingestion.py       # Text chunking & metadata tagging logic
```text


