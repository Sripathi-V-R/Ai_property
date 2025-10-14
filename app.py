# ==============================================================
#  Streamlit - AI Property Intelligence Agent
#  (MongoDB + Factual Fields + Ordered Output)
#  Author: Ai Master | Powered by GPT-5
# ==============================================================

import streamlit as st
import pandas as pd
import os
from openai import OpenAI
from pymongo import MongoClient
import requests
import re
from io import BytesIO
from urllib.parse import quote_plus
from dotenv import load_dotenv

# --------------------------------------------------------------
# Environment Handling (Safe for Local + Streamlit Cloud)
# --------------------------------------------------------------

# ✅ Load .env locally if available
if os.path.exists(".env"):
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
else:
    # ✅ Use Streamlit Cloud secrets
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    MONGO_URI = st.secrets["MONGO_URI"]

# --------------------------------------------------------------
# Initialize Clients
# --------------------------------------------------------------
client = OpenAI(api_key=OPENAI_API_KEY)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["property_intelligence"]
collection = db["property_results"]

# --------------------------------------------------------------
# Streamlit App Config
# --------------------------------------------------------------
st.set_page_config(page_title="AI Property Intelligence Agent", layout="wide")
st.title("🏠 AI Property Intelligence Agent")
st.caption("Factual, ordered property data — auto-saved to MongoDB and retrievable anytime.")


# --------------------------------------------------------------
# Tabs
# --------------------------------------------------------------
tab1, tab2 = st.tabs(["🧠 Generate & Save Data", "📜 View Past Lookups"])

# --------------------------------------------------------------
# Field Template
# --------------------------------------------------------------
def load_field_template():
    data = [
        ("Property ID", "Unique identifier like Parcel Number, APN, or Tax ID."),
        ("External Reference ID", "From bank, lender, registry, etc."),
        ("Property Name", "Complex / Project / Building Name."),
        ("Property Type", "Residential, Commercial, Industrial, or Special Purpose."),
        ("Property Subtype", "Subtype such as Single Family, Office, Retail, etc."),
        ("Ownership Type", "Freehold / Leasehold / Co-op / License / Perpetual Lease."),
        ("Occupancy Status", "Occupied / Vacant / Under Construction."),
        ("Registration Status", "Registered / Unregistered."),
        ("Registry Reference", "Deed or Registration ID."),
        ("Address Line 1", "Street number or unit."),
        ("Street Name", "Street or road name."),
        ("City", "City or municipality."),
        ("County", "County, Parish, or Borough."),
        ("State", "State or province."),
        ("Postal Code", "Zip or PIN code."),
        ("Latitude", "GIS coordinate."),
        ("Longitude", "GIS coordinate."),
        ("Lot Size", "Total land area (sqft/acres)."),
        ("Year of Construction", "Year built."),
        ("Building Condition", "Excellent / Good / Fair / Poor."),
        ("Owner Name(s)", "Registered owner(s)."),
        ("Last Sale Price", "Most recent sale amount."),
        ("Last Sale Date", "Date of last recorded sale."),
        ("Assessed Value", "Value used for taxation."),
        ("Market Value", "Current estimated market value."),
        ("Tax Year", "Latest assessment year."),
        ("Tax Amount", "Total property taxes for that year."),
        ("Zoning", "Zoning classification per local government."),
        ("Flood Zone", "FEMA or local flood zone classification."),
        ("Legal Description", "Official land parcel or lot boundary description."),
        ("Mortgage / Liens", "Outstanding loans or encumbrances."),
        ("HOA Name", "Homeowners Association name (if applicable)."),
        ("HOA Fees", "Monthly or annual HOA dues."),
        ("Energy Rating", "LEED / Energy Star / Green certification."),
        ("Utilities Included", "Which utilities are included."),
        ("Parking Spaces", "Total number of vehicle spaces."),
        ("Neighborhood Type", "Residential / Commercial / Mixed-use."),
        ("Market Cap Rate", "Capitalization rate for the market."),
        ("NOI", "Net Operating Income."),
        ("Crime Index", "Neighborhood crime risk indicator."),
        ("Walk Score", "Walkability index."),
        ("Air Quality Index", "EPA or equivalent measure."),
        ("Condition of Sale", "Arm’s Length / Distressed / Auction."),
        ("Transaction Type", "Individual / Portfolio / Entity Sale."),
        ("Developer / Owner", "Developer or Owner entity name."),
    ]
    return pd.DataFrame(data, columns=["Field", "Description"])

df_fields = load_field_template()

# --------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------
def detect_county_and_state(address):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={quote_plus(address)}&format=json&addressdetails=1"
        headers = {"User-Agent": "AiMaster-Property-Agent"}
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        if data and "address" in data[0]:
            addr = data[0]["address"]
            return addr.get("county", ""), addr.get("state", "")
    except Exception:
        pass
    return "", ""


def find_county_website(county, state):
    if not county or not state:
        return None
    try:
        res = client.responses.create(
            model="gpt-4.1-mini",
            input=f"Provide the official government website URL for {county} County, {state}, USA. Return only the verified URL (no explanation)."
        )
        content = res.output[0].content[0].text.strip()
        match = re.search(r'https?://[^\s]+', content)
        return match.group(0) if match else content
    except Exception:
        return None


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
                records.append({"Field": field, "Value": value, "Source": "Other Government Records"})
    return records


