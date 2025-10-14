# ==============================================================
# 🏙️ ReValix AI Property Intelligence
# (Async Field Calls + Smart Retry + MongoDB)
# Author: Ai Master | Powered by GPT-5
# ==============================================================

import streamlit as st
import pandas as pd
import os
import asyncio
import aiohttp
from openai import OpenAI
from pymongo import MongoClient
import requests
import re
from io import BytesIO
from urllib.parse import quote_plus
from dotenv import load_dotenv
from asyncio import Semaphore

# --------------------------------------------------------------
# ENVIRONMENT HANDLING
# --------------------------------------------------------------
if os.path.exists(".env"):
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
else:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    MONGO_URI = st.secrets["MONGO_URI"]

client = OpenAI(api_key=OPENAI_API_KEY)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["revalix_property_intelligence"]
collection = db["property_results"]

# --------------------------------------------------------------
# STREAMLIT CONFIG + CSS THEME
# --------------------------------------------------------------
st.set_page_config(page_title="ReValix AI Property Intelligence", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(145deg, #f8fafc, #e2ecf7);
        color: #0f172a;
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 { color: #0ea5e9 !important; }
    .block-container {
        background: rgba(255,255,255,0.8);
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        padding: 2rem;
        backdrop-filter: blur(8px);
    }
    .stTabs [data-baseweb="tab-list"] button[data-selected="true"] {
        background: linear-gradient(90deg, #0ea5e9, #2563eb);
        color: white !important;
        font-weight: 700;
    }
    .revalix-header {
        font-size: 2.4rem;
        text-align: center;
        color: #0ea5e9;
        font-weight: 800;
        margin-bottom: 0;
    }
    .revalix-sub {
        text-align: center;
        font-size: 1.1rem;
        color: #334155;
        margin-bottom: 35px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='revalix-header'>🏙️ ReValix AI Property Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='revalix-sub'>High-Accuracy Field-Level AI Property Insights</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🧠 Generate Intelligence", "📜 View Historical Records"])

# --------------------------------------------------------------
# FIELD TEMPLATE
# --------------------------------------------------------------
def load_field_template():
    # Simplified version for brevity — use your full field list
    data = [
        ("Property ID", "Unique identifier like Parcel/APN/Tax ID"),
        ("Property Type", "Residential, Commercial, Industrial, etc."),
        ("Property Subtype", "Single Family / Office / Retail / Warehouse"),
        ("Year of Construction", "YYYY"),
        ("Land Area", "Total land area in sqft or acres"),
        ("Building Name", "Name of the structure or project"),
        ("City", "City or Municipality"),
        ("State", "State or Province"),
        ("County", "County name"),
        ("Postal Code", "ZIP / PIN code"),
        ("Latitude", "GIS coordinate"),
        ("Longitude", "GIS coordinate"),
        ("Ownership Type", "Freehold / Leasehold / Co-op"),
        ("Occupancy Status", "Occupied / Vacant / Under Construction"),
        ("Current Market Value", "Estimated current market value"),
        ("Appraised Value", "Assessor’s appraised value"),
        ("Purchase Price", "Most recent sale price"),
        ("Purchase Date", "Date of sale or purchase"),
        ("Flood Zone", "FEMA classification"),
        ("Zoning Code", "Municipal zoning classification"),
        ("Neighborhood Type", "Residential / Commercial / Mixed"),
        ("Building Condition", "Excellent / Good / Fair / Poor"),
        ("Stories", "Number of floors"),
        ("Units", "Number of housing/commercial units"),
        ("Total Rooms", "Total room count"),
        ("Bathrooms", "Total bathroom count"),
        ("Market Cap Rate", "Capitalization rate for valuation"),
        ("Market Rent", "Comparable average rent"),
        ("Vacancy Rate", "Percent unoccupied"),
        ("Owner Name", "Registered owner"),
        ("Legal Description", "Official parcel/legal description"),
    ]
    return pd.DataFrame(data, columns=["Field", "Description"])

df_fields = load_field_template()

# --------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------
def detect_county_and_state(address):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={quote_plus(address)}&format=json&addressdetails=1"
        res = requests.get(url, headers={"User-Agent": "ReValix-Agent"}, timeout=10)
        data = res.json()
        if isinstance(data, list) and len(data) > 0 and "address" in data[0]:
            addr = data[0]["address"]
            return addr.get("county", ""), addr.get("state", "")
    except Exception:
        pass
    return "", ""

def parse_table(raw_output):
    records = []
    for line in raw_output.split("\n"):
        if "|" in line and not re.search(r"Field\s*\|\s*Value\s*\|\s*Source|----", line, re.IGNORECASE):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                field = parts[0]
                value = parts[1] if len(parts) > 1 else "NotFound"
                source = parts[2] if len(parts) > 2 else "AI Estimation"
                records.append({"Field": field, "Value": value, "Source": source})
    return records

def build_prompt(address, field_list, section_name, county_name, county_url):
    field_defs = "\n".join([f"{f}: {d}" for f, d in field_list])
    county_info = f"\nAlso check official county site: {county_name} ({county_url})" if county_url else ""
    return f"""
You are a verified property data retriever.
Fetch the accurate value for each field below for the property: {address}

Fields:
{field_defs}

Use trusted sources: Zillow, Redfin, County Assessor, Realtor, official data.
{county_info}

Return strictly in markdown table:
| Field | Value | Source |

Missing = NotFound
"""

# --------------------------------------------------------------
# ASYNC FIELD-LEVEL CALL
# --------------------------------------------------------------
async def call_api_async(session, address, field_list, field_name, county, county_url):
    prompt = build_prompt(address, field_list, field_name, county, county_url)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4.1",
        "messages": [
            {"role": "system", "content": "You are a verified real estate data retriever."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
    }

    try:
        async with session.post("https://api.openai.com/v1/chat/completions",
                                json=payload, headers=headers, timeout=60) as resp:
            data = await resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"API call error for {field_name}: {e}")
        return ""

# --------------------------------------------------------------
# PROCESS ALL FIELDS (ASYNC)
# --------------------------------------------------------------
async def process_all_fields(property_address, county, county_url):
    sem = Semaphore(20)  # limit concurrency (20 requests at once)
    async with aiohttp.ClientSession() as session:
        async def safe_call(field, desc):
            async with sem:
                return await call_api_async(session, property_address, [(field, desc)], field, county, county_url)

        tasks = [safe_call(row["Field"], row["Description"]) for _, row in df_fields.iterrows()]
        results = await asyncio.gather(*tasks)
        return results

# --------------------------------------------------------------
# MERGE & SAVE TO MONGODB
# --------------------------------------------------------------
def merge_and_save(df_ai, df_fields, property_address):
    if df_ai.empty:
        df_ai = pd.DataFrame(columns=["Field", "Value", "Source"])
    df_fields = df_fields.drop_duplicates(subset=["Field"], keep="first")
    merged = (
        df_ai.groupby("Field", as_index=False)
        .agg({
            "Value": lambda v: next((x for x in v if x and x != "NotFound"), "NotFound"),
            "Source": lambda s: next((x for x in s if x and x != ""), "AI Estimation"),
        })
    )
    df_final = pd.merge(df_fields[["Field"]], merged, on="Field", how="left")
    df_final["Value"].fillna("NotFound", inplace=True)
    df_final["Source"].fillna("AI Estimation", inplace=True)

    try:
        collection.replace_one(
            {"address": property_address},
            {"address": property_address, "records": df_final.to_dict(orient="records")},
            upsert=True,
        )
    except Exception as e:
        print("MongoDB save error:", e)
    return df_final

# --------------------------------------------------------------
# FINAL RETRY
# --------------------------------------------------------------
async def run_missing_fields_retry(property_address, df_final, df_fields, county, county_url):
    missing = df_final[df_final["Value"] == "NotFound"]["Field"].tolist()
    if not missing:
        st.info("✅ All fields successfully retrieved.")
        return df_final

    st.warning(f"🔁 Retrying {len(missing)} missing fields...")
    async with aiohttp.ClientSession() as session:
        sem = Semaphore(10)
        async def retry_field(field, desc):
            async with sem:
                return await call_api_async(session, property_address, [(field, desc)], f"Retry: {field}", county, county_url)
        missing_defs = df_fields[df_fields["Field"].isin(missing)][["Field", "Description"]].values.tolist()
        tasks = [retry_field(f, d) for f, d in missing_defs]
        results = await asyncio.gather(*tasks)

    new_records = []
    for content in results:
        new_records.extend(parse_table(content))
    df_new = pd.DataFrame(new_records)
    for _, row in df_new.iterrows():
        df_final.loc[df_final["Field"] == row["Field"], ["Value", "Source"]] = [row["Value"], row["Source"]]
    st.success("✨ Missing fields updated.")
    return df_final

# --------------------------------------------------------------
# TAB 1 — GENERATE INTELLIGENCE
# --------------------------------------------------------------
with tab1:
    st.markdown("### 🧠 Generate Property Intelligence")
    property_address = st.text_input("🏡 Enter Full Property Address:")

    if st.button("🚀 Generate Report", use_container_width=True):
        if not property_address.strip():
            st.warning("⚠️ Please enter a property address.")
        else:
            with st.spinner("🔍 Detecting location and fetching all fields..."):
                county, state = detect_county_and_state(property_address)
                county_url = f"https://www.{county.lower().replace(' ', '')}{state.lower().replace(' ', '')}.gov" if county and state else ""
            st.success(f"📍 County Detected: {county}, {state}")

            results = asyncio.run(process_all_fields(property_address, county, county_url))
            all_records = []
            for content in results:
                all_records.extend(parse_table(content))
            df_ai = pd.DataFrame(all_records)

            df_final = merge_and_save(df_ai, df_fields, property_address)
            df_final = asyncio.run(run_missing_fields_retry(property_address, df_final, df_fields, county, county_url))

            st.success(f"✅ Report generated for: {property_address}")
            st.dataframe(df_final[["Field", "Value"]], use_container_width=True)

            output = BytesIO()
            df_final.drop(columns=["Source"]).to_excel(output, index=False)
            st.download_button(
                "⬇️ Download Report (Excel)",
                data=output.getvalue(),
                file_name=f"ReValix_{property_address.replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# --------------------------------------------------------------
# TAB 2 — HISTORY
# --------------------------------------------------------------
with tab2:
    st.markdown("### 📜 View Saved Reports")
    search_address = st.text_input("🏠 Search by Address:")
    if st.button("🔍 Retrieve Report", use_container_width=True):
        doc = collection.find_one({"address": search_address})
        if doc:
            df_past = pd.DataFrame(doc["records"])[["Field", "Value"]]
            st.success(f"✅ Showing saved report for: {search_address}")
            st.dataframe(df_past, use_container_width=True)
        else:
            st.error("❌ No records found for this address.")


