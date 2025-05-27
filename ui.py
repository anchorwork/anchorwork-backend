import streamlit as st
import requests

BASE_URL = "http://localhost:8000"  # Change if your API runs elsewhere

st.set_page_config(page_title="Anchorwork Crew UI", page_icon="⚓️")
st.title("⚓️ Anchorwork Crew Interface")

st.sidebar.title("Interact with...")
options = [
    "Coder", "First Matey", "Cartographer", "Compass", "Watcher", "Alchemist", "Full Crew (Council)"
]
agent = st.sidebar.radio("Choose your agent or crew:", options)

prompt = st.text_area("What do you want to ask or do?", "")

if st.button("Send"):
    if agent == "Full Crew (Council)":
        resp = requests.post(f"{BASE_URL}/crew/brainstorm", json={"prompt": prompt})
        data = resp.json()
        st.subheader("Crew Council Response")
        st.write(data.get("formatted", data))
    else:
        endpoint = agent.lower().replace(" ", "")
        resp = requests.post(f"{BASE_URL}/{endpoint}", json={"prompt": prompt})
        data = resp.json()
        st.subheader(f"{agent} Response")
        st.write(data.get("result", data))

st.sidebar.markdown("---")
if st.sidebar.button("Show Crew History"):
    hist = requests.get(f"{BASE_URL}/crew/history?n=5").json()
    st.sidebar.write(hist.get("history", hist))

st.sidebar.markdown("---")
st.sidebar.info("Powered by Anchorwork Multi-Agent System")