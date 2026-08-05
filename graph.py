import os
from dotenv import load_dotenv
load_dotenv()

from typing import TypedDict, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# 1. Define Structured Output Models
class CodeIssue(BaseModel):
    severity: str = Field(description="Critical, High, Medium, or Low")
    line_or_function: str = Field(description="Where the issue was found")
    description: str = Field(description="What the issue is")
    fix: str = Field(description="Actionable fix")

class ReviewResult(BaseModel):
    summary: str = Field(description="High-level summary of the code quality")
    issues: List[CodeIssue] = Field(description="List of identified issues")

# 2. Define Multi-Stage Graph State
class GraphState(TypedDict):
    code_diff: str
    security_analysis: ReviewResult
    performance_analysis: ReviewResult
    feedback: str

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)
# Force the model to return structured data matching our Pydantic model
structured_llm = llm.with_structured_output(ReviewResult)

# 3. Define Graph Nodes
def security_scan_node(state: GraphState):
    """Stage 1: Scan strictly for OWASP security vulnerabilities."""
    prompt = f"Analyze this code diff strictly for security vulnerabilities (e.g., injections, leaks, bad defaults):\n\n{state['code_diff']}"
    result = structured_llm.invoke([SystemMessage(content="You are an elite AppSec engineer."), HumanMessage(content=prompt)])
    return {"security_analysis": result}

def performance_scan_node(state: GraphState):
    """Stage 2: Scan strictly for performance and optimization issues."""
    prompt = f"Analyze this code diff strictly for performance bottlenecks (e.g., O(n^2) loops, memory waste):\n\n{state['code_diff']}"
    result = structured_llm.invoke([SystemMessage(content="You are a Principal Performance Engineer."), HumanMessage(content=prompt)])
    return {"performance_analysis": result}

def format_report_node(state: GraphState):
    """Stage 3: Combine structured data into a final Markdown report."""
    sec = state.get("security_analysis")
    perf = state.get("performance_analysis")
    
    report = f"## 🛡️ Aegis AI Enterprise Code Review\n\n"
    report += f"**Security Summary:** {sec.summary}\n"
    report += f"**Performance Summary:** {perf.summary}\n\n"
    
    report += "### 🚨 Security Vulnerabilities\n"
    if not sec.issues: report += "✅ No critical security issues found.\n"
    for issue in sec.issues:
        report += f"- **[{issue.severity}]** `{issue.line_or_function}`: {issue.description}\n  - *Fix:* {issue.fix}\n"
        
    report += "\n### ⚡ Performance Bottlenecks\n"
    if not perf.issues: report += "✅ No major performance issues found.\n"
    for issue in perf.issues:
        report += f"- **[{issue.severity}]** `{issue.line_or_function}`: {issue.description}\n  - *Fix:* {issue.fix}\n"

    return {"feedback": report}

# 4. Build the Pipeline
workflow = StateGraph(GraphState)
workflow.add_node("security_scan", security_scan_node)
workflow.add_node("performance_scan", performance_scan_node)
workflow.add_node("format_report", format_report_node)

workflow.add_edge(START, "security_scan")
workflow.add_edge("security_scan", "performance_scan")
workflow.add_edge("performance_scan", "format_report")
workflow.add_edge("format_report", END)

ai_reviewer_graph = workflow.compile()