def call_api(prompt):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a verified property intelligence engine. Return factual Field–Value–Source tables only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    return response.choices[0].message.content


def build_prompt(address, field_list, source_group, county_name, county_url):
    sources_str = "\n".join(f"- {s}" for s in source_group)
    field_defs = "\n".join([f"{f}: {d}" for f, d in field_list])
    county_info = f"\nAlso verify via county site: {county_name} ({county_url})." if county_url else ""
    return f"""
You are a **Professional Real Estate Property Intelligence Engine**.

Task:
For property:
**{address}**

Search these verified sources:
{sources_str}
{county_info}

Use these field definitions:
{field_defs}

Return table:
| Field | Value | Source |

Rules:
- Fill factual values.
- Keep order.
- If missing, return "NotFound".
- Include verified Source.
"""


def merge_and_save(df_ai, df_fields, property_address):
    merged = (
        df_ai.groupby("Field", as_index=False)
        .agg({
            "Value": lambda vals: next((v for v in vals if v and v != "NotFound"), "NotFound"),
            "Source": lambda vals: next((s for s in vals if s and s != ""), "Other Government Records")
        })
    )
    df_final = pd.merge(df_fields[["Field"]], merged, on="Field", how="left")
    df_final["Value"] = df_final["Value"].fillna("NotFound")
    df_final["Source"] = df_final["Source"].fillna("Other Government Records")

    # Save to MongoDB
    doc = {"address": property_address, "records": df_final.to_dict(orient="records")}
    collection.replace_one({"address": property_address}, doc, upsert=True)

    df_final["Field"] = pd.Categorical(df_final["Field"], categories=df_fields["Field"], ordered=True)
    df_final = df_final.sort_values("Field").reset_index(drop=True)
    return df_final[["Field", "Value", "Source"]]


def highlight_cells(val):
    if val == "NotFound":
        return "background-color: #ffcccc; color: #b30000; font-weight: 600;"
    else:
        return "background-color: #e6ffe6; color: #006600;"

# ==============================================================
# 🧠 TAB 1: GENERATE & SAVE
# ==============================================================
with tab1:
    property_address = st.text_input("🏡 Enter Full Property Address:")
    sources = [
        "Zillow", "Trulia", "Costar", "MLS", "Realtor", "Redfin", "Attom", "LoopNet",
        "Corelogic", "Realtytrac", "HouseCanary", "Reonomy", "County Assessor",
        "County Clerk / Recorder / Deeds", "County Tax Office", "Google Maps", "Any Government Records"
    ]
    mid = len(sources)//2
    sources_a, sources_b = sources[:mid], sources[mid:]

    if st.button("🚀 Generate & Save to MongoDB"):
        if not property_address.strip():
            st.warning("⚠️ Please enter a property address first.")
        else:
            with st.spinner("Detecting county and fetching verified data..."):
                county, state = detect_county_and_state(property_address)
                county_url = find_county_website(county, state)

            if county:
                st.success(f"📍 County Detected: **{county}, {state}**")
            if county_url:
                st.info(f"🌐 County Site: {county_url}")

            field_list = list(zip(df_fields["Field"], df_fields["Description"]))
            st.info("🔍 Fetching and mapping property data from verified sources...")

            output_a = call_api(build_prompt(property_address, field_list, sources_a, county, county_url))
            output_b = call_api(build_prompt(property_address, field_list, sources_b, county, county_url))

            df_ai = pd.DataFrame(parse_table(output_a) + parse_table(output_b))
            df_final = merge_and_save(df_ai, df_fields, property_address)

            st.success(f"✅ Data for {property_address} saved to MongoDB.")
            st.dataframe(df_final[["Field", "Value"]].style.applymap(highlight_cells, subset=["Value"]), use_container_width=True)

            output = BytesIO()
            df_final.drop(columns=["Source"]).to_excel(output, index=False)
            st.download_button(
                label="⬇️ Download Excel (Field + Value)",
                data=output.getvalue(),
                file_name=f"property_data_{property_address.replace(',', '').replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.caption("🟩 Green = Found | 🟥 Red = NotFound | Data stored in MongoDB with sources.")

# ==============================================================
# 📜 TAB 2: VIEW PAST LOOKUPS
# ==============================================================
with tab2:
    st.subheader("🔎 View Property Data from MongoDB")
    search_address = st.text_input("🏠 Enter Property Address to Search:")
    if st.button("🔍 Search in MongoDB"):
        if not search_address.strip():
            st.warning("⚠️ Please enter an address.")
        else:
            doc = collection.find_one({"address": search_address})
            if doc:
                df_past = pd.DataFrame(doc["records"])[["Field", "Value"]]
                st.success(f"✅ Showing saved results for: {search_address}")
                st.dataframe(df_past.style.applymap(highlight_cells, subset=["Value"]), use_container_width=True)
            else:
                st.error("❌ No record found for this address in MongoDB.")

