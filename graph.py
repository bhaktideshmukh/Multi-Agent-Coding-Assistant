from langgraph.graph import StateGraph, START, END
from state import AgentState
from agents import planner_agent, architect_agent, coder_agent

# 1. Initialize the graph with our custom State schema
workflow = StateGraph(AgentState)

# 2. Add our agents as nodes in the graph
workflow.add_node("planner", planner_agent)
workflow.add_node("architect", architect_agent)
workflow.add_node("coder", coder_agent)

# 3. Define the edges (the arrows connecting the nodes)
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "architect")
workflow.add_edge("architect", "coder")

# 4. Define a conditional edge for the Coder loop
def router(state: AgentState):
    """
    Checks if we have coded all the files.
    If yes, go to END. If no, go back to coder.
    """
    architecture = state.get("architecture", [])
    current_index = state.get("current_file_index", 0)
    
    if current_index >= len(architecture):
        return END
    else:
        return "coder"

# 5. Add the conditional edge to the coder node
workflow.add_conditional_edges(
    "coder",
    router,
    {
        "coder": "coder", # If router returns "coder", loop back to coder
        END: END          # If router returns END, stop the graph
    }
)

# 6. Compile the graph into an executable application
app = workflow.compile()
