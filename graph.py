from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Define the exact data our graph will pass around
class GraphState(TypedDict):
    code_diff: str
    feedback: str

# Initialize the free Gemini model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

def reviewer_node(state: GraphState):
    code_diff = state.get("code_diff", "")
    
    sys_msg = SystemMessage(content=(
        "You are a senior software engineer conducting a code review. "
        "Analyze the provided code for security vulnerabilities, bugs, and performance issues. "
        "Provide your feedback in clean Markdown formatting with clear Python code blocks."
    ))
    human_msg = HumanMessage(content=f"Here is the code:\n\n{code_diff}")
    
    # Send the messages to Gemini
    response = llm.invoke([sys_msg, human_msg])
    
    # Cleanly extract text whether Gemini returns a raw string or a list of dictionaries
    content = response.content
    if isinstance(content, list):
        feedback_text = "\n".join([part.get("text", "") for part in content if isinstance(part, dict)])
    else:
        feedback_text = str(content)
    
    return {"feedback": feedback_text}

def build_graph():
    # Use the new StateGraph standard
    workflow = StateGraph(GraphState)
    
    # Add our node
    workflow.add_node("reviewer", reviewer_node)
    
    # Define the flow from START to reviewer to END
    workflow.add_edge(START, "reviewer")
    workflow.add_edge("reviewer", END)
    
    return workflow.compile()

# This is the graph that main.py imports
ai_reviewer_graph = build_graph()
