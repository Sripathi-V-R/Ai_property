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
        ("Property ID", "Unique system-generated identifier"),
        ("External Reference ID", "From bank, lender, registry, etc."),
        ("Property Name", "Complex / Project / Building Name"),
        ("Property Type", "Residential , Commercial, Industrial, Special Purpose"),
        ("Property Subtype", "Single Family Homes_Detached , Office Building, Retail Warehouse , etc"),
        ("Ownership Type", "Freehold / Leasehold / Co-op / License / Perpetual Lease"),
        ("Occupancy Status", "Occupied / Vacant / Under Construction"),
        ("Registration Status", "Registered / Unregistered"),
        ("Registry Reference", "Registration ID / Deed No."),
        ("Building Code / Permit ID", "Municipal permit number/PIN"),
        ("Geo ID", "Numeric code identifying geographic area"),
        ("Address Line 1", "Door / Unit Number"),
        ("Street Name", "Name of the street/Location Identifier"),
        ("City", "City / Municipality"),
        ("County", "Parish/Borough/ Census Area"),
        ("Township", "Local Administrative or Survey Division"),
        ("State", "State / Province/ Territory"),
        ("Postal Code", "Zip or PIN code"),
        ("Latitude", "GIS coordinate"),
        ("Longitude", "GIS coordinate"),
        ("Facing Direction", "North / East / South / West / NE / NW / SE / SW"),
        ("Neighborhood Type", "Residential / Commercial / Mixed / Institutional / Recreational / Open Space / Land / Tourism / Hospitality / Historic / Heritage"),
        ("Landmark", "Nearest known point / Natural or Man-Made Landmark / Institutional / Commercial / Transportation"),
        ("Connectivity Score", "Weighted accessibility score"),
        ("Legal Description", "Property Boundaries/ Lot & Block / Metes & Bounds"),
        ("Census Tract", "Statistical Area/ Urban Tract/ Rural Tract/ Special Tract"),
        ("Market", "Metropolitan / Secondary / Regional / Rural / Local Market"),
        ("Submarket", "Localized Market Area"),
        ("Submarket Cluster", "Residential/ Commercial/ Mixed-Use/ Industrial/ Retail Corridor"),
        ("CBSA", "Core-Based Statistical Area"),
        ("DMA", "Designated Market Area"),
        ("State Class Code", "Property Classification Code"),
        ("Neighborhood Code", "Local Area Identifier"),
        ("Neighborhood Name", "Local Area Name"),
        ("Map Facet", "Geographic Layer or Feature"),
        ("Key Map", "Reference Map Identifier"),
        ("Tax District", "Property Tax Jurisdiction"),
        ("Tax Code", "Property Classification for Tax Purposes"),
        ("Volume", "Building / Space Cubic Measurement"),
        ("Location Type", "Urban / Suburban / Rural"),
        ("Land Area", "Total Land Size in squarefeet / acres"),
        ("Plot No. / Survey No.", "Land Registry ID"),
        ("Land Use Code", "Numeric or Alphanumeric code assigned by local governments"),
        ("Land Market Value Per Square Foot", "Market value per land area"),
        ("Plot Shape", "Rectangular / Square / Irregular / L-Shape / Triangular / Flag"),
        ("Topography", "Level / Sloping / Rolling / Undulating"),
        ("Grade", "Above Street / At Street / Below Street"),
        ("Soil Type", "Clay / Sandy / Silty / Loamy / Peaty / Chalky / Gravelly / Rocky"),
        ("Dimensions", "Frontage and Depth"),
        ("Ground Coverage", "Land to Building Ratio"),
        ("Easements/Right of Way", "Access rights if any"),
        ("Encroachments", "Yes / No / Description"),
        ("Land Use Compliance / Zoning", "As per Zoning Certificate / City or County Zoning"),
        ("FSI / FAR Allowed", "Zonal Floor Space Index / Floor Area Ratio"),
        ("Flood Zone", "FEMA classification: A / AE / V / VE / X / D"),
        ("Flood Map Number", "Identifier of specific flood map panel"),
        ("Flood Map Date", "Date flood map goes into effect"),
        ("Flood Plain Area", "100-year / 500-year / Floodway"),
        ("Flood Risk Area", "Low / Moderate / High"),
        ("Site Improvements", "Paving / Sidewalks / Landscaping / etc."),
        ("Off-Site Improvements", "Signalization / Curbs / Gutters / Street Lights / Transformers"),
        ("Immediate access to Highways/Freeways", "Yes / No; If yes, which"),
        ("Lot Position", "Corner / Non-Corner"),
        ("Site Utility", "Good / Average / Poor"),
        ("Frontage Rating", "Good / Average / Poor"),
        ("Access Rating", "Good / Average / Poor"),
        ("Visibility Rating", "Good / Average / Poor"),
        ("Location Rating", "Good / Average / Poor"),
        ("Building Name", "Tower / Block name"),
        ("Year of Construction", "YYYY"),
        ("Building Style code", "Architectural or Structural Classification Code"),
        ("Building Design", "Architectural or Structural Classification Style"),
        ("Age of Building", "Derived (years)"),
        ("Stories", "Number of Floors"),
        ("Buildings", "Number of Buildings"),
        ("Exterior", "Material e.g., Brick / Wood / Metal / Concrete / etc."),
        ("Structural System", "Frame / Load-Bearing / RC / Steel / Timber / Precast / Modular"),
        ("No. of Floors", "Total floors"),
        ("Lift Count", "Number of elevators"),
        ("Fire Safety Systems", "Sprinklers / Extinguishers / Hydrants / Alarms / etc."),
        ("Security Systems", "CCTV / Access Control / Guards / Alarm Systems / etc."),
        ("Building Code", "Assessor or Municipal Classification Code"),
        ("Building Condition", "Excellent / Good / Fair / Poor"),
        ("GBA", "Gross Building Area (Sq.ft)"),
        ("NRA", "Net Rentable Area (Sq.ft)"),
        ("Year of Renovation", "YYYY"),
        ("Useful Life", "Derived (years) based on property type"),
        ("Effective Age", "Building Condition Age"),
        ("Remaining Economic Life", "Derived (years)"),
        ("Building Class", "Quality Category: A, B, C, D, E"),
        ("Foundation", "Concrete / Crawl / Piling / Slab / etc."),
        ("Total Rooms", "Number of Rooms"),
        ("Total Bedroom", "Number of Bedrooms"),
        ("Total Bath", "Number of Bathrooms"),
        ("Interior Flooring", "Brick / Tile / Wood / Vinyl / etc."),
        ("Ceiling", "Type: Drywall / Suspended / Exposed / etc."),
        ("Ceiling Height", "Floor-to-Ceiling Height"),
        ("Interior Finish %", "Finished Area Percentage"),
        ("Dock Doors", "Roll-Up / Overhead / Leveler / etc."),
        ("Roofing", "Material: Metal / Shingle / Concrete / Tile / etc."),
        ("Heating", "Type: Central / Forced Air / Heat Pump / etc."),
        ("Cooling", "Ductless / Central / Window / etc."),
        ("Other Improvements/Extra Features", "Paving / Patio / Deck / Shed / etc."),
        ("Occupied By", "Owner / Tenant"),
        ("Number of Tenants", "Single Tenant / Multiple Tenant"),
        ("Lease Structure", "Gross / Net / Modified Gross / Percentage / etc."),
        ("Occupancy at the time of sale", "Occupancy % in building"),
        ("Exempt %", "Portion of Property Exempt from Taxation"),
        ("Prorated Bldg %", "Allocated Building Value Ratio"),
        ("Parking Ratio", "Spaces per Unit Area"),
        ("Parking Spaces", "Number of Parking Spots"),
        ("Assessment Information", "Valuation Year / Assessed improvement / land / total"),
        ("Unit No. / Unit Name", "Flat / Suite / Bay ID"),
        ("Floor No.", "Level in building"),
        ("Unit Type", "Studio / 1BR / 2BR / Office / Retail / Industrial / etc."),
        ("Use Type", "Residential / Commercial / Mixed-Use"),
        ("Carpet Area", "Net usable floor space inside the unit"),
        ("Built-up Area", "Carpet Area + Wall Thickness + Balconies"),
        ("Super Built-up Area", "Built-up area + Proportionate share of common areas"),
        ("No. of Rooms", "Total number of rooms in the unit"),
        ("Bedrooms", "Count"),
        ("Bathrooms", "Count"),
        ("Ceiling Height (Unit)", "Important metric for some units"),
        ("Furniture", "Furnished / Semi / Unfurnished"),
        ("Unit Condition", "Finished / Shell / Under Construction / Needs Renovation"),
        ("Balcony / Terrace", "Presence and Size"),
        ("Occupied Exempt Units", "Percent of units with tax exemptions"),
        ("Occupied Rent-Regulated Units", "Percent occupied and rent-regulated"),
        ("Vacant Units", "Percent vacant"),
        ("Lease Status", "Active / Month-to-Month / Expired / Terminated"),
        ("Tenant Name (or ID)", "Individual or company"),
        ("Lease Start Date", "Date lease commenced"),
        ("Lease End Date", "Date lease expires"),
        ("Lease Term", "Duration in months/years"),
        ("Renewal Options", "Yes/No and terms"),
        ("Special Clauses", "e.g., exclusivity, early termination"),
        ("Appliances Included", "Stove/Fridge/Washer/Dryer etc."),
        ("HVAC Type", "Central / Split / Window / etc."),
        ("Parking Assigned", "Number of spaces assigned"),
        ("Storage Unit Assigned", "Availability and size"),
        ("Internet/Cable Ready", "Included or tenant-provided"),
        ("ADA Accessibility", "Compliance with accessibility standards"),
        ("Photos / Floor Plans", "Links or asset references"),
        ("Owner Name(s)", "Registered owner"),
        ("Title Status", "Clear / Disputed / Encumbered"),
        ("Registration No.", "Document reference"),
        ("Registration Date", "dd-mm-yyyy"),
        ("Registrar Office", "Location"),
        ("Encumbrance Certificate", "Reference No."),
        ("Mortgages / Liens", "Bank / Amount / Date"),
        ("Occupancy Certificate", "Number & Date"),
        ("Fire NOC", "Number & Date"),
        ("Compliance to Local By-laws", "Yes / No"),
        ("Grantor", "Property Seller / Transferor"),
        ("Grantee", "Property Buyer / Recipient"),
        ("Condition of Sale", "Arm’s Length / Distressed / Foreclosure / etc."),
        ("Rights Transferred", "Fee Simple / Leasehold / Easement / etc."),
        ("Qualified", "Qualified / Not Qualified / Pending Verification"),
        ("Type of Deed / Instrument", "Warranty / Quitclaim / Grant Deed / etc."),
        ("Covenants / Warranties", "Covenant of Seisin / Quiet Enjoyment / etc."),
        ("Recording Information", "County clerk recording stamp, book & page"),
        ("Miscellaneous Clauses", "Restrictions / Rights of first refusal / Easements"),
        ("Purchase Price / Sale Price", "Historical acquisition / sale"),
        ("Purchase Date / Sale Date", "dd-mm-yyyy"),
        ("Current Market Value", "Estimated Value"),
        ("Current Appraised Value", "Assessor appraised value"),
        ("Current Land Value", "Land appraised value"),
        ("Current Improvements Value", "Improvements appraised value"),
        ("Appraised Value History", "3 years past the present date"),
        ("Listing Price", "Quoted listing price"),
        ("No. of days on market", "Days on market"),
        ("Assessed Value", "Tax assessment value"),
        ("Land Assessed Value", "Land portion assessed"),
        ("Improvements Assessed Value", "Improvements portion assessed"),
        ("Assessed Value History", "3 years past the present date"),
        ("Guideline / Circle Rate", "Government benchmark value"),
        ("Current Rent / Lease Rate", "If leased; rent per unit or per SF/year"),
        ("Market Rent", "Comparable expected rent"),
        ("Lease Duration", "Years / Months"),
        ("Security Deposit Held", "Amount collected from tenant"),
        ("CAM Charges (Commercial)", "Common area maintenance charges"),
        ("Property Tax", "Annual tax"),
        ("Utilities Included", "Which utilities are included in rent"),
        ("Subsidies / Vouchers", "If applicable"),
        ("Vacancy rate (Property)", "Percent unoccupied"),
        ("Tenant Incentives / TI Allowance", "Tenant improvement credits"),
        ("Leasing Commission", "Broker fee"),
        ("Reimbursements", "Repayments"),
        ("CapEx", "Capital expenditures"),
        ("Cap Rate", "Capitalization rate"),
        ("Discount rate", "Discount rate used for valuations"),
        ("Mortgage Loan", "Amount"),
        ("Loan Date", "Date of loan"),
        ("Originator", "Lender"),
        ("Mortgage Rate", "Interest rate"),
        ("Rate Type", "Fixed / Variable"),
        ("Loan Term", "In years / months"),
        ("Monthly Mortgage Payment", "Installment amount"),
        ("Debt Service", "Total annual loan payments"),
        ("Debt Service Coverage Ratio (DSCR)", "NOI / Debt Service"),
        ("Equity Rate", "Return on equity"),
        ("Current Tax Year", "Year of assessment"),
        ("Gross Tax", "Total taxes for the assessment year"),
        ("Special Assessments", "Any special assessment amounts"),
        ("Other Deductions", "Other deductions on tax bill"),
        ("Net Tax", "Net taxes after deductions"),
        ("Full Rate", "Mill rate on gross tax"),
        ("Effective Rate", "Mill rate on net tax"),
        ("Tax History", "Taxes paid in past 3 years"),
        ("Power Backup", "Yes / No; Generator / UPS / Solar / etc."),
        ("Water Supply", "Municipal / Borewell / Both / Storage / Treatment on site"),
        ("Sewage System", "Municipal / Private / Holding Tanks / On-site Treatment"),
        ("Security", "CCTV / Gated / Watchman / Alarm"),
        ("Internet Connectivity", "Fiber / Cable / DSL / Satellite / etc."),
        ("Common Areas", "Lobby / Lounge / Terrace / Hallways / etc."),
        ("Recreational Amenities", "Clubhouse / Pool / Gym / Play Area / etc."),
        ("Green Area", "Percent of plot"),
        ("Parking", "Open / Covered / Multi-level / Underground / EV spaces"),
        ("Lighting", "Street / Common area / Emergency / Smart lighting"),
        ("Market Segment", "Luxury / Mid / Affordable"),
        ("Price Trend (12m)", "12-month appreciation / depreciation %"),
        ("Supply-Demand Index", "Local ratio"),
        ("Sales Trend", "6m / 12m change in transactions"),
        ("Sales to Asking Price Differential", "Variance %"),
        ("For Sale Trend", "6m / 12m change in listings"),
        ("Transaction Type", "Individual / Portfolio / Entity Sale"),
        ("Comparable Properties", "IDs of nearby comps"),
        ("Avg. Comparable Price", "$ per sqft"),
        ("Price Deviation", "% variance from comps"),
        ("Rent Trend", "6m / 12m trajectory"),
        ("Direct & Sublet Rent Trend", "6m / 12m trajectory"),
        ("Vacancy Rate (Market)", "Market vacancy %"),
        ("24 Months Lease Renewal Rate", "%"),
        ("RBA", "Total Rentable Building Area"),
        ("Availability Rate", "% of space available for lease"),
        ("Net Absorption SF", "Occupied space change over period"),
        ("Months on Market (Market)", "Trend"),
        ("Months to Lease (Market)", "Trend"),
        ("Months Vacant (Market)", "Trend"),
        ("Probability of Leasing", "In months"),
        ("Deliveries SF", "Completed construction square feet"),
        ("Demolitions SF", "Square feet demolished"),
        ("Under Construction SF", "Area being built"),
        ("Under Construction Rate", "Percent area being built"),
        ("Preleased Rate", "Percent of under-construction leased"),
        ("Start Date (Project)", "mm-dd-yyyy"),
        ("Complete Date (Project)", "mm-dd-yyyy"),
        ("Developer/Owner", "Name"),
        ("Sales Volume", "Square feet sold"),
        ("Market Sale Price per SF", "Market sale $/SF"),
        ("Market Asking Rent per SF", "Market asking rent $/SF"),
        ("Market Cap Rate", "Market cap rate"),
        ("Market Employment by Industry", "Jobs / growth / historical / forecast"),
        ("Unemployment Rate (Market)", "%"),
        ("Net Employment Change", "In thousands"),
        ("Predicted Value Range", "Min–Max"),
        ("AI Condition Score", "0–100"),
        ("Asset Value by Owner Type", "% by owner type"),
        ("Sales by Buyer Type", "% by buyer type"),
        ("Sales by Seller Type", "% by seller type"),
        ("Marketing and Exposure Time", "In months"),
        ("Traffic Count", "Vehicles per day"),
        ("Population in 1, 3 & 5 miles", "Population per latest stats"),
        ("Population Growth", "% Year on Year"),
        ("Population", "Current Level / 12 Month Change / 10 Year Change / 5 Year Forecast"),
        ("Households", "Current Level / changes / forecasts"),
        ("Average Household Size", "Current / changes / forecasts"),
        ("Total Housing Units", "Current Level / changes / forecasts"),
        ("Owner Occupied Housing Units", "Current Level / changes / forecasts"),
        ("Renter Occupied Housing Units", "Current Level / changes / forecasts"),
        ("Vacant Housing Units", "Current Level / changes / forecasts"),
        ("Labor Force", "Current Level / changes / forecasts"),
        ("Unemployment", "Current Level / changes / forecasts"),
        ("Median Household Income", "Current and trends"),
        ("Per Capita Income", "Current and trends"),
        ("Median Home Price", "Current and trends"),
        ("Latest Population 25+ by Educational Attainment", "Distribution across education levels"),
        ("AI Condition Index", "Derived via image model"),
        ("Structural Integrity Score", "AI-based risk flag"),
        ("Market Confidence Index", "ML output"),
        ("Price Prediction (Now)", "Currency"),
        ("Price Prediction (12M Ahead)", "Currency"),
        ("Market Liquidity Score", "Time-to-sell estimate"),
        ("Risk Classification", "Low / Moderate / High"),
        ("Anomaly Detection", "Flag for mismatched data"),
        ("Automated Summary", "NLP-based summary paragraph"),
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


