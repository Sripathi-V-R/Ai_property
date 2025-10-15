# ==============================================================
# 🏙️ ReValix AI Property Intelligence
# (Async Section Calls + ATTOM Verified + Smart Retry + Modern UI)
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

# --------------------------------------------------------------
# ENVIRONMENT HANDLING
# --------------------------------------------------------------
if os.path.exists(".env"):
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ATTOM_API_KEY = os.getenv("ATTOM_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
else:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    ATTOM_API_KEY = st.secrets["ATTOM_API_KEY"]
    MONGO_URI = st.secrets["MONGO_URI"]

client = OpenAI(api_key=OPENAI_API_KEY)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["revalix_property_intelligence"]
collection = db["property_results"]

# --------------------------------------------------------------
# STREAMLIT CONFIG + GLASS UI
# --------------------------------------------------------------
st.set_page_config(page_title="ReValix AI Property Intelligence", layout="wide")
st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #f8fafc, #e2ecf7);
    font-family: 'Inter', sans-serif;
}
.block-container {
    background: rgba(255,255,255,0.8);
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    padding: 2rem;
    backdrop-filter: blur(8px);
}
h1, h2, h3 { color: #0ea5e9 !important; }
.revalix-header { font-size: 2.4rem; text-align: center; color: #0ea5e9; font-weight: 800; }
.revalix-sub { text-align: center; font-size: 1.1rem; color: #334155; margin-bottom: 35px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='revalix-header'>🏙️ ReValix AI Property Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='revalix-sub'>AI-Powered Property Data Enrichment (GPT-4.1-mini + ATTOM)</div>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🧠 Generate Intelligence", "📜 View Past Reports"])

# --------------------------------------------------------------
# FIELD TEMPLATE
# --------------------------------------------------------------
def load_field_template():
    data = [
        ("Property ID", "Parcel/APN/Tax ID"),
        ("Property Type", "Residential, Commercial, Industrial, etc."),
        ("Property Subtype", "Single Family / Office / Retail / Warehouse"),
        ("Address Line 1", "Street address"),
        ("City", "City or Municipality"),
        ("County", "County or District"),
        ("State", "State or Province"),
        ("Postal Code", "ZIP / PIN code"),
        ("Latitude", "GIS coordinate"),
        ("Longitude", "GIS coordinate"),
        ("Land Area", "Land area in sqft or acres"),
        ("Zoning Type", "Zoning classification"),
        ("Year Built", "Construction year"),
        ("Building Condition", "Excellent / Good / Fair / Poor"),
        ("Stories", "Number of floors"),
        ("Bedrooms", "Total bedrooms"),
        ("Bathrooms", "Total bathrooms"),
        ("Owner Name", "Registered owner(s)"),
        ("Appraised Value", "Assessor’s appraised value"),
        ("Market Value", "Estimated market value"),
        ("Purchase Price", "Most recent sale price"),
        ("Purchase Date", "Date of sale or purchase"),
        ("Property Tax", "Annual tax"),
        ("Tax Year", "Year of tax assessment"),
        ("Cooling Type", "Cooling type"),
        ("Heating Type", "Heating type"),
        ("Energy Type", "Energy source"),
        ("AI Condition Index", "AI-generated condition score"),
    ]
    return pd.DataFrame(data, columns=["Field", "Description"])

df_fields = load_field_template()

# --------------------------------------------------------------
# SECTION MAPPING
# --------------------------------------------------------------
def get_field_sections(df_fields):
    sections = {
        "Identification": ["Property ID", "Property Type", "Property Subtype"],
        "Location": ["Address Line 1", "City", "County", "State", "Postal Code", "Latitude", "Longitude"],
        "Land & Zoning": ["Land Area", "Zoning Type"],
        "Building Details": ["Year Built", "Building Condition", "Stories", "Bedrooms", "Bathrooms"],
        "Ownership": ["Owner Name"],
        "Valuation": ["Appraised Value", "Market Value", "Purchase Price", "Purchase Date", "Property Tax", "Tax Year"],
        "Utilities": ["Cooling Type", "Heating Type", "Energy Type"],
        "AI Insights": ["AI Condition Index"],
    }
    records = []
    for section, fields in sections.items():
        for f in fields:
            desc = df_fields.loc[df_fields["Field"] == f, "Description"].values[0]
            records.append({"Section": section, "Field": f, "Description": desc})
    return pd.DataFrame(records)

df_sections = get_field_sections(df_fields)

# --------------------------------------------------------------
# ATTOM FETCH & FLATTEN
# --------------------------------------------------------------
def safe_get(d, keys):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return None
    return d

def fetch_attom_data(address):
    try:
        parts = address.split(",")
        address1 = parts[0].strip()
        address2 = ",".join(parts[1:]).strip() if len(parts) > 1 else ""
        url = (
            "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/basicprofile"
            f"?address1={quote_plus(address1)}&address2={quote_plus(address2)}"
        )
        headers = {"apikey": ATTOM_API_KEY, "accept": "application/json"}
        res = requests.get(url, headers=headers, timeout=30)
        res.raise_for_status()
        data = res.json()
        return data.get("property", [])
    except Exception as e:
        print("ATTOM fetch error:", e)
        return []

def flatten_attom_properties(properties):
    rows = []
    for p in properties:
        r = {}
        r["Property ID"] = safe_get(p, ["identifier", "apn"])
        r["Property Type"] = safe_get(p, ["summary", "propType"])
        r["Property Subtype"] = safe_get(p, ["summary", "propSubType"])
        r["Address Line 1"] = safe_get(p, ["address", "line1"])
        r["City"] = safe_get(p, ["address", "locality"])
        r["County"] = safe_get(p, ["area", "countrySecSubd"])
        r["State"] = safe_get(p, ["address", "countrySubd"])
        r["Postal Code"] = safe_get(p, ["address", "postal1"])
        r["Latitude"] = safe_get(p, ["location", "latitude"])
        r["Longitude"] = safe_get(p, ["location", "longitude"])
        r["Land Area"] = safe_get(p, ["lot", "lotSize1"])
        r["Year Built"] = safe_get(p, ["summary", "yearBuilt"])
        r["Building Condition"] = safe_get(p, ["building", "construction", "condition"])
        r["Stories"] = safe_get(p, ["building", "summary", "levels"])
        r["Bedrooms"] = safe_get(p, ["building", "rooms", "beds"])
        r["Bathrooms"] = safe_get(p, ["building", "rooms", "bathsTotal"])
        r["Owner Name"] = safe_get(p, ["assessment", "owner", "owner1", "fullName"])
        r["Appraised Value"] = safe_get(p, ["assessment", "assessed", "assdTtlValue"])
        r["Market Value"] = safe_get(p, ["assessment", "market", "mktTtlValue"])
        r["Purchase Price"] = safe_get(p, ["sale", "saleAmountData", "saleAmt"])
        r["Purchase Date"] = safe_get(p, ["sale", "saleAmountData", "saleRecDate"])
        r["Property Tax"] = safe_get(p, ["assessment", "tax", "taxAmt"])
        r["Tax Year"] = safe_get(p, ["assessment", "tax", "taxYear"])
        r["Cooling Type"] = safe_get(p, ["utilities", "coolingType"])
        r["Heating Type"] = safe_get(p, ["utilities", "heatingType"])
        r["Energy Type"] = safe_get(p, ["utilities", "energyType"])
        rows.append(r)
    return pd.DataFrame(rows)

# --------------------------------------------------------------
# UTILITIES
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
    return records

# --------------------------------------------------------------
# PROMPT BUILDER
# --------------------------------------------------------------
def build_prompt(address, field_list, section_name, county_name, county_url, attom_df):
    field_defs = "\n".join([f"{f}: {d}" for f, d in field_list])
    attom_text = attom_df.to_string(index=False) if not attom_df.empty else "None"
    county_info = f"\nAlso check official county site: {county_name} ({county_url})" if county_url else ""
    return f"""
You are a verified property intelligence assistant.
Retrieve accurate factual data for: {address}

Section: {section_name}
Fields:
{field_defs}

ATTOM verified data (use this to cross-check or fill missing values):
{attom_text}

Use trusted real estate sources: Zillow, Redfin, County Assessor, ATTOM, Realtor.
{county_info}

Return strictly:
| Field | Value | Source |
If not available, mark as NotFound.
"""

# --------------------------------------------------------------
# ASYNC GPT CALL
# --------------------------------------------------------------
async def call_api_async(session, address, field_list, section_name, county, county_url, df_attom):
    prompt = build_prompt(address, field_list, section_name, county, county_url, df_attom)
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [{"role": "user", "content": prompt}],
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
# MERGE + SAVE
# --------------------------------------------------------------
def merge_and_save(df_ai, df_fields, property_address, df_attom):
    if df_ai.empty:
        df_ai = pd.DataFrame(columns=["Field", "Value", "Source"])
    if not df_attom.empty:
        df_attom_melt = df_attom.melt(var_name="Field", value_name="Value")
        df_attom_melt["Source"] = "ATTOM Verified"
        df_ai = pd.concat([df_attom_melt, df_ai], ignore_index=True)
    merged = (
        df_ai.groupby("Field", as_index=False)
        .agg({
            "Value": lambda v: next((x for x in v if x and x != "NotFound"), "NotFound"),
            "Source": lambda s: next((x for x in s if x and x != ""), "Verified Data"),
        })
    )
    df_final = pd.merge(df_fields[["Field"]], merged, on="Field", how="left")
    df_final["Value"].fillna("NotFound", inplace=True)
    df_final["Source"].fillna("Verified Data", inplace=True)
    collection.replace_one({"address": property_address}, {"address": property_address, "records": df_final.to_dict(orient="records")}, upsert=True)
    return df_final

# --------------------------------------------------------------
# RETRY MISSING FIELDS
# --------------------------------------------------------------
async def run_missing_retry(property_address, df_final, df_fields, county, county_url):
    missing = df_final[df_final["Value"] == "NotFound"]["Field"].tolist()
    if not missing:
        st.info("✅ All fields successfully retrieved.")
        return df_final
    st.warning(f"🔁 Retrying {len(missing)} missing fields...")
    missing_defs = df_fields[df_fields["Field"].isin(missing)][["Field", "Description"]].values.tolist()
    prompt = build_prompt(property_address, missing_defs, "Final Retry", county, county_url, pd.DataFrame())
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers) as resp:
            data = await resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            df_new = pd.DataFrame(parse_table(content))
            for _, row in df_new.iterrows():
                df_final.loc[df_final["Field"] == row["Field"], ["Value", "Source"]] = [row["Value"], row["Source"]]
    st.success("✨ Missing fields updated successfully.")
    return df_final

# --------------------------------------------------------------
# TAB 1 — GENERATE DATA
# --------------------------------------------------------------
with tab1:
    st.markdown("### 🧠 Generate Property Intelligence")
    property_address = st.text_input("🏡 Enter Full Property Address:")

    if st.button("🚀 Generate Report", use_container_width=True):
        if not property_address.strip():
            st.warning("⚠️ Please enter an address.")
        else:
            with st.spinner("Fetching verified ATTOM data..."):
                attom_props = fetch_attom_data(property_address)
                df_attom = flatten_attom_properties(attom_props) if attom_props else pd.DataFrame()
                if not df_attom.empty:
                    st.success(f"✅ ATTOM data found with {len(df_attom.columns)} fields.")
                else:
                    st.warning("⚠️ No ATTOM data found, GPT-only mode.")

            county, state = detect_county_and_state(property_address)
            county_url = f"https://www.{county.lower().replace(' ', '')}{state.lower().replace(' ', '')}.gov" if county and state else ""

            async def process_sections():
                async with aiohttp.ClientSession() as session:
                    tasks = []
                    for section_name in df_sections["Section"].unique():
                        fields = df_sections[df_sections["Section"] == section_name][["Field", "Description"]].values.tolist()
                        tasks.append(call_api_async(session, property_address, fields, section_name, county, county_url, df_attom))
                    results = await asyncio.gather(*tasks)
                    return results

            results = asyncio.run(process_sections())
            all_records = []
            for content in results:
                all_records.extend(parse_table(content))

            df_ai = pd.DataFrame(all_records)
            df_final = merge_and_save(df_ai, df_fields, property_address, df_attom)
            df_final = asyncio.run(run_missing_retry(property_address, df_final, df_fields, county, county_url))

            st.success(f"✅ Report generated for {property_address}")
            st.dataframe(df_final[["Field", "Value"]], use_container_width=True)

            output = BytesIO()
            df_final.drop(columns=["Source"]).to_excel(output, index=False)
            st.download_button("⬇️ Download Report", data=output.getvalue(),
                               file_name=f"ReValix_{property_address.replace(' ', '_')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

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
            st.success(f"✅ Showing saved report for {search_address}")
            st.dataframe(df_past, use_container_width=True)
        else:
            st.error("❌ No records found for this address.")
