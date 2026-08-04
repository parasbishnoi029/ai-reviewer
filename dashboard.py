import streamlit as st
import requests
import os
from supabase import create_client, Client

st.set_page_config(page_title="AI Code Reviewer", page_icon="🤖", layout="wide")

# Configuration (replace backend URL with your Render link if different)
BACKEND_URL = os.getenv("BACKEND_URL", "https://ai-reviewer-backend-ofpx.onrender.com")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

st.title("🤖 AI Code Reviewer Control Center")
st.markdown("Automated GitHub Pull Request Reviews & Interactive Code Playground")

# Create two tabs for the app
tab1, tab2 = st.tabs(["⚡ Live Code Chatbot / Playground", "📊 GitHub PR History"])

# ---------------------------------------------------------
# TAB 1: Live Interactive Code Review
# ---------------------------------------------------------
with tab1:
    st.header("Interactive Code Assistant")
    st.write("Paste any code snippet below to receive instant AI security and code quality feedback.")
    
    code_input = st.text_area(
        "Paste your code here:",
        height=250,
        placeholder="def calculate_total(prices):\n    total = 0\n    for p in prices:\n        total += p\n    return total"
    )
    
    if st.button("Analyze Code", type="primary"):
        if not code_input.strip():
            st.warning("Please paste some code before clicking analyze!")
        else:
            with st.spinner("AI is inspecting your code..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/manual-review",
                        json={"code": code_input},
                        timeout=60
                    )
                    if response.status_code == 200:
                        feedback = response.json().get("feedback", "No feedback generated.")
                        st.success("Analysis Complete!")
                        st.markdown("### 🤖 AI Feedback & Recommendations")
                        st.markdown(feedback)
                    else:
                        st.error(f"Backend responded with error code: {response.status_code}")
                except Exception as e:
                    st.error(f"Failed to connect to backend server: {e}")

# ---------------------------------------------------------
# TAB 2: Supabase PR History
# ---------------------------------------------------------
with tab2:
    st.header("Automated PR Review Logs")
    
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            response = supabase.table("reviews").select("*").order("id", desc=True).execute()
            reviews = response.data
            
            if reviews:
                st.metric("Total Reviews in Database", len(reviews))
                st.markdown("---")
                for item in reviews:
                    pr_id = item.get("id")
                    timestamp = item.get("timestamp", "N/A")
                    pr_url = item.get("pr_url", "#")
                    feedback = item.get("feedback", "")
                    
                    with st.expander(f"Review #{pr_id} — {timestamp}"):
                        st.markdown(f"**Pull Request Link:** [{pr_url}]({pr_url})")
                        st.markdown("---")
                        st.markdown(feedback)
            else:
                st.info("No GitHub PR reviews have been saved to Supabase yet. Open a PR to generate one!")
        except Exception as e:
            st.error(f"Error fetching data from Supabase: {e}")
    else:
        st.warning("Supabase environment variables (SUPABASE_URL & SUPABASE_KEY) are missing.")
