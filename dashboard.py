import streamlit as st
import pandas as pd

# Set the page title and layout
st.set_page_config(page_title="AI Code Reviewer", layout="wide")

st.title("🤖 AI Code Review Dashboard")
st.markdown("Welcome to the control center for your AI reviewer.")

# Create two columns for a clean layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("System Status")
    st.success("API Connection: Online")
    st.info("GitHub Webhook: Active")

with col2:
    st.subheader("Review Analytics (Mock Data)")
    # We will connect this to real data later
    mock_data = pd.DataFrame({
        'Review Type': ['Security', 'Performance', 'Style'],
        'Issues Found': [2, 5, 12]
    })
    st.bar_chart(mock_data.set_index('Review Type'))
