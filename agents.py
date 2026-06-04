import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from dotenv import load_dotenv
load_dotenv()

# Initialize our LLM (Llama 3 70B is highly capable and fast)
# Note: It will automatically look for GROQ_API_KEY in your environment later
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.2)

def planner_agent(state: AgentState) -> AgentState:
    print("--- PLANNER AGENT RUNNING ---")
    user_request = state["user_request"]
    
    # Define how the AI should behave
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert software project manager. Your job is to take a user's request and create a detailed, step-by-step project plan. Describe the features, the tech stack, and the overall architecture. Do NOT write code."),
        ("user", "Here is the request: {request}")
    ])
    
    # Connect the prompt to the LLM and run it
    chain = prompt | llm
    result = chain.invoke({"request": user_request})
    
    # Return a dictionary that updates the 'plan' field in our state
    return {"plan": result.content}

# --- 2. Architect Agent ---
# Define the strict schema we want the Architect to return
class FileTask(BaseModel):
    file_name: str = Field(description="The name of the file, including path if necessary (e.g., 'app.py' or 'components/button.py')")
    description: str = Field(description="Detailed instructions on what code should be written in this file")

class Architecture(BaseModel):
    files: List[FileTask] = Field(description="A list of files to be created for the project")

def architect_agent(state: AgentState) -> AgentState:
    print("--- ARCHITECT AGENT RUNNING ---")
    plan = state["plan"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert software architect. Based on the provided project plan, determine exactly what files need to be created. For each file, provide the file name and detailed instructions for the coder. Break down the project into a logical file structure."),
        ("user", "Here is the project plan: {plan}")
    ])
    
    # Force the LLM to return data matching our Architecture schema
    structured_llm = llm.with_structured_output(Architecture)
    chain = prompt | structured_llm
    
    result = chain.invoke({"plan": plan})
    
    # Convert the Pydantic models back into standard dictionaries for our State
    architecture_list = [{"file_name": f.file_name, "description": f.description, "code": ""} for f in result.files]
    
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
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert senior software engineer. You write highly optimized, clean, and bug-free code. Return ONLY the raw code for the requested file. Do NOT include markdown blocks, explanations, or conversational text. Just the code."),
        ("user", "File name: {file_name}\n\nInstructions: {description}\n\nWrite the complete code for this file.")
    ])
    
    chain = prompt | llm
    result = chain.invoke({"file_name": file_to_code["file_name"], "description": file_to_code["description"]})
    
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

