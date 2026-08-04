from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
from dotenv import load_dotenv

# Load the secret API key from the .env file
load_dotenv()

# Define the data our graph will pass around
class ReviewState(TypedDict):
    code_diff: str
    feedback: str

# Initialize the LLM (using the mini model for speed and cost efficiency)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Define our specialist node
def reviewer_node(state: ReviewState):
    sys_msg = SystemMessage(
        content="You are a Senior Software Engineer. Review the following code diff. "
                "Lines starting with '+' are additions, '-' are deletions. "
                "Provide a brief, professional code review. Point out bugs, security flaws, "
                "or praise good code. Keep it under 3 paragraphs."
    )
    human_msg = HumanMessage(content=state["code_diff"])
    
    # Call the LLM
    response = llm.invoke([sys_msg, human_msg])
    
    # Update the state with the LLM's feedback
    return {"feedback": response.content}

# Build the State Machine
builder = StateGraph(ReviewState)
builder.add_node("reviewer", reviewer_node)

# Define the flow: START -> reviewer -> END
builder.add_edge(START, "reviewer")
builder.add_edge("reviewer", END)

# Compile it into a runnable application
ai_reviewer_graph = builder.compile()
