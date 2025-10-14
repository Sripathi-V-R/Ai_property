
# ==============================================================
#  🏙️ ReValix AI Property Intelligence
#  (Async Section Calls + Smart Retry + Modern UI)
#  Author: Ai Master | Powered by GPT-5
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
# STREAMLIT CONFIG + MODERN GLASS THEME
# --------------------------------------------------------------
st.set_page_config(page_title="ReValix AI Property Intelligence", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(145deg, #f8fafc, #e2ecf7);
        color: #0f172a;
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3 {
        color: #0ea5e9 !important;
    }
    .block-container {
        background: rgba(255,255,255,0.8);
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        padding: 2rem;
        backdrop-filter: blur(8px);
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1rem;
        color: #1e293b !important;
        border-radius: 8px;
        transition: all 0.3s ease-in-out;
    }
    .stTabs [data-baseweb="tab-list"] button[data-selected="true"] {
        background: linear-gradient(90deg, #0ea5e9, #2563eb);
        color: white !important;
        font-weight: 700;
    }
    .loader {
        border: 5px solid #e2e8f0;
        border-top: 5px solid #0ea5e9;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .revalix-header {
        font-size: 2.4rem;
        text-align: center;
        color: #0ea5e9;
        font-weight: 800;
        letter-spacing: 0.5px;
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
st.markdown("<div class='revalix-sub'>AI-Powered Real Estate Intelligence Engine</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🧠 Generate Intelligence", "📜 View Past Reports"])

# --------------------------------------------------------------
# FIELD TEMPLATE (simplified)
# --------------------------------------------------------------
def load_field_template():
    data = [
    ("Property ID", "Unique identifier like Parcel/APN/Tax ID"),
    ("Property Type", "Residential, Commercial, or Industrial"),
    ("Property Subtype", "Single Family / Office / Retail / Warehouse"),
    ("Address Line 1", "Street address of the property"),
    ("City", "City or Municipality name"),
    ("County", "County or District"),
    ("State", "State or Province"),
    ("Postal Code", "ZIP / PIN code"),
    ("Latitude", "GIS coordinate"),
    ("Longitude", "GIS coordinate"),
    ("Land Area", "Total land area in sqft or acres"),
    ("Building Name", "Name of the building or complex"),
    ("Year of Construction", "Construction year"),
    ("Building Condition", "Excellent / Good / Fair / Poor"),
    ("Stories", "Number of floors"),
    ("Units", "Number of housing/commercial units"),
    ("Total Rooms", "Total room count"),
    ("Bathrooms", "Total bathroom count"),
    ("Ownership Type", "Freehold / Leasehold / Co-op"),
    ("Owner Name", "Registered property owner(s)"),
    ("Occupancy Status", "Occupied / Vacant / Under Construction"),
    ("Current Market Value", "Estimated current market value"),
    ("Appraised Value", "Assessor’s appraised value"),
    ("Purchase Price", "Most recent sale price"),
    ("Purchase Date", "Date of sale or purchase"),
    ("Property Tax", "Annual tax amount"),
    ("Market Cap Rate", "Capitalization rate for valuation"),
    ("Market Rent", "Comparable average rent"),
    ("Vacancy Rate", "Percent unoccupied"),
    ("Flood Zone", "FEMA classification"),
    ("Zoning Code", "Municipal zoning classification"),
    ("Neighborhood Type", "Residential / Commercial / Mixed"),
    ("Legal Description", "Official parcel/legal description"),
    ("AI Condition Index", "AI-based property condition score"),
]
    return pd.DataFrame(data, columns=["Field", "Description"])

df_fields = load_field_template()

# --------------------------------------------------------------
# SECTION TEMPLATE (you can expand this later)
# --------------------------------------------------------------
def get_field_sections(df_fields):
    sections = {
    "Identification": [
        "Property ID",
        "Property Type",
        "Property Subtype"
    ],

    "Location": [
        "Address Line 1",
        "City",
        "County",
        "State",
        "Postal Code",
        "Latitude",
        "Longitude"
    ],

    "Land & Zoning": [
        "Land Area",
        "Flood Zone",
        "Zoning Code",
        "Neighborhood Type",
        "Legal Description"
    ],

    "Building Details": [
        "Building Name",
        "Year of Construction",
        "Building Condition",
        "Stories",
        "Units",
        "Total Rooms",
        "Bathrooms"
    ],

    "Ownership & Status": [
        "Ownership Type",
        "Owner Name",
        "Occupancy Status"
    ],

    "Market & Financial": [
        "Current Market Value",
        "Appraised Value",
        "Purchase Price",
        "Purchase Date",
        "Property Tax",
        "Market Cap Rate",
        "Market Rent",
        "Vacancy Rate"
    ],

    "AI Insights": [
        "AI Condition Index"
    ]
}


    records = []
    for section, fields in sections.items():
        for f in fields:
            if f in df_fields["Field"].values:
                desc = df_fields.loc[df_fields["Field"] == f, "Description"].values[0]
                records.append({"Section": section, "Field": f, "Description": desc})
    return pd.DataFrame(records)

df_sections = get_field_sections(df_fields)

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
            if len(parts) == 3:
                field, value, source = parts
                records.append({"Field": field, "Value": value, "Source": source})
            elif len(parts) == 2:
                field, value = parts
                records.append({"Field": field, "Value": value, "Source": "Government/Verified Records"})
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
# ASYNC API CALL
# --------------------------------------------------------------
async def call_api_async(session, address, field_list, section_name, county, county_url):
    prompt = build_prompt(address, field_list, section_name, county, county_url)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {"role": "system", "content": "You are a verified real estate data retriever."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
    }

    try:
        async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=60) as resp:
            data = await resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"API call error for {section_name}: {e}")
        return ""

# --------------------------------------------------------------
# MERGE AND SAVE
# --------------------------------------------------------------
def merge_and_save(df_ai, df_fields, property_address):
    if df_ai.empty:
        df_ai = pd.DataFrame(columns=["Field", "Value", "Source"])

    df_fields = df_fields.drop_duplicates(subset=["Field"], keep="first")
    merged = (
        df_ai.groupby("Field", as_index=False)
        .agg({
            "Value": lambda v: next((x for x in v if x and x != "NotFound"), "NotFound"),
            "Source": lambda s: next((x for x in s if x and x != ""), "Government/Verified Records"),
        })
    )
    df_final = pd.merge(df_fields[["Field"]], merged, on="Field", how="left")
    df_final["Value"].fillna("NotFound", inplace=True)
    df_final["Source"].fillna("Government/Verified Records", inplace=True)

    try:
        collection.replace_one({"address": property_address}, {"address": property_address, "records": df_final.to_dict(orient="records")}, upsert=True)
    except Exception as e:
        print("MongoDB save error:", e)

    return df_final

# --------------------------------------------------------------
# FINAL RETRY FOR MISSING FIELDS
# --------------------------------------------------------------
async def run_missing_fields_retry(property_address, df_final, df_fields, county, county_url):
    missing = df_final[df_final["Value"] == "NotFound"]["Field"].tolist()
    if not missing:
        st.info("✅ All fields successfully retrieved.")
        return df_final

    st.warning(f"🔁 Re-fetching {len(missing)} missing fields...")
    missing_defs = df_fields[df_fields["Field"].isin(missing)][["Field", "Description"]].values.tolist()
    prompt = build_prompt(property_address, missing_defs, "Final Retry", county, county_url)

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [{"role": "system", "content": "Fill factual property data only."}, {"role": "user", "content": prompt}],
        "temperature": 0.0,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers) as resp:
            data = await resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    new_records = parse_table(content)
    df_new = pd.DataFrame(new_records)
    for _, row in df_new.iterrows():
        df_final.loc[df_final["Field"] == row["Field"], ["Value", "Source"]] = [row["Value"], row["Source"]]
    st.success("✨ Missing fields refined and updated successfully.")
    return df_final

