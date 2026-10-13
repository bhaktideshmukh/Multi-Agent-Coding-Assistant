import os
import time
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv(override=True)

# Initialize our LLM with max_tokens=650 to stay comfortably within Groq's 1000 OTPM ceiling
llm = ChatGroq(model_name="qwen/qwen3.8-27b", temperature=0.2, max_tokens=650)

def invoke_with_retry(target, inputs, max_retries=4, delay=5):
    """Retries LLM calls automatically with sufficient backoff for Groq's 60-second rolling token window."""
    for attempt in range(max_retries):
        try:
            return target.invoke(inputs)
        except Exception as e:
            err_msg = str(e).lower()
            is_transient = any(term in err_msg for term in ["429", "rate_limit", "connection", "connecterror", "timeout", "getaddrinfo", "aborted", "socket"])
            if is_transient and attempt < max_retries - 1:
                # Groq OTPM limit rolls over every 60 seconds. Wait 20s so the window replenishes.
                wait_time = 20 if ("429" in err_msg or "rate_limit" in err_msg) else delay
                print(f"Rate limit / transient issue. Pausing {wait_time}s for token replenishment ({attempt+1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                raise e
    return target.invoke(inputs)

def planner_agent(state: AgentState) -> AgentState:
    print("--- PLANNER AGENT RUNNING ---")
    user_request = state["user_request"]
    
    # Define how the AI should behave
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert software project manager. Take the user's request and create a concise, practical project plan. Focus on a clean, working solution with 3 to 6 essential files. Avoid overengineering with endless config files or excessive micro-modules. Do NOT write code."),
        ("user", "Here is the request: {request}")
    ])
    
    # Connect the prompt to the LLM and run it
    chain = prompt | llm
    result = invoke_with_retry(chain, {"request": user_request})
    
    # Return a dictionary that updates the 'plan' field in our state
    return {"plan": result.content}

# --- 2. Architect Agent ---
# Define the strict schema we want the Architect to return
class FileTask(BaseModel):
    file_name: str = Field(description="The name of the file, including path if necessary (e.g., 'app.py' or 'components/button.py')")
    description: str = Field(description="Brief 1-2 sentence instruction on what code to write in this file")

class Architecture(BaseModel):
    files: List[FileTask] = Field(description="A list of 3 to 6 essential files to be created for the project (maximum 8 files)")

def architect_agent(state: AgentState) -> AgentState:
    print("--- ARCHITECT AGENT RUNNING ---")
    plan = state["plan"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert software architect. Based on the provided project plan, define the essential files needed to build a functional project.\n"
                   "- Generate between 3 to 6 core, runnable files (maximum 8 files).\n"
                   "- Each entry must be an actual code file (never directories or asset folders).\n"
                   "- Keep each description brief (1 to 2 sentences max).\n"
                   "- Avoid extraneous linters, configs, or boilerplate files."),
        ("user", "Here is the project plan:\n{plan}")
    ])
    
    # Force the LLM to return data matching our Architecture schema
    structured_llm = llm.with_structured_output(Architecture)
    chain = prompt | structured_llm
    
    result = invoke_with_retry(chain, {"plan": plan})
    
    # Filter out any directory names or empty filenames
    valid_files = [f for f in result.files if f.file_name and not f.file_name.endswith("/") and not f.file_name.endswith("\\")]
    
    # Convert the Pydantic models back into standard dictionaries for our State
    architecture_list = [{"file_name": f.file_name, "description": f.description, "code": ""} for f in valid_files]
    
    return {"architecture": architecture_list, "current_file_index": 0}

# --- 3. Coder Agent ---
def coder_agent(state: AgentState) -> AgentState:
    print("--- CODER AGENT RUNNING ---")
    architecture = state["architecture"]
    current_index = state.get("current_file_index", 0)
    
    # Check if we have coded all the files
    if current_index >= len(architecture):
        return {"status": "Coding Complete"}
        
    file_to_code = architecture[current_index]
    print(f"Coding file: {file_to_code['file_name']}")
    time.sleep(3)  # Pause between files to respect Groq OTPM rate limits
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert senior software engineer. You write highly optimized, clean, and bug-free code. Return ONLY the raw code for the requested file. Do NOT include markdown blocks, explanations, or conversational text. Just the code."),
        ("user", "File name: {file_name}\n\nInstructions: {description}\n\nWrite the complete code for this file.")
    ])
    
    chain = prompt | llm
    result = invoke_with_retry(chain, {"file_name": file_to_code["file_name"], "description": file_to_code["description"]})
    
    # Strip markdown backticks just in case the LLM still tries to format it as markdown
    code = result.content
    if code.startswith("```"):
        lines = code.split("\n")
        if len(lines) > 2:
            code = "\n".join(lines[1:-1])
            
    # Save code to the state
    architecture[current_index]["code"] = code
    
    # Write the code to the physical hard drive in a 'workspace' folder
    output_dir = "workspace"
    os.makedirs(output_dir, exist_ok=True)
    
    # Handle folders (e.g. if file_name is "components/button.py")
    full_path = os.path.join(output_dir, file_to_code["file_name"])
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(code)
    
    # Move to the next file for the next loop iteration
    return {"architecture": architecture, "current_file_index": current_index + 1}

