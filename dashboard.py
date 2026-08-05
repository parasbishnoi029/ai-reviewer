import streamlit as st
import pandas as pd
import requests
import os
from dotenv import load_dotenv

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
tab1, tab2 = st.tabs(["💬 Conversational Assistant", "📊 Enterprise Analytics"])

with tab1:
    st.write("Paste code for a DevSecOps review, or ask follow-up questions about vulnerabilities.")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I am Aegis AI. Paste your code below for an instant security scan, or ask me a question."}
        ]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Paste code or ask a follow-up question..."):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤖 Analyzing..."):
                try:
                    BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")
                    API_KEY = os.environ.get("API_KEY", "dev-secret-key")
                    
                    # Send prompt AND the history (excluding the current prompt we just added)
                    payload = {
                        "code": prompt,
                        "history": st.session_state.messages[:-1] 
                    }
                    
                    response = requests.post(
                        f"{BACKEND_URL}/manual-review", 
                        json=payload,
                        headers={"X-API-Key": API_KEY}
                    )
                    
                    if response.status_code == 200:
                        ai_reply = response.json().get("feedback", "No response generated.")
                    else:
                        ai_reply = f"⚠️ API Error {response.status_code}: {response.text}"
                        
                    st.markdown(ai_reply)
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    
                except Exception as e:
                    st.error(f"Connection to backend failed: {e}")

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
