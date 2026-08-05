import streamlit as st
import requests
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables for local testing
load_dotenv()

st.set_page_config(page_title="AI Code Reviewer", page_icon="🤖", layout="wide")

# --- Configuration & Secrets Management ---
# This safely checks the local .env file first, then falls back to Streamlit Cloud Secrets
try:
    BACKEND_URL = os.environ.get("BACKEND_URL") or st.secrets.get("BACKEND_URL", "https://ai-reviewer-backend-ofpx.onrender.com")
    SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")
except FileNotFoundError:
    # Fallback if secrets.toml isn't found and we are just relying on os.environ
    BACKEND_URL = os.environ.get("BACKEND_URL", "https://ai-reviewer-backend-ofpx.onrender.com")
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# --- UI Header ---
st.title("🤖 AI Code Reviewer Control Center")
st.markdown("Automated GitHub Pull Request Reviews & Interactive Code Playground")

# --- Tabs ---
tab1, tab2 = st.tabs(["⚡ Live Code Chatbot / Playground", "📊 GitHub PR History"])

with tab1:
    st.header("Interactive Code Assistant")
    st.markdown("Paste any code snippet below to receive instant AI security and code quality feedback.")
    
    code_input = st.text_area("Paste your code here:", height=300)
    
    if st.button("Analyze Code"):
        if not code_input.strip():
            st.warning("Please enter some code to analyze.")
        else:
            with st.spinner("Analyzing code..."):
                try:
                    response = requests.post(f"{BACKEND_URL}/manual-review", json={"code": code_input})
                    if response.status_code == 200:
                        data = response.json()
                        feedback_text = data.get("feedback", "")
                        
                        st.success("Analysis Complete!")
                        st.markdown("### 🤖 AI Feedback & Recommendations")
                        # Using st.markdown ensures the AI output has clean formatting and copyable code blocks!
                        st.markdown(feedback_text)
                    else:
                        st.error(f"Backend responded with error code: {response.status_code}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")

with tab2:
    st.header("Automated PR Review Logs")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.warning("Supabase environment variables (SUPABASE_URL & SUPABASE_KEY) are missing. Please add them to your Streamlit Cloud Advanced Settings > Secrets.")
    else:
        try:
            # Connect to Supabase
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Fetch data from the 'reviews' table
            response = supabase.table("reviews").select("*").order("created_at", desc=True).execute()
            
            reviews = response.data
            
            if not reviews:
                st.info("No pull request reviews found yet.")
            else:
                for review in reviews:
                    # Create a clean dropdown menu for each review
                    with st.expander(f"PR #{review.get('pr_number', 'N/A')} - {review.get('repo_name', 'Unknown Repo')}"):
                        st.caption(f"Reviewed at: {review.get('created_at')}")
                        st.markdown(review.get("review_comment", "No comment generated."))
                        
        except Exception as e:
            st.error(f"Error fetching data from Supabase: {e}")
