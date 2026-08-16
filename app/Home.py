"""Lakehouse Data Platform Streamlit control-plane landing page."""

import streamlit as st

st.set_page_config(page_title="Lakehouse Data Platform", layout="wide")
st.title("Lakehouse Data Platform")
st.caption("Config-Driven Self-Service Data Engineering Platform")
st.info("Use **New Pipeline** to upload and configure a dataset. Pipeline execution remains in the reusable Python engine.")
st.markdown("### Current capabilities\n- Demo pipeline engine\n- Config-driven Bronze and Silver stages\n- Data-quality quarantine\n\n### Planned\n- Run history and monitoring\n- Gold preview\n- Airflow orchestration")