# --------------------------------------------------------------
# TAB 1 — GENERATE DATA
# --------------------------------------------------------------
with tab1:
    st.markdown("### 🧠 Generate Property Intelligence")
    property_address = st.text_input("🏡 Enter Full Property Address:")

    if st.button("🚀 Generate Report", use_container_width=True):
        if not property_address.strip():
            st.warning("⚠️ Please enter a property address.")
        else:
            with st.spinner("Detecting location and processing sections..."):
                county, state = detect_county_and_state(property_address)
                county_url = f"https://www.{county.lower().replace(' ', '')}{state.lower().replace(' ', '')}.gov" if county and state else ""

            st.success(f"📍 County Detected: {county}, {state}")
            async def process_sections():
                async with aiohttp.ClientSession() as session:
                    tasks = []
                    for section_name in df_sections["Section"].unique():
                        fields = df_sections[df_sections["Section"] == section_name][["Field", "Description"]].values.tolist()
                        tasks.append(call_api_async(session, property_address, fields, section_name, county, county_url))
                    results = await asyncio.gather(*tasks)
                    return results

            results = asyncio.run(process_sections())
            all_records = []
            for content in results:
                all_records.extend(parse_table(content))
            df_ai = pd.DataFrame(all_records)

            df_final = merge_and_save(df_ai, df_fields, property_address)
            df_final = asyncio.run(run_missing_fields_retry(property_address, df_final, df_fields, county, county_url))

            st.success(f"✅ Intelligence report for {property_address} generated successfully.")
            st.dataframe(df_final[["Field", "Value"]], use_container_width=True)

            output = BytesIO()
            df_final.drop(columns=["Source"]).to_excel(output, index=False)
            st.download_button("⬇️ Download Report (Excel)", data=output.getvalue(), file_name=f"ReValix_{property_address.replace(' ', '_')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

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


