import os
from typing import TypedDict, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

# --- Structured Output Models ---
class CodeIssue(BaseModel):
    severity: str = Field(description="Critical, High, Medium, or Low")
    line_or_function: str = Field(description="Where the issue was found")
    description: str = Field(description="What the issue is")
    fix: str = Field(description="Actionable fix")

class ReviewResult(BaseModel):
    summary: str = Field(description="High-level summary of the code quality")
    issues: List[CodeIssue] = Field(description="List of identified issues")

class RefactorResult(BaseModel):
    pros: List[str] = Field(description="List of good practices or positive aspects found in the original code")
    final_code: str = Field(description="The complete, fully refactored code fixing all issues.")

# --- Graph State ---
class GraphState(TypedDict, total=False):
    code_diff: str  
    security_analysis: ReviewResult
    performance_analysis: ReviewResult
    refactor_analysis: RefactorResult
    feedback: str

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)
structured_review = llm.with_structured_output(ReviewResult)
structured_refactor = llm.with_structured_output(RefactorResult)

# --- Define Graph Nodes ---
def security_scan_node(state: GraphState):
    prompt = f"Analyze this code diff strictly for security vulnerabilities:\n\n{state['code_diff']}"
    result = structured_review.invoke([SystemMessage(content="You are an elite AppSec engineer."), HumanMessage(content=prompt)])
    return {"security_analysis": result}

def performance_scan_node(state: GraphState):
    prompt = f"Analyze this code diff strictly for performance bottlenecks:\n\n{state['code_diff']}"
    result = structured_review.invoke([SystemMessage(content="You are a Principal Performance Engineer."), HumanMessage(content=prompt)])
    return {"performance_analysis": result}

def refactor_node(state: GraphState):
    sec_issues = state.get("security_analysis").issues if state.get("security_analysis") else []
    perf_issues = state.get("performance_analysis").issues if state.get("performance_analysis") else []
    
    prompt = f"""Review this original code:\n{state['code_diff']}\n\nSecurity Issues to fix: {sec_issues}\nPerformance Issues to fix: {perf_issues}\n\n1. Identify 2-3 good practices (Pros) in the original code.\n2. Rewrite the entire code snippet to resolve ALL listed security and performance issues. Return clean, production-ready code."""
    
    result = structured_refactor.invoke([SystemMessage(content="You are a Senior Principal Software Engineer."), HumanMessage(content=prompt)])
    return {"refactor_analysis": result}

def format_report_node(state: GraphState):
    sec = state.get("security_analysis")
    perf = state.get("performance_analysis")
    refactor = state.get("refactor_analysis")
    all_issues = getattr(sec, 'issues', []) + getattr(perf, 'issues', [])
    
    report = "## 🛡️ Aegis AI Comprehensive Code Review\n\n"
    
    report += "### 🌟 Pros (What's Good)\n"
    if refactor and refactor.pros:
        for pro in refactor.pros:
            report += f"- ✅ {pro}\n"
    else:
        report += "- ✅ Code is structurally parseable.\n"
        
    report += "\n### 🚨 Cons & Vulnerabilities (What Needs Fixing)\n"
    if not all_issues:
        report += "- ✨ No major issues found!\n"
    for issue in all_issues:
        report += f"- **[{issue.severity}]** `{issue.line_or_function}`: {issue.description}\n"
        
    report += "\n### 🛠️ Recommended Fixes\n"
    if not all_issues:
        report += "- ✨ No fixes needed!\n"
    for issue in all_issues:
        report += f"- 🔧 **Fix for `{issue.line_or_function}`:** {issue.fix}\n"
        
    report += "\n### 💻 Final Refactored Code\n"
    if refactor and refactor.final_code:
        clean_code = refactor.final_code.strip("`").removeprefix("python").strip()
        report += f"```python\n{clean_code}\n```\n"

    return {"feedback": report}

# --- Build the Pipeline ---
workflow = StateGraph(GraphState)
workflow.add_node("security_scan", security_scan_node)
workflow.add_node("performance_scan", performance_scan_node)
workflow.add_node("refactor", refactor_node)
workflow.add_node("format_report", format_report_node)

# Straight pipeline execution
workflow.add_edge(START, "security_scan")
workflow.add_edge("security_scan", "performance_scan")
workflow.add_edge("performance_scan", "refactor")
workflow.add_edge("refactor", "format_report")
workflow.add_edge("format_report", END)

ai_reviewer_graph = workflow.compile()
