from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from src.database import VectorDatabase
import shutil
import pathlib
from pathlib import Path

class AnalystAgent:
    """
    Orchestrates the LLM and Vector Database to analyze documents.
    """
    #TODO pass a VDB object in as a reference, an agent should not OWN a database
    def __init__(self, vdb: VectorDatabase):
        # 1. Initialize the LLM
        # temperature=0 is critical for strict data extraction
        self.llm = OllamaLLM(model="llama3.2", temperature=0)
        #test_db_dir = "test_chroma_db"
        # 2. Connect to the DB
        self.db = vdb




    def analyze_single_field(self, company_name: str, field: str) -> str:
        """
        Extracts a single data point with high precision.
        """
        # 1. TARGETED RETRIEVAL
        # We search for "Apple Revenue" instead of just "Apple".
        #  we should  get the specific paragraph about revenue.
        specific_query = f"{company_name} {field}"
        print(f"   🔎 Zooming in on: '{specific_query}'...")
        
        docs = self.db.retrieve(query=specific_query, k=3) # We only need 2 chunks for 1 fact not 6!
        
        if not docs:
            return "N/A"
            
        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 2. SIMPLE PROMPT
        # No complex instructions. just "Find X". avoids reaching context limit
        template_text = """
        Based ONLY on the context below, extract the value for: {field}
        
        Context:
        {context}
        
        Instructions:
        - return only the value found for field
        - do not write any sentances or explanation
        - If not found, write 'N/A'.
        """
        
        prompt = ChatPromptTemplate.from_template(template_text)
        chain = prompt | self.llm
        
        # 3. EXECUTE
        response = chain.invoke({
            "context": context_text, 
            "field": field
        })
        
        return response.strip()
        
    
    

    
    def generate_prompt(self, target_fields: list[str]) -> ChatPromptTemplate:
        """
        Dynamically constructs a prompt based on the specific fields the user wants.
        """
        field_list_str = "\n".join([f"{i+1}. {field}" for i, field in enumerate(target_fields)])
        
        template_text = """
        You are an expert financial analyst. Your goal is to extract specific data points from the provided context.
        
        Based on ONLY the context provided below, extract the following information:
        if a company is given that is not included in the context, write N/A for all fields
        {field_list_str}
        
        --- INSTRUCTIONS ---
        1. Return the values in a single line, separated by pipes (|).
        2. Follow the exact order of the list above.
        3. If a piece of information is NOT found in the context, write 'N/A' for that field Do NOT repeat previous values..
        4. Do NOT write any introduction, explanation, or extra text. Output ONLY the values. 
        5. Do NOT format as Markdown.
    

        
        Example Output for 3 fields:
        $45 Billion | Tim Cook | Supply Chain Disruptions

        
        Context:
        {context}
        
        Analysis:
        """
        
        prompt = ChatPromptTemplate.from_template(template_text)
        return prompt.partial(field_list_str=field_list_str)

    def _parse_response(self, raw_response: str, fields: list[str]) -> dict:
        """
        Internal helper to clean and structure the LLM output.
        """
        # 1. Clean whitespace
        cleaned_response = raw_response.strip()
        
        # 2. Split by pipe
        # We assume the model followed the "Value | Value" instruction
        values = [val.strip() for val in cleaned_response.split("|")]
        
        # 3. Handle Edge Case: Fewer values than fields
        if len(values) < len(fields):
            print(f"⚠️ Warning: Model returned {len(values)} values for {len(fields)} fields. Padding with 'N/A'.")
            # Fill the rest with "N/A"
            values.extend(["N/A"] * (len(fields) - len(values)))
            
        # 4. Handle Edge Case: More values (Rare, but truncate if needed)
        if len(values) > len(fields):
            values = values[:len(fields)]
            
        # 5. Zip into dictionary
        return dict(zip(fields, values))

    def analyze_company(self, company_name: str, target_fields: list[str]) -> dict:
        """
        The main entry point:
        1. Retrieves context for the company.
        2. Generates the prompt.
        3. Runs the LLM.
        4. Parses the result.
        """
        # Step A: Retrieve Context
        # We search specifically for the company name to get its relevant chunks
        print(f"🤖 Agent is analyzing: {company_name}...")
        docs = self.db.retrieve(query=company_name, k=6)
        
        if not docs:
            print("❌ No documents found. Returning empty results.")
            return {field: "N/A" for field in target_fields}
            
        # Combine the text from the retrieved chunks
        context_text = "\n\n".join([d.page_content for d in docs])
        
        # Step B: Build Chain
        prompt_template = self.generate_prompt(target_fields)
        chain = prompt_template | self.llm
        
        # Step C: Execute
        raw_response = chain.invoke({"context": context_text})

        # ----------------- DEBUG FIELD -----------------
        print(f"\n🐛 DEBUG RAW OUTPUT for {company_name}:")
        print(f"'{raw_response}'")
        print("-" * 20)
        
        # Step D: Parse
        return self._parse_response(raw_response, target_fields)
    




# --- TICKET TEST BLOCK ---
if __name__ == "__main__":
    print("🧪 STARTING TEST: Full Analyst Pipeline\n")
    
    # 1. Setup
    test_db_dir = "test_chroma_db"
        #make sure to use param
    vdb = VectorDatabase(test_db_dir)
    agent = AnalystAgent(vdb)
    
    # Note: This relies on the data we loaded in Ticket 3/Test Scripts.
    # If your DB is empty, run 'src/database.py' first to populate dummy data.
    
    # 2. Define Request
    # (from our dummy data)
    test_company = "Apex Technologies"
    test_fields = ["Revenue", "CEO"]
    
    # 3. Run Analysis
    try:
        result = agent.analyze_company(test_company, test_fields)
        
        # 4. Verification
        print(f"\n📊 RESULTS for {test_company}:")
        print("-" * 30)
        for key, value in result.items():
            print(f"{key:<15}: {value}")
        print("-" * 30)
        
        # Acceptance Criteria Checks
        if result.get("Revenue") and "$4.2 billion" in result["Revenue"] and result.get("CEO") and "Elena Rostova" in result["CEO"]:
            print("\n✅ TICKET COMPLETE: Revenue extracted correctly.")
            print("✅ Dictionary created successfully.")
        else:
            print("\n❌ FAILURE: Revenue extraction failed. (Did you populate the DB?)")
            
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")