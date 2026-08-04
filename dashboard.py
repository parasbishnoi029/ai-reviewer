import streamlit as st
import json
import os

st.set_page_config(page_title="AI Code Reviewer", layout="wide")
st.title("🤖 AI Code Review Dashboard")
st.markdown("Welcome to the control center for your AI reviewer.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("System Status")
    st.success("API Connection: Online")
    st.info("GitHub Webhook: Active")

with col2:
    st.subheader("Recent Code Reviews")
    if os.path.exists("reviews.json"):
        with open("reviews.json", "r") as f:
            reviews = json.load(f)
        st.metric("Total Reviews Completed", len(reviews))
    else:
        st.warning("No reviews yet. Open a Pull Request to generate one!")
        reviews = []

st.divider()
st.subheader("Review History")

# Display the reviews, newest first
for review in reversed(reviews):
    with st.expander(f"PR Review: {review['timestamp']}"):
        st.write(f"**Pull Request URL:** [{review['pr_url']}]({review['pr_url']})")
        st.markdown(review['feedback'])
