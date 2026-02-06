import pandas as pd
from src.agent import AnalystAgent
from src.database import VectorDatabase
from src.ingestion import load_and_chunk_documents 



import shutil
import pathlib
from pathlib import Path

#this *test_single_field* causes STATE LEAKAGE
""""
It happens when a variable (like context) isn't properly wiped clean between loop iterations. 
 If the database finds nothing for "Company B," the program might accidentally reuse the text it found for "Company A," 
 causing the AI to hallucinate Company A's CEO into Company B's report.

 we are trying instead to reinit agent in   current_agent = AnalystAgent(vdb) to avoid context leakage as "defensive programming"
 #larger documents exeeced chromadb context limits of embedding model

 #reinitilzing agent causes AGENTcontext to blank every to you make one
"""
def test_single_field(all_results,companies,fields_to_extract, agent,vdb):
     
    #for longer documents, more specifc lookups
    for company in companies:
        print(f"\n🏢 Analyzing {company}...")
        
        # Create a dictionary to hold results for THIS company
        company_data = {"Company": company}
        #current_agent = AnalystAgent(vdb)
        try:
            # --- THE NEW LOOP ---
            for field in fields_to_extract:
                # We ask the agent for ONE thing at a time
                value = agent.analyze_single_field(company, field)
                
                # Save it
                company_data[field] = value
                print(f"   ✅ {field}: {value}")
            
            # Append the completed row to our master list
            all_results.append(company_data)
            
        except Exception as e:
            print(f"❌ Error analyzing {company}: {e}")

        # Output Results
    if all_results:
        df = pd.DataFrame(all_results)

        # 1. Enforce Column Order
        # We explicitly tell Pandas: "Put 'Company' first, then the fields in the exact order I listed them."
        desired_order = ["Company"] + fields_to_extract
        
        # 2. Reindex
        # This sorts the columns. If a field was somehow missed, it fills it with "N/A" automatically.
        df = df.reindex(columns=desired_order).fillna("N/A")

        print("\n" + "="*50)
        print("📊 FINAL ANALYSIS TABLE")
        print("="*50)
        
        # print the table without the index numbers (0, 1, 2) on the left
        print(df.to_string(index=False))
        
        df.to_csv("analysis_results.csv", index=False)
        print("\n💾 Results saved to 'analysis_results.csv'")
    else:
        print("\n❌ No results to display.")


import pandas as pd
from src.database import VectorDatabase
from src.agent import AnalystAgent


#this creates a new agent every time a new company is seached with the same db
def run_clean_room_analysis(companies, fields_to_extract,vdb):
    print("🚀 Starting 'Clean Room' Analysis Pipeline...\n")
    
    # 1. HEAVY LIFTING: Initialize Database ONCE outside the loop
    # We load the data from disk here. This takes time (e.g., 2 seconds).
    
    
    all_results = []

    # 2. OUTER LOOP: Iterate Companies
    for company in companies:
        print(f"\n🏢 Processing: {company}")
        print("   Build: Creating fresh Agent instance...")
        
        # --- THE NEW APPROACH ---
        # We spawn a BRAND NEW agent just for this company.
        # It has zero memory of previous iterations.
        # We pass 'shared_vdb' so we don't waste time reloading files.
        disposable_agent = AnalystAgent(vdb)
        
        # Dictionary to hold this company's data
        row_data = {"Company": company}
        
        # 3. INNER LOOP: Iterate Fields (Sequential Extraction)
        for field in fields_to_extract:
            try:
                # The disposable agent focuses on one field at a time
                value = disposable_agent.analyze_single_field(company, field)
                row_data[field] = value
                print(f"   ✅ {field}: {value}")
                
            except Exception as e:
                print(f"   ❌ Error on {field}: {e}")
                row_data[field] = "ERROR"
        
        # 4. TEARDOWN
        # When the loop restarts, 'disposable_agent' is overwritten/deleted.
        # No variables survive to the next company.
        all_results.append(row_data)

    # 5. Output Results
    if all_results:
        df = pd.DataFrame(all_results)
        
        # Sort columns nicely
        cols = ["Company"] + fields_to_extract
        df = df.reindex(columns=cols).fillna("N/A")

        print("\n" + "="*60)
        print("📊 FINAL CLEAN ROOM REPORT")
        print("="*60)
        print(df.to_string(index=False))
        df.to_csv("clean_analysis_results.csv", index=False)

        

def test_list_fields(all_results,companies,fields_to_extract, agent):
     
    for company in companies:
        try:
            # We explicitly ask for context around the company name
            data = agent.analyze_company(company, fields_to_extract)
            data["Company"] = company
            all_results.append(data)
            print(f"✅ Finished analyzing {company}")
            
        except Exception as e:
            print(f"❌ Error analyzing {company}: {e}")

    # Output Results
    if all_results:
        df = pd.DataFrame(all_results)
        cols = ["Company"] + [col for col in df.columns if col != "Company"]
        df = df[cols]

        print("\n" + "="*50)
        print("📊 FINAL ANALYSIS TABLE")
        print("="*50)
        print(df.to_string(index=False))
        
        df.to_csv("analysis_results.csv", index=False)
        print("\n💾 Results saved to 'analysis_results.csv'")
    else:
        print("\n❌ No results to display.")

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

def main():
    print("🚀 Starting Comparative Analyst Agent...\n")

    # --- STEP 1: AUTO-INGESTION (The New Part) ---
    print("🔄 Checking for new documents...")
    
    # 1. Load raw text files
    raw_docs = load_and_chunk_documents("data/txt_files_med_test")

   
 
    
    if raw_docs:
        # 2. Connect to DB and clear old data (Optional: clear only if you want a fresh start)
        # For a clean test loop, we often wipe the DB so we don't have duplicate chunks.
        test_db_dir = "test_chroma_db"
        #make sure to use param
        check_clear_database()
        vdb = VectorDatabase(test_db_dir)
        
       
        
        # 3. Add the new chunks
        vdb.add_documents(raw_docs)
        print(f"✅ Ingestion Complete: {len(raw_docs)} chunks loaded into ChromaDB.\n")
    else:
        print("⚠️ No documents found in data/raw_docs/ to ingest.\n")

    # --- STEP 2: ANALYSIS (The Existing Part) ---
    
    # Initialize the Agent
    
    agent = AnalystAgent(vdb)

    # Define Your Targets
    
    companies = [
        "Apex Technologies",
        "OmniMarkets Global Group",
        "GreenField Power"
    ]
    

    fields_to_extract = [
        "Revenue",
        "CEO", 
        "Primary Risks",
        "Future Projections"
    ]

    print(f"📋 Target Companies: {companies}")
    print(f"🔍 Extracting: {fields_to_extract}\n")

    all_results = []



    test_list_fields(all_results,companies,fields_to_extract, agent)
    #run_clean_room_analysis(companies,fields_to_extract,vdb)
    #test_single_field(all_results,companies,fields_to_extract, agent,vdb)
    

   


   

if __name__ == "__main__":
    main()