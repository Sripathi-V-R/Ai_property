# ==============================================================
#  🏙️ ReValix AI Property Intelligence
#  (GPT-5 Factual + Web Scraper + Async Fetch + MongoDB Storage)
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
from bs4 import BeautifulSoup
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
# STREAMLIT CONFIG + THEME
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
    background: rgba(255,255,255,0.9);
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    padding: 2rem;
    backdrop-filter: blur(10px);
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
st.markdown("<div class='revalix-sub'>GPT-5 Factual Mode with Real Web Data</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🧠 Generate Intelligence", "📜 View Past Reports"])

# --------------------------------------------------------------
# FIELD TEMPLATE
# --------------------------------------------------------------
def load_field_template():
    fields = [
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
    return pd.DataFrame(fields, columns=["Field", "Description"])

df_fields = load_field_template()

# --------------------------------------------------------------
# COUNTY DETECTION
# --------------------------------------------------------------
def detect_county_and_state(address):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={quote_plus(address)}&format=json&addressdetails=1"
        res = requests.get(url, headers={"User-Agent": "ReValix-Agent"}, timeout=10)
        data = res.json()
        if data and isinstance(data, list):
            addr = data[0]["address"]
            return addr.get("county", ""), addr.get("state", "")
    except Exception:
        pass
    return "", ""

# --------------------------------------------------------------
# WEB SCRAPER
# --------------------------------------------------------------
def scrape_property_sources(address):
    """Fetch snippets from Zillow, Realtor, LoopNet, and OpenStreetMap."""
    address_q = quote_plus(address)
    snippets = []

    urls = [
        f"https://www.zillow.com/homes/{address_q}/",
        f"https://www.realtor.com/realestateandhomes-search/{address_q}",
        f"https://www.loopnet.com/search/commercial-real-estate/{address_q}/",
        f"https://nominatim.openstreetmap.org/search?q={address_q}&format=json&addressdetails=1"
    ]

    for url in urls:
        try:
            html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
            soup = BeautifulSoup(html, "html.parser")
            text = " ".join(soup.stripped_strings)
            snippets.append(f"### Source: {url}\n{text[:4000]}")
        except Exception as e:
            snippets.append(f"### Source: {url}\nError fetching: {e}")

    return "\n\n".join(snippets)

# --------------------------------------------------------------
# GPT PROMPT BUILDER
# --------------------------------------------------------------
def build_prompt(address, field_list, section_name, county_name, county_url, scraped_text):
    field_defs = "\n".join([f"- {f}: {d}" for f, d in field_list])
    county_info = f"\nCounty info: {county_name} ({county_url})" if county_url else ""

    return f"""
You are **ReValix AI**, a real estate intelligence system.

Your task is to extract verified and realistic property details for:
🏠 {address}

Section: {section_name}

Use the factual web snippets below as your data source:
{scraped_text}

{county_info}

---
### Fields:
{field_defs}

Return ONLY this Markdown table:

| Field | Value | Confidence | Source |
|-------|--------|-------------|--------|
Rules:
- Confidence = High / Medium / Low
- Include real data where possible.
- Avoid "NotFound" unless no info appears in sources.
"""

# --------------------------------------------------------------
# GPT-5 ASYNC CALL
# --------------------------------------------------------------
async def call_api_async(session, address, field_list, section_name, county, county_url):
    scraped_text = scrape_property_sources(address)
    prompt = build_prompt(address, field_list, section_name, county, county_url, scraped_text)

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-5",
        "messages": [
            {"role": "system", "content": "You extract factual real estate information and summarize it clearly."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2500
    }

    try:
        async with session.post("https://api.openai.com/v1/chat/completions",
                                json=payload, headers=headers, timeout=150) as resp:
            data = await resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"API call error for {section_name}: {e}")
        return ""

# --------------------------------------------------------------
# PARSE TABLE
# --------------------------------------------------------------
def parse_table(raw_output):
    records = []
    for line in raw_output.split("\n"):
        if "|" in line and not re.search(r"Field\s*\|\s*Value", line, re.IGNORECASE):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 4:
                records.append({
                    "Field": parts[0],
                    "Value": parts[1],
                    "Confidence": parts[2],
                    "Source": parts[3]
                })
    return records

# --------------------------------------------------------------
# MERGE + SAVE
# --------------------------------------------------------------
def merge_and_save(df_ai, df_fields, property_address):
    if df_ai.empty:
        df_ai = pd.DataFrame(columns=["Field", "Value", "Confidence", "Source"])
    merged = df_fields.merge(df_ai, on="Field", how="left")
    merged.fillna({"Value": "NotFound", "Confidence": "Low", "Source": "Unknown"}, inplace=True)
    collection.replace_one({"address": property_address},
                           {"address": property_address, "records": merged.to_dict(orient="records")},
                           upsert=True)
    return merged

# --------------------------------------------------------------
# UI - GENERATE TAB
# --------------------------------------------------------------
with tab1:
    st.markdown("### 🧠 Generate Property Intelligence")
    property_address = st.text_input("🏡 Enter Full Property Address:")

    if st.button("🚀 Generate Report", use_container_width=True):
        if not property_address.strip():
            st.warning("⚠️ Please enter a property address.")
        else:
            with st.spinner("Fetching and analyzing data..."):
                county, state = detect_county_and_state(property_address)
                county_url = f"https://www.{county.lower().replace(' ', '')}{state.lower().replace(' ', '')}.gov" if county and state else ""
                st.info(f"📍 County detected: {county}, {state}")

                async def process_sections():
                    async with aiohttp.ClientSession() as session:
                        tasks = []
                        for sec in ["Identification", "Location", "Building Details", "Land & Zoning", "Ownership & Status", "Market & Financial"]:
                            fields = df_fields[df_fields["Field"].isin(df_fields["Field"])][["Field", "Description"]].values.tolist()
                            tasks.append(call_api_async(session, property_address, fields, sec, county, county_url))
                        return await asyncio.gather(*tasks)

                results = asyncio.run(process_sections())
                all_records = []
                for content in results:
                    all_records.extend(parse_table(content))

                df_ai = pd.DataFrame(all_records)
                df_final = merge_and_save(df_ai, df_fields, property_address)

                st.success(f"✅ Report for {property_address} generated successfully.")
                st.dataframe(df_final[["Field", "Value", "Confidence", "Source"]], use_container_width=True)

                output = BytesIO()
                df_final.to_excel(output, index=False)
                st.download_button("⬇️ Download Report (Excel)", data=output.getvalue(),
                                   file_name=f"ReValix_{property_address.replace(' ', '_')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --------------------------------------------------------------
# UI - HISTORY TAB
# --------------------------------------------------------------
with tab2:
    st.markdown("### 📜 View Saved Reports")
    search_address = st.text_input("🏠 Search by Address:")
    if st.button("🔍 Retrieve Report", use_container_width=True):
        doc = collection.find_one({"address": search_address})
        if doc:
            df_past = pd.DataFrame(doc["records"])[["Field", "Value", "Confidence", "Source"]]
            st.success(f"✅ Showing saved report for: {search_address}")
            st.dataframe(df_past, use_container_width=True)
        else:
            st.error("❌ No record found for this address.")
