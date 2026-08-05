import streamlit as st
import pandas as pd
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="Aegis AI | DevSecOps", page_icon="🛡️", layout="wide")

# --- Database Connection ---
@st.cache_resource
def init_db():
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if url and key:
            return create_client(url, key)
    except Exception as e:
        st.error(f"Database connection failed: {e}")
    return None

supabase = init_db()

# --- Fetch Data ---
def load_data():
    if supabase:
        try:
            response = supabase.table("reviews").select("*").execute()
            if response.data:
                return pd.DataFrame(response.data)
        except Exception as e:
            pass
    return pd.DataFrame()

df_reviews = load_data()

# --- Dashboard Header ---
st.title("🛡️ Aegis AI | Command Center")
st.markdown("Next-Generation DevSecOps Intelligence & Automated Code Reviews")
st.divider()

# --- Tabs ---
tab1, tab2 = st.tabs(["🔍 Live Code Sandbox", "📊 Enterprise Analytics"])

# --- TAB 1: Live Code Sandbox ---
with tab1:
    st.markdown("### 🔍 Live Code Sandbox")
    st.write("Paste any code snippet below for an instant, comprehensive AI review (Pros, Cons, Fixes, and Final Code).")
    
    code_input = st.text_area("Paste Python/Code Diff here:", height=250)
    
    if st.button("Run DevSecOps Review", type="primary"):
        if not code_input.strip():
            st.warning("Please paste some code first!")
        else:
            with st.spinner("🤖 Analyzing Code..."):
                try:
                    BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
                    API_KEY = os.environ.get("API_KEY", "dev-secret-key")
                    
                    response = requests.post(
                        f"{BACKEND_URL}/manual-review", 
                        json={"code": code_input},
                        headers={"X-API-Key": API_KEY}
                    )
                    
                    if response.status_code == 200:
                        st.success("Analysis Complete!")
                        st.markdown(response.json().get("feedback", ""))
                    else:
                        st.error(f"API Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Connection to backend failed: {e}")

# --- TAB 2: Enterprise Analytics ---
with tab2:
    if df_reviews.empty:
        st.info("No enterprise data available yet. Waiting for GitHub webhooks...")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        total_reviews = len(df_reviews)
        active_repos = df_reviews['repo_name'].nunique() if total_reviews > 0 else 0
        
        if 'created_at' in df_reviews.columns:
            df_reviews['created_at'] = pd.to_datetime(df_reviews['created_at'])
            recent_reviews = len(df_reviews[df_reviews['created_at'] >= pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=7)])
        else:
            recent_reviews = 0
            
        hours_saved = total_reviews * 0.5
        
        with col1:
            st.metric("Total PRs Reviewed", total_reviews, f"{recent_reviews} this week")
        with col2:
            st.metric("Active Repositories", active_repos)
        with col3:
            st.metric("Eng Hours Saved", f"{hours_saved} hrs", "Based on 30m/PR")
        with col4:
            st.metric("Database Status", "Connected", "Syncing Live", delta_color="normal")
            
        st.divider()
        st.markdown("### Recent Automated Reviews")
        st.dataframe(
            df_reviews[['created_at', 'repo_name', 'pr_number', 'review_comment']].sort_values(by='created_at', ascending=False),
            use_container_width=True,
            hide_index=True
        )
