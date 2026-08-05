import os
from typing import TypedDict, List, Dict, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

# 1. Structured Output Models
class CodeIssue(BaseModel):
    severity: str = Field(description="Critical, High, Medium, or Low")
    line_or_function: str = Field(description="Where the issue was found")
    description: str = Field(description="What the issue is")
    fix: str = Field(description="Actionable fix")

class ReviewResult(BaseModel):
    summary: str = Field(description="High-level summary of the code quality")
    issues: List[CodeIssue] = Field(description="List of identified issues")

# 2. Multi-Stage Graph State (Added chat_history and intent)
class GraphState(TypedDict, total=False):
    code_diff: str  # User input (either code or chat message)
    chat_history: List[Dict[str, str]]
    intent: str     # "review" or "chat"
    security_analysis: ReviewResult
    performance_analysis: ReviewResult
    feedback: str

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)
structured_llm = llm.with_structured_output(ReviewResult)

# 3. Define Graph Nodes
def routing_node(state: GraphState):
    """Stage 1: Determine if the user wants a code review or is just chatting."""
    prompt = f"Analyze this user input: '{state['code_diff']}'. Does this look like code that needs a DevSecOps review, or is it a conversational question? Reply with strictly 'review' or 'chat'."
    response = llm.invoke([HumanMessage(content=prompt)]).content.strip().lower()
    intent = "review" if "review" in response else "chat"
    return {"intent": intent}

def security_scan_node(state: GraphState):
    """Path A1: Scan strictly for OWASP security vulnerabilities."""
    prompt = f"Analyze this code diff strictly for security vulnerabilities:\n\n{state['code_diff']}"
    result = structured_llm.invoke([SystemMessage(content="You are an elite AppSec engineer."), HumanMessage(content=prompt)])
    return {"security_analysis": result}

def performance_scan_node(state: GraphState):
    """Path A2: Scan strictly for performance and optimization issues."""
    prompt = f"Analyze this code diff strictly for performance bottlenecks:\n\n{state['code_diff']}"
    result = structured_llm.invoke([SystemMessage(content="You are a Principal Performance Engineer."), HumanMessage(content=prompt)])
    return {"performance_analysis": result}

def format_report_node(state: GraphState):
    """Path A3: Combine structured data into a final Markdown report."""
    sec = state.get("security_analysis")
    perf = state.get("performance_analysis")
    
    report = f"## 🛡️ Aegis AI Enterprise Code Review\n\n"
    report += f"**Security Summary:** {sec.summary}\n"
    report += f"**Performance Summary:** {perf.summary}\n\n"
    
    report += "### 🚨 Security Vulnerabilities\n"
    if not getattr(sec, 'issues', []): report += "✅ No critical security issues found.\n"
    for issue in getattr(sec, 'issues', []):
        report += f"- **[{issue.severity}]** `{issue.line_or_function}`: {issue.description}\n  - *Fix:* {issue.fix}\n"
        
    report += "\n### ⚡ Performance Bottlenecks\n"
    if not getattr(perf, 'issues', []): report += "✅ No major performance issues found.\n"
    for issue in getattr(perf, 'issues', []):
        report += f"- **[{issue.severity}]** `{issue.line_or_function}`: {issue.description}\n  - *Fix:* {issue.fix}\n"

    return {"feedback": report}

def conversational_chat_node(state: GraphState):
    """Path B: Handle follow-up questions using memory."""
    messages = [SystemMessage(content="You are Aegis AI, an elite DevSecOps assistant. Answer the user's follow-up questions based on the previous code reviews. Keep answers concise, technical, and actionable.")]
    
    # Inject chat history
    for msg in state.get("chat_history", []):
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
            
    # Add current prompt
    messages.append(HumanMessage(content=state["code_diff"]))
    
    response = llm.invoke(messages)
    return {"feedback": response.content}

# 4. Routing Logic
def route_action(state: GraphState):
    if state.get("intent") == "review":
        return "security_scan"
    return "conversational_chat"

# 5. Build the Pipeline
workflow = StateGraph(GraphState)
workflow.add_node("router", routing_node)
workflow.add_node("security_scan", security_scan_node)
workflow.add_node("performance_scan", performance_scan_node)
workflow.add_node("format_report", format_report_node)
workflow.add_node("conversational_chat", conversational_chat_node)

workflow.add_edge(START, "router")
workflow.add_conditional_edges("router", route_action)

# Path A: Code Review
workflow.add_edge("security_scan", "performance_scan")
workflow.add_edge("performance_scan", "format_report")
workflow.add_edge("format_report", END)

# Path B: Chat
workflow.add_edge("conversational_chat", END)

ai_reviewer_graph = workflow.compile()
