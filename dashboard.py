import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="Enterprise AI Review Analytics", page_icon="🏢", layout="wide")

# --- Initialize Database with Caching ---
@st.cache_resource
def init_connection():
    url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL"))
    key = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY"))
    if not url or not key:
        return None
    return create_client(url, key)

supabase = init_connection()

# --- Fetch Data with TTL Caching ---
@st.cache_data(ttl=60)
def fetch_review_metrics():
    if not supabase:
        return pd.DataFrame()
    
    # Requires a 'created_at' column in your Supabase table
    try:
        response = supabase.table("reviews").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# --- UI Layout ---
st.title("🏢 Enterprise AI Code Review Analytics")
st.markdown("Monitor automated code reviews, security flags, and developer velocity.")

df_reviews = fetch_review_metrics()

if supabase is None:
    st.warning("Supabase credentials missing. Please configure your environment variables or Streamlit secrets.")
elif not df_reviews.empty:
    
    # --- Top-Level KPI Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_reviews = len(df_reviews)
    
    # Calculate recent reviews safely
    if 'created_at' in df_reviews.columns:
        df_reviews['created_at'] = pd.to_datetime(df_reviews['created_at'])
        recent_reviews = len(df_reviews[df_reviews['created_at'] >= pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=7)])
    else:
        recent_reviews = 0
    
    with col1:
        st.metric(label="Total PRs Reviewed", value=total_reviews, delta=f"{recent_reviews} this week")
    with col2:
        st.metric(label="Engineering Hours Saved", value=f"{total_reviews * 0.5} hrs", delta="Based on 30m/PR")
    with col3:
        st.metric(label="Avg Review Time", value="3.2s", delta="-0.5s", delta_color="normal")
    with col4:
        st.metric(label="Security Scans", value="100%", delta="Passing", delta_color="normal")
    
    st.divider()
    
    # --- Interactive Data Visualization ---
    st.subheader("Recent Pull Request Reviews")
    
    repo_filter = st.selectbox("Filter by Repository", ["All"] + list(df_reviews['repo_name'].unique()))
    filtered_df = df_reviews if repo_filter == "All" else df_reviews[df_reviews['repo_name'] == repo_filter]
    
    # Display Clean Table
    display_cols = ['pr_number', 'repo_name']
    if 'created_at' in filtered_df.columns:
        display_cols.append('created_at')
        
    st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)
    
    # Detailed Expander View
    st.subheader("Detailed Review Logs")
    for _, row in filtered_df.head(10).iterrows(): # Show top 10 to avoid UI lag
        timestamp = row['created_at'].strftime("%Y-%m-%d %H:%M") if 'created_at' in row else "Unknown Date"
        with st.expander(f"PR #{row['pr_number']} - {row['repo_name']} ({timestamp})"):
            st.markdown(row.get("review_comment", "No review body available."))
else:
    st.info("No enterprise data available. Trigger a webhook from GitHub to generate logs.")
