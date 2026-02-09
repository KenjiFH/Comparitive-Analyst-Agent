import streamlit as st
import pandas as pd
from src.database import VectorDatabase
from src.agent import AnalystAgent
from src.ingestion import *

import pathlib
from pathlib import Path


import gc
import time
import shutil

import os
import stat

# --- CONSTANTS ---
# We explicitly set the DB directory to match your test script environment
DB_DIR = "test_chroma_db" 

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="AI Financial Analyst",
    page_icon="📊",
    layout="wide"
)

# --- HEADER ---
st.title("🤖 AI Financial Analyst Agent")
st.markdown(f"""
This tool uses **LangChain**, **Ollama**, and **ChromaDB** to analyze financial reports.
It connects to the local database at: `{DB_DIR}`
""")


def streamit_safe_clear_db():
    db_path = pathlib.Path("test_chroma_db")
    
    # 1. THE FIX: Force Python to release the file lock
    # If a 'vdb' variable exists in the global scope or session state, delete it.
    if 'vdb' in globals():
        del globals()['vdb']
    
    # Force Garbage Collection to close the SQLite connection
    gc.collect()
    
    # Give the OS a tiny moment to register the file release
    time.sleep(0.5)

    # 2. NOW try to delete (with the read-only handler)
    if db_path.exists():
        print(f"🧹 Streamlit is clearing {db_path}...")
        try:
            # Only define handler locally if needed, or import it
            def remove_readonly(func, path, _):
                os.chmod(path, stat.S_IWRITE)
                func(path)
                
            shutil.rmtree(db_path, onerror=remove_readonly)
            print("✅ Database successfully wiped.")
            return True
        except Exception as e:
            print(f"❌ Still locked! Error: {e}")
            return False
    return True

# --- SIDEBAR: SYSTEM CONTROLS ---
with st.sidebar:
    st.header("⚙️ System Management")
    
    # 2. View Database Stats
    if st.button("📊 Check Database Connection"):
        try:
          
            vdb = VectorDatabase(persist_directory=DB_DIR)
            st.success(f"Connected to DB at: {vdb.persist_directory}")
        except Exception as e:
            st.error(f"Connection failed: {e}")

# --- MAIN INPUT AREA ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏢 Companies to Analyze")
    default_companies = "Apex Technologies\nGreenField Power\nOmniMarkets Global Group"
    companies_text = st.text_area("Enter company names (one per line):", value=default_companies, height=150)
    # Simple list comprehension to clean input
    companies = [c.strip() for c in companies_text.split('\n') if c.strip()]

with col2:
    st.subheader("🔍 Fields to Extract")
    default_fields = "Revenue\nCEO\nPrimary Risks"
    fields_text = st.text_area("Enter fields (one per line):", value=default_fields, height=150)
    target_fields = [f.strip() for f in fields_text.split('\n') if f.strip()]

# --- ANALYSIS LOGIC ---
if st.button("🚀 Start Analysis", type="primary"):
   
    if not companies or not target_fields:
        st.warning("Please enter at least one company and one field.")
    else:
        # Create a container for the results
        results_area = st.container()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_results = []
        
       
        
       
                
        with st.status("Processing Data...", expanded=True) as status:
            #streamit_safe_clear_db()
            try:
                # Initialize DB with specific directory
            
                vdb = VectorDatabase(persist_directory=DB_DIR)
       
        
                
               
             
                
                # Load and Chunk
                st.write("📂 Loading & Chunking documents...")

                 # Clear existing data
                st.write("🧹 Clearing old vectors...")
 
                raw_docs = load_and_chunk_documents("data/txt_files_med_test")
                
                if raw_docs:
                    # Embed and Store
                    st.write(f"🧠 Embedding {len(raw_docs)} chunks...")
                    vdb.add_documents(raw_docs)
                    status.update(label="✅ Ingestion Complete!", state="complete", expanded=False)
                    st.success(f"Successfully indexed {len(raw_docs)} chunks.")
                else:
                    status.update(label="⚠️ No documents found!", state="error")
                    st.error("No .txt files found in directory.")
                
            except Exception as e:
                st.error(f"Error during ingestion: {e}")
   
       
        agent = AnalystAgent(vdb)
        # Iterate through companies
        for i, company in enumerate(companies):
            status_text.text(f"Analyzing {company}...")
            
            try:
               
             
                
                # --- CALL THE MONOLITHIC FUNCTION ---
                # This uses your specific analyze_company method
                company_data = agent.analyze_company(company, target_fields)
                
                # Add the Company Name column explicitly for the table
                company_data["Company"] = company
                
                all_results.append(company_data)
                
            except Exception as e:
                st.error(f"Error analyzing {company}: {e}")
                all_results.append({"Company": company, "Error": str(e)})
            
            # Update Progress
            progress = (i + 1) / len(companies)
            progress_bar.progress(progress)
            
        # --- DISPLAY RESULTS ---
        status_text.text("✅ Analysis Complete!")
        progress_bar.empty()
        
        with results_area:
            st.subheader("📊 Analysis Results")
            
            if all_results:
                df = pd.DataFrame(all_results)
                
                # Reorder columns: Company first, then the requested fields
                # We use a set intersection to handle cases where fields might be missing
                cols = ["Company"] + [f for f in target_fields if f in df.columns]
                
                # Fill N/A for missing data
                df = df.reindex(columns=cols).fillna("N/A")
                
                # Display interactive table
                st.dataframe(df, use_container_width=True)
                
                # CSV Download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Download Results as CSV",
                    data=csv,
                    file_name="financial_analysis_report.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No results generated.")