import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os

from modules.mongo_manager import get_mongo_connection, save_property_data, get_saved_property
from modules.property_engine import call_openai_api, parse_output
from modules.ui_helpers import show_dataframe, download_excel_button
from modules.utils import detect_county_state

load_dotenv()

# Streamlit config
st.set_page_config(page_title="🏠 AI Property Intelligence", layout="wide")
st.title("🏠 AI Property Intelligence Agent")
st.caption("Factual, ordered property data — auto-saved to MongoDB & retrievable anytime.")

# MongoDB connection
collection = get_mongo_connection()

tab1, tab2 = st.tabs(["🧠 Generate & Save", "📜 View Past Lookups"])

# --- Field template (same as before) ---
fields = ["Property ID", "Property Name", "Property Type", "Owner Name(s)", "Assessed Value", "Tax Year", "Tax Amount", "Flood Zone"]
df_fields = pd.DataFrame(fields, columns=["Field"])

# ---------------- TAB 1 ----------------
with tab1:
    property_address = st.text_input("🏡 Enter Full Property Address:")
    if st.button("🚀 Generate & Save to MongoDB"):
        if not property_address.strip():
            st.warning("⚠️ Please enter an address first.")
        else:
            county, state = detect_county_state(property_address)
            st.info(f"🌍 Detected Location: {county}, {state}")

            # Build a simple prompt for OpenAI
            prompt = f"""
Fetch factual property data for "{property_address}" from official public sources (County Assessor, Zillow, Realtor, etc.).
Return a markdown table with these fields:
{', '.join(df_fields['Field'])}
If a field is missing, mark it as "NotFound".
"""

            raw = call_openai_api(prompt)
            df_ai = parse_output(raw)
            df_final = pd.merge(df_fields, df_ai, on="Field", how="left")
            df_final["Value"] = df_final["Value"].fillna("NotFound")
            df_final["Source"] = df_final["Source"].fillna("Other Government Records")

            save_property_data(collection, property_address, df_final)
            st.success(f"✅ Data saved for: {property_address}")
            show_dataframe(df_final)
            download_excel_button(df_final, property_address)

# ---------------- TAB 2 ----------------
with tab2:
    search_address = st.text_input("🏠 Search Address:")
    if st.button("🔍 View Saved Data"):
        doc = get_saved_property(collection, search_address)
        if doc:
            df_past = pd.DataFrame(doc["records"])[["Field", "Value"]]
            st.success(f"✅ Showing results for: {search_address}")
            show_dataframe(df_past)
        else:
            st.error("❌ No data found for this address.")
