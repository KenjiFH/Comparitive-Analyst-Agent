import pandas as pd
from src.agent import AnalystAgent

def main():
    print("🚀 Starting Comparative Analyst Agent...\n")

    # 1. Initialize the Agent
    # This loads the Llama 3.2 model and connects to your Chroma DB
    agent = AnalystAgent()

    # 2. Define Your Targets
    # These names must match the content in your text files so the vector DB finds them.
    # (Using the realistic data we created in Ticket 3/Seed Step)
    companies = [
        "Apex Technologies",
        "OmniMarkets Global Group",
        "GreenField Power"
    ]

    # 3. Define the Data Points you want to extract
    # You can change this list to anything ("Net Income", "Dividends", "Strategy", etc.)
    fields_to_extract = [
        "Revenue",
        "CEO", 
        "Primary Risks",
        "Forward Guidance"
    ]

    print(f"📋 Target Companies: {companies}")
    print(f"🔍 Extracting: {fields_to_extract}\n")

    all_results = []

    # 4. The Analysis Loop
    for company in companies:
        try:
            # Run the extraction (this calls the DB retrieval + LLM generation)
            data = agent.analyze_company(company, fields_to_extract)
            
            # Add the 'Company' name to the dictionary so it's the first column in our table
            data["Company"] = company
            
            all_results.append(data)
            print(f"✅ Finished analyzing {company}")
            
        except Exception as e:
            print(f"❌ Error analyzing {company}: {e}")

    # 5. Convert to Pandas DataFrame
    df = pd.DataFrame(all_results)

    # Reorder columns to put 'Company' first (just for looks)
    cols = ["Company"] + [col for col in df.columns if col != "Company"]
    df = df[cols]

    # 6. Output Results
    print("\n" + "="*50)
    print("📊 FINAL ANALYSIS TABLE")
    print("="*50)
    print(df.to_string(index=False))
    
    # Optional: Save to CSV
    df.to_csv("analysis_results.csv", index=False)
    print("\n💾 Results saved to 'analysis_results.csv'")

if __name__ == "__main__":
    main()