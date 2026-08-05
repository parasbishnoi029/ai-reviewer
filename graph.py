from langgraph.graph import Graph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Initialize the free Gemini 1.5 Flash model
# It will automatically look for the GOOGLE_API_KEY environment variable
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

def reviewer_node(state: dict):
    code_diff = state.get("code_diff", "")
    
    sys_msg = SystemMessage(content="You are a senior software engineer conducting a code review. Analyze the provided code for security vulnerabilities, bugs, and performance issues. Provide your feedback in clean Markdown formatting.")
    human_msg = HumanMessage(content=f"Here is the code:\n\n{code_diff}")
    
    # Send the messages to Gemini
    response = llm.invoke([sys_msg, human_msg])
    
    return {"feedback": response.content}

def build_graph():
    workflow = Graph()
    workflow.add_node("reviewer", reviewer_node)
    workflow.set_entry_point("reviewer")
    workflow.set_finish_point("reviewer")
    return workflow.compile()

