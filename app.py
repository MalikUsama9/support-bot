"""Streamlit demo UI.  Run:  streamlit run app.py"""
import os
import streamlit as st

# chroma_db is not stored in GitHub, so build the knowledge base on first start
if not os.path.exists("chroma_db"):
    from src.ingest import main as build_knowledge_base
    build_knowledge_base()

from src.answer import answer, STORE_NAME

st.set_page_config(page_title=f"{STORE_NAME} Support", page_icon="💬")
st.title(f"💬 {STORE_NAME} Support Assistant")
st.caption("AI assistant. Answers come from our store policies. It can make mistakes; "
           "tricky cases are passed to our team.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        if m.get("sources"):
            with st.expander("Sources"):
                for s in m["sources"]:
                    st.write("•", s)

question = st.chat_input("Ask about shipping, returns, sizing, payments...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Checking our policies..."):
            res = answer(question)
        st.write(res["answer"])
        if res["handoff"]:
            st.info("👤 Handed off to a human team member.")
        if res["sources"]:
            with st.expander("Sources"):
                for s in res["sources"]:
                    st.write("•", s)

    st.session_state.messages.append(
        {"role": "assistant", "content": res["answer"], "sources": res["sources"]}
    )