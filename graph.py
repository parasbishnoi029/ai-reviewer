from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

class GraphState(TypedDict):
    code_diff: str
    feedback: str

# Using the high-limit free tier model
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

def reviewer_node(state: GraphState):
    code_diff = state.get("code_diff", "")
    
    sys_msg = SystemMessage(content=(
        "You are a Senior Staff Software Engineer conducting an enterprise code review. "
        "Analyze the provided pull request diff for security vulnerabilities, architectural flaws, "
        "and performance bottlenecks. Provide feedback in clean Markdown with Python code blocks."
    ))
    human_msg = HumanMessage(content=f"Here is the diff:\n\n{code_diff}")
    
    response = llm.invoke([sys_msg, human_msg])
    
    content = response.content
    if isinstance(content, list):
        feedback_text = "\n".join([part.get("text", "") for part in content if isinstance(part, dict)])
    else:
        feedback_text = str(content)
    
    return {"feedback": feedback_text}

def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_edge(START, "reviewer")
    workflow.add_edge("reviewer", END)
    return workflow.compile()

ai_reviewer_graph = build_graph()
