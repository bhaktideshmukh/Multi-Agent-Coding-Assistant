from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    """
    This dictionary represents the state of our multi-agent system.
    It acts as a shared memory that gets passed from agent to agent.
    """
    
    # 1. The original prompt from the user (e.g., "Build a snake game")
    user_request: str
    
    # 2. The high-level plan written by the Planner agent
    plan: str
    
    # 3. The list of files and tasks created by the Architect agent
    architecture: List[Dict[str, Any]]
    
    # 4. A tracker so the Coder knows which file it is currently working on
    current_file_index: int
    
    # 5. A status message to let the system know when everything is finished
    status: str
