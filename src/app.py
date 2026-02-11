import streamlit as st
import pandas as pd
import subprocess
import sys

# Import Agent/DB for the ANALYSIS phase (Read-Only)
from src.database import VectorDatabase
from src.agent import AnalystAgent

# --- CONSTANTS ---
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
This tool uses **LangChain**, **Ollama**, and **ChromaDB**.
Current Architecture: **Subprocess Ingestion** (Prevents File Locks).
""")

# --- SIDEBAR: SYSTEM CONTROLS ---
with st.sidebar:
    st.header("⚙️ System Management")
    
    if st.button("📊 Check Database Connection"):
        try:
            # We connect in Read-Only mode effectively
            vdb = VectorDatabase(persist_directory=DB_DIR)
            st.success(f"✅ Connected to: {vdb.persist_directory}")
        except Exception as e:
            st.error(f"Connection failed: {e}")

# --- MAIN INPUT AREA ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏢 Companies to Analyze")
    default_companies = "Apex Technologies\nGreenField Power\nOmniMarkets Global Group"
    companies_text = st.text_area("Enter company names (one per line):", value=default_companies, height=150)
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
        results_area = st.container()
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_results = []
        
        # --- PHASE 1: INGESTION (VIA SUBPROCESS) ---
        # We run the heavy lifting in a separate process.
        # This guarantees the file lock is released when the process dies.
        with st.status("🔄 Running Ingestion Pipeline...", expanded=True) as status:
            st.write("🚀 Launching worker process...")
            
            try:
                # Calls 'ingest_worker.py' using the same python interpreter
                result = subprocess.run(
                    [sys.executable, "ingest_worker.py"],
                    capture_output=True,
                    text=True,
                    check=True # Raises error if script fails
                )
                
                # Show the logs from the worker script
                st.code(result.stdout, language="bash")
                status.update(label="✅ Ingestion Complete!", state="complete", expanded=False)
                
            except subprocess.CalledProcessError as e:
                status.update(label="❌ Ingestion Failed", state="error")
                st.error("The worker script crashed.")
                st.error(e.stderr) # Show the error log
                st.stop() # Stop execution here
        
        # --- PHASE 2: ANALYSIS (MAIN PROCESS) ---
        # Now that the worker is dead and locks are gone, we can safely connect.
        try:
            # Initialize DB Connection
            shared_vdb = VectorDatabase(persist_directory=DB_DIR)
            
            # Clean Room: Create a fresh Agent wrapper
            agent = AnalystAgent(shared_vdb)

            for i, company in enumerate(companies):
                status_text.text(f"Analyzing {company}...")
                
                try:
                    # Call your monolithic function
                    company_data = agent.analyze_company(company, target_fields)
                    company_data["Company"] = company
                    all_results.append(company_data)
                    
                except Exception as e:
                    st.error(f"Error analyzing {company}: {e}")
                    all_results.append({"Company": company, "Error": str(e)})
                
                # Update Progress
                progress = (i + 1) / len(companies)
                progress_bar.progress(progress)
                
        except Exception as e:
            st.error(f"Critical Error during analysis initialization: {e}")
            
        # --- PHASE 3: DISPLAY RESULTS ---
        status_text.text("✅ Analysis Complete!")
        progress_bar.empty()
        
        with results_area:
            st.subheader("📊 Analysis Results")
            
            if all_results:
                df = pd.DataFrame(all_results)
                cols = ["Company"] + [f for f in target_fields if f in df.columns]
                df = df.reindex(columns=cols).fillna("N/A")
                
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="💾 Download Results as CSV",
                    data=csv,
                    file_name="financial_analysis_report.csv",
                    mime="text/csv",
                )