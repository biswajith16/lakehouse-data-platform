"""Create a dataset configuration without embedding pipeline logic in Streamlit."""

from pathlib import Path

import pandas as pd
import streamlit as st

from app.services.pipeline_service import write_dataset_config

st.title("New Pipeline")
uploaded = st.file_uploader("Upload CSV, JSON, or Parquet", type=["csv", "json", "parquet"])
if uploaded:
    suffix = Path(uploaded.name).suffix.lower()
    readers = {".csv": pd.read_csv, ".json": pd.read_json, ".parquet": pd.read_parquet}
    try:
        preview = readers[suffix](uploaded)
        st.dataframe(preview.head(20))
        st.caption(f"Detected {len(preview.columns)} columns; preview row count: {len(preview)}")
        name = st.text_input("Dataset name", value=Path(uploaded.name).stem)
        primary_key = st.selectbox("Primary key", [""] + list(preview.columns))
        required = st.multiselect("Required columns", list(preview.columns))
        if st.button("Save configuration") and name:
            destination = Path("data/input") / uploaded.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(uploaded.getvalue())
            config = write_dataset_config(name, str(destination), suffix[1:], primary_key, required)
            st.success(f"Configuration saved: {config}")
    except Exception as error:
        st.error(f"Could not preview file: {error}")
