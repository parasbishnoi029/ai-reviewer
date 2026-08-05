from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Define the exact data our graph will pass around
class GraphState(TypedDict):
    code_diff: str
    feedback: str

# Initialize the free Gemini 1.5 Flash model
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

def reviewer_node(state: GraphState):
    code_diff = state.get("code_diff", "")
    
    sys_msg = SystemMessage(content="You are a senior software engineer conducting a code review. Analyze the provided code for security vulnerabilities, bugs, and performance issues. Provide your feedback in clean Markdown formatting.")
    human_msg = HumanMessage(content=f"Here is the code:\n\n{code_diff}")
    
    # Send the messages to Gemini
    response = llm.invoke([sys_msg, human_msg])
    
    return {"feedback": response.content}

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