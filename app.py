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
from streamlit_lottie import st_lottie

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
    background: rgba(255,255,255,0.85);
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    padding: 2rem;
    backdrop-filter: blur(10px);
}
h1, h2, h3 { color: #0ea5e9 !important; }
.revalix-header { font-size: 2.4rem; text-align: center; color: #0ea5e9; font-weight: 800; }
.revalix-sub { text-align: center; font-size: 1.1rem; color: #334155; margin-bottom: 35px; }
.dataframe td { font-weight: 500; }
.highlight-red { color: red; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='revalix-header'>🏙️ ReValix AI Property Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='revalix-sub'>AI-Powered Property Data Enrichment</div>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🧠 Generate Intelligence", "📜 View Past Reports"])

# --------------------------------------------------------------
# LOTTIE LOADERS
# --------------------------------------------------------------
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

LOTTIE_LOADING = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_j1adxtyb.json")
LOTTIE_SUCCESS = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json")

# --------------------------------------------------------------
# FIELD TEMPLATE
# --------------------------------------------------------------
def load_field_template():
    data = [
        ("Property ID", "Unique system-generated identifier, Parcel no, APN etc."),
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
# SECTION MAPPING
# --------------------------------------------------------------
def get_field_sections(df_fields):
    sections = {
        # ----------------------------------------------------------
        # 1️⃣ Identification & Basic Property Info
        # ----------------------------------------------------------
        "Identification": [
            "Property ID", "External Reference ID", "Property Name",
            "Property Type", "Property Subtype", "Ownership Type",
            "Occupancy Status", "Registration Status", "Registry Reference",
            "Building Code / Permit ID", "Geo ID"
        ],

        # ----------------------------------------------------------
        # 2️⃣ Location & Geography
        # ----------------------------------------------------------
        "Location": [
            "Address Line 1", "Street Name", "City", "County", "Township",
            "State", "Postal Code", "Latitude", "Longitude",
            "Facing Direction", "Neighborhood Type", "Neighborhood Name",
            "Landmark", "Connectivity Score", "Legal Description",
            "Census Tract", "Market", "Submarket", "Submarket Cluster",
            "CBSA", "DMA", "State Class Code", "Neighborhood Code",
            "Map Facet", "Key Map", "Tax District", "Tax Code", "Location Type"
        ],

        # ----------------------------------------------------------
        # 3️⃣ Land & Site Details
        # ----------------------------------------------------------
        "Land Details": [
            "Land Area", "Plot No. / Survey No.", "Land Use Code",
            "Land Market Value Per Square Foot", "Plot Shape", "Topography",
            "Grade", "Soil Type", "Dimensions", "Ground Coverage",
            "Easements/Right of Way", "Encroachments",
            "Land Use Compliance / Zoning", "FSI / FAR Allowed",
            "Flood Zone", "Flood Map Number", "Flood Map Date",
            "Flood Plain Area", "Flood Risk Area",
            "Site Improvements", "Off-Site Improvements",
            "Immediate access to Highways/Freeways", "Lot Position",
            "Site Utility", "Frontage Rating", "Access Rating",
            "Visibility Rating", "Location Rating"
        ],

        # ----------------------------------------------------------
        # 4️⃣ Building & Structural Characteristics
        # ----------------------------------------------------------
        "Building Details": [
            "Building Name", "Year of Construction", "Building Style code",
            "Building Design", "Type", "Age of Building", "Stories", "Buildings",
            "Exterior", "Structural System", "No. of Floors", "Lift Count",
            "Fire Safety Systems", "Security Systems", "Building Code",
            "Building Condition", "GBA", "NRA", "Year of Renovation",
            "Useful Life", "Effective Age", "Remaining Economic Life",
            "Building Class", "Foundation", "Total Rooms", "Total Bedroom",
            "Total Bath", "Interior Flooring", "Ceiling", "Ceiling Height",
            "Interior Finish %", "Dock Doors", "Roofing", "Heating",
            "Cooling", "Other Improvements/Extra Features"
        ],

        # ----------------------------------------------------------
        # 5️⃣ Unit & Interior Level Details
        # ----------------------------------------------------------
        "Unit Details": [
            "Assessment Information", "Unit No. / Unit Name", "Floor No.",
            "Unit Type", "Use Type", "Carpet Area", "Built-up Area",
            "Super Built-up Area", "No. of Rooms", "Bedrooms", "Bathrooms",
            "Ceiling Height", "Furniture", "Unit Condition",
            "Balcony / Terrace / Private Outdoor Space", "Occupancy Status",
            "Occupied Exempt Units", "Occupied Rent-Regulated Units",
            "Vacant Units", "Appliances Included", "HVAC Type",
            "Parking Assigned", "Storage Unit Assigned", "Internet/Cable Ready",
            "ADA Accessibility", "Photos / Floor Plans"
        ],

        # ----------------------------------------------------------
        # 6️⃣ Tenancy, Lease & Occupancy
        # ----------------------------------------------------------
        "Tenancy and Lease": [
            "Occupied By", "Number of Tenants", "Lease Structure",
            "Occupancy at the time of sale", "Exempt %", "Prorated Bldg %",
            "Parking Ratio", "Parking Spaces", "Lease Status",
            "Tenant Name (or ID)", "Lease Start Date", "Lease End Date",
            "Lease Term", "Renewal Options", "Special Clauses",
            "Current Rent / Lease Rate", "Market Rent", "Lease Duration",
            "Security Deposit Held", "CAM Charges (Commercial)",
            "Utilities Included", "Subsidies / Vouchers (if any)",
            "Vacancy rate", "Tenant Incentives / TI Allowance",
            "Leasing Commission", "Reimbursements"
        ],

        # ----------------------------------------------------------
        # 7️⃣ Ownership, Title & Legal
        # ----------------------------------------------------------
        "Ownership and Legal": [
            "Owner Name(s)", "Title Status", "Registration No.",
            "Registration Date", "Registrar Office", "Encumbrance Certificate",
            "Mortgages / Liens", "Occupancy Certificate", "Fire NOC",
            "Compliance to Local By-laws", "Grantor", "Grantee",
            "Condition of Sale", "Rights Transferred", "Qualified",
            "Type of Deed / Instrument", "Covenants / Warranties",
            "Recording Information", "Miscellaneous Clauses"
        ],

        # ----------------------------------------------------------
        # 8️⃣ Market, Sales & Financial Valuation
        # ----------------------------------------------------------
        "Market and Financial": [
            "Purchase Price / Sale Price", "Purchase Date / Sale Date",
            "Current Market Value", "Current Appaised Value",
            "Current Land Value", "Current Improvements Value",
            "Appraised Value History", "Listing Price", "No. of days on market",
            "Assessed Value", "Land Assessed Value", "Improvements Assessed Value",
            "Assessed Value History", "Guideline / Circle Rate", "CapEx",
            "Cap Rate", "Discount rate", "Mortgage Loan", "Loan Date",
            "Originator", "Mortgage Rate", "Rate Type", "Loan Term",
            "Monthly Mortgage Payment", "Debt Service",
            "Debt Service Coverage Ratio (DSCR)", "Equity Rate"
        ],

        # ----------------------------------------------------------
        # 9️⃣ Taxes & Assessments
        # ----------------------------------------------------------
        "Tax and Assessment": [
            "Current Tax Year", "Gross Tax", "Special Assessments",
            "Other Deductions", "Net Tax", "Full Rate", "Effective Rate",
            "Tax History", "Property Tax"
        ],

        # ----------------------------------------------------------
        # 🔟 Amenities, Infrastructure & Utilities
        # ----------------------------------------------------------
        "Amenities and Utilities": [
            "Power Backup", "Water Supply", "Sewage System",
            "Security", "Internet Connectivity", "Common Areas",
            "Recreational Amenities", "Green Area", "Parking", "Lighting"
        ],

        # ----------------------------------------------------------
        # 11️⃣ Market Dynamics & Performance
        # ----------------------------------------------------------
        "Market Performance": [
            "Market Segment", "Price Trend (12m)", "Supply-Demand Index",
            "Sales Trend", "Sales to Asking Price Differential",
            "For Sale Trend", "Transaction Type", "Comparable Properties",
            "Avg. Comparable Price", "Price Deviation", "Rent Trend",
            "Direct & Sublet Rent Trend", "Vacancy Rate",
            "24 Months Lease Renewal Rate", "RBA", "Availability Rate",
            "Net Absorption SF", "Months on Market", "Months to Lease",
            "Months Vacant", "Probability of Leasing", "Deliveries SF",
            "Demolitions SF", "Under Construction SF",
            "Under Construction Rate", "Preleased Rate", "Start Date",
            "Complete Date", "Developer/Owner", "Sales Volume",
            "Market Sale Price per SF", "Market Asking Rent per SF",
            "Market Cap Rate", "Market Employment by Industry",
            "Unemployment Rate", "Net Employment Change",
            "Predicted Value Range"
        ],

        # ----------------------------------------------------------
        # 12️⃣ Demographics & Socioeconomic Indicators
        # ----------------------------------------------------------
        "Demographics": [
            "Traffic Count", "Census Tract", "Population in 1, 3 & 5 miles",
            "Population Growth", "Population", "Households",
            "Average Household Size", "Total Housing Units",
            "Owner Occupied Housing Units", "Renter Occupied Housing Units",
            "Vacant Housing Units", "Labor Force", "Unemployment",
            "Median Household Income", "Per Capita Income",
            "Median Home Price", "Latest Population 25+ by Educational Attainment"
        ],

        # ----------------------------------------------------------
        # 13️⃣ AI, Predictive & Risk Analytics
        # ----------------------------------------------------------
        "AI and Predictive Analytics": [
            "AI Condition Score", "AI Condition Index", "Structural Integrity Score",
            "Market Confidence Index", "Price Prediction (Now)",
            "Price Prediction (12M Ahead)", "Market Liquidity Score",
            "Risk Classification", "Anomaly Detection", "Automated Summary",
            "Asset Value by Owner Type", "Sales by Buyer Type", "Sales by Seller Type",
            "Marketing and Exposure Time"
        ],
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
# ATTOM FETCH + FLATTEN
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
    except Exception:
        return []

def flatten_attom_properties(properties):
    rows = []
    for p in properties:
        r = {}
        # --------------------------------------------------------------
        # ADDRESS
        # --------------------------------------------------------------
        r["Address Country"] = safe_get(p, ["address", "country"])
        r["Address State"] = safe_get(p, ["address", "countrySubd"])
        r["Address Line 1"] = safe_get(p, ["address", "line1"])
        r["Address Line 2"] = safe_get(p, ["address", "line2"])
        r["Address City"] = safe_get(p, ["address", "locality"])
        r["Address Match Code"] = safe_get(p, ["address", "matchCode"])
        r["Address OneLine"] = safe_get(p, ["address", "oneLine"])
        r["Postal Code 1"] = safe_get(p, ["address", "postal1"])
        r["Postal Code 2"] = safe_get(p, ["address", "postal2"])
        r["Postal Code 3"] = safe_get(p, ["address", "postal3"])

        # --------------------------------------------------------------
        # AREA
        # --------------------------------------------------------------
        r["Census Block Group"] = safe_get(p, ["area", "censusBlockGroup"])
        r["Census Tract Ident"] = safe_get(p, ["area", "censusTractIdent"])
        r["Country Sec Subd"] = safe_get(p, ["area", "countrySecSubd"])
        r["Subdivision Name"] = safe_get(p, ["area", "subdName"])
        r["Subdivision Tract Num"] = safe_get(p, ["area", "subdTractNum"])

        # --------------------------------------------------------------
        # ASSESSMENT
        # --------------------------------------------------------------
        r["Appraised Value"] = safe_get(p, ["assessment", "appraised"])
        r["Assessed Improvement Value"] = safe_get(p, ["assessment", "assessed", "assdImprValue"])
        r["Assessed Land Value"] = safe_get(p, ["assessment", "assessed", "assdLandValue"])
        r["Assessed Total Value"] = safe_get(p, ["assessment", "assessed", "assdTtlValue"])
        r["Delinquent Year"] = safe_get(p, ["assessment", "delinquentyear"])
        r["Improvement Percent"] = safe_get(p, ["assessment", "improvementPercent"])
        r["Market Improvement Value"] = safe_get(p, ["assessment", "market", "mktImprValue"])
        r["Market Land Value"] = safe_get(p, ["assessment", "market", "mktLandValue"])
        r["Market Total Value"] = safe_get(p, ["assessment", "market", "mktTtlValue"])

        # --------------------------------------------------------------
        # MORTGAGE
        # --------------------------------------------------------------
        r["First Mortgage Amount"] = safe_get(p, ["assessment", "mortgage", "FirstConcurrent", "amount"])
        r["First Mortgage Lender First Name"] = safe_get(p, ["assessment", "mortgage", "FirstConcurrent", "lenderFirstName"])
        r["First Mortgage Lender Last Name"] = safe_get(p, ["assessment", "mortgage", "FirstConcurrent", "lenderLastName"])
        r["First Mortgage Document Number"] = safe_get(p, ["assessment", "mortgage", "FirstConcurrent", "trustDeedDocumentNumber"])
        r["Second Mortgage Amount"] = safe_get(p, ["assessment", "mortgage", "SecondConcurrent", "amount"])
        r["Second Mortgage Lender First Name"] = safe_get(p, ["assessment", "mortgage", "SecondConcurrent", "lenderFirstName"])
        r["Second Mortgage Lender Last Name"] = safe_get(p, ["assessment", "mortgage", "SecondConcurrent", "lenderLastName"])
        r["Second Mortgage Document Number"] = safe_get(p, ["assessment", "mortgage", "SecondConcurrent", "trustDeedDocumentNumber"])

        # --------------------------------------------------------------
        # OWNER
        # --------------------------------------------------------------
        r["Absentee Owner Status"] = safe_get(p, ["assessment", "owner", "absenteeOwnerStatus"])
        r["Corporate Owner Indicator"] = safe_get(p, ["assessment", "owner", "corporateIndicator"])
        r["Mailing Address OneLine"] = safe_get(p, ["assessment", "owner", "mailingAddressOneLine"])
        r["Owner 1 Name"] = safe_get(p, ["assessment", "owner", "owner1", "fullName"])
        r["Owner 2 Name"] = safe_get(p, ["assessment", "owner", "owner2", "fullName"])
        r["Owner 3 Name"] = safe_get(p, ["assessment", "owner", "owner3", "fullName"])
        r["Owner 4 Name"] = safe_get(p, ["assessment", "owner", "owner4", "fullName"])

        # --------------------------------------------------------------
        # TAX
        # --------------------------------------------------------------
        r["Tax Amount"] = safe_get(p, ["assessment", "tax", "taxAmt"])
        r["Tax Year"] = safe_get(p, ["assessment", "tax", "taxYear"])
        r["Tax Exemption"] = safe_get(p, ["assessment", "tax", "exemption"])
        r["Homeowner Exemption"] = safe_get(p, ["assessment", "tax", "exemptiontype", "Homeowner"])
        r["Veteran Exemption"] = safe_get(p, ["assessment", "tax", "exemptiontype", "Veteran"])

        # --------------------------------------------------------------
        # BUILDING - CONSTRUCTION & INTERIOR
        # --------------------------------------------------------------
        r["Building Condition"] = safe_get(p, ["building", "construction", "condition"])
        r["Construction Type"] = safe_get(p, ["building", "construction", "constructionType"])
        r["Foundation Type"] = safe_get(p, ["building", "construction", "foundationType"])
        r["Frame Type"] = safe_get(p, ["building", "construction", "frameType"])
        r["Basement Finished Percent"] = safe_get(p, ["building", "interior", "bsmtFinishedPercent"])
        r["Basement Size"] = safe_get(p, ["building", "interior", "bsmtSize"])
        r["Fireplace Count"] = safe_get(p, ["building", "interior", "fplcCount"])
        r["Fireplace Type"] = safe_get(p, ["building", "interior", "fplcType"])

        # --------------------------------------------------------------
        # PARKING & ROOMS
        # --------------------------------------------------------------
        r["Garage Type"] = safe_get(p, ["building", "parking", "garageType"])
        r["Parking Size"] = safe_get(p, ["building", "parking", "prkgSize"])
        r["Bedrooms"] = safe_get(p, ["building", "rooms", "beds"])
        r["Bathrooms Total"] = safe_get(p, ["building", "rooms", "bathsTotal"])
        r["Rooms Total"] = safe_get(p, ["building", "rooms", "roomsTotal"])

        # --------------------------------------------------------------
        # SIZE & SUMMARY
        # --------------------------------------------------------------
        r["Building Size"] = safe_get(p, ["building", "size", "bldgSize"])
        r["Living Size"] = safe_get(p, ["building", "size", "livingSize"])
        r["Gross Size"] = safe_get(p, ["building", "size", "grossSize"])
        r["Building Levels"] = safe_get(p, ["building", "summary", "levels"])
        r["Building View"] = safe_get(p, ["building", "summary", "view"])
        r["Building View Code"] = safe_get(p, ["building", "summary", "viewCode"])

        # --------------------------------------------------------------
        # LOT
        # --------------------------------------------------------------
        r["Lot Number"] = safe_get(p, ["lot", "lotNum"])
        r["Lot Size 1"] = safe_get(p, ["lot", "lotSize1"])
        r["Lot Size 2"] = safe_get(p, ["lot", "lotSize2"])
        r["Zoning Type"] = safe_get(p, ["lot", "zoningType"])

        # --------------------------------------------------------------
        # SALE
        # --------------------------------------------------------------
        r["Sale Amount"] = safe_get(p, ["sale", "saleAmountData", "saleAmt"])
        r["Sale Record Date"] = safe_get(p, ["sale", "saleAmountData", "saleRecDate"])
        r["Sale Document Number"] = safe_get(p, ["sale", "saleAmountData", "saleDocNum"])
        r["Sale Transaction Date"] = safe_get(p, ["sale", "saleTransDate"])
        r["Sale Transaction ID"] = safe_get(p, ["sale", "transactionIdent"])

        # --------------------------------------------------------------
        # SUMMARY
        # --------------------------------------------------------------
        r["Property Type"] = safe_get(p, ["summary", "propType"])
        r["Property Subtype"] = safe_get(p, ["summary", "propSubType"])
        r["Property Land Use"] = safe_get(p, ["summary", "propLandUse"])
        r["Year Built"] = safe_get(p, ["summary", "yearBuilt"])

        # --------------------------------------------------------------
        # LOCATION
        # --------------------------------------------------------------
        r["Latitude"] = safe_get(p, ["location", "latitude"])
        r["Longitude"] = safe_get(p, ["location", "longitude"])
        r["GeoID"] = safe_get(p, ["location", "geoid"])
        r["Geo Accuracy"] = safe_get(p, ["location", "accuracy"])

        # --------------------------------------------------------------
        # IDENTIFIER
        # --------------------------------------------------------------
        r["Identifier ID"] = safe_get(p, ["identifier", "Id"])
        r["APN"] = safe_get(p, ["identifier", "apn"])
        r["ATTOM ID"] = safe_get(p, ["identifier", "attomId"])
        r["FIPS Code"] = safe_get(p, ["identifier", "fips"])

        # --------------------------------------------------------------
        # UTILITIES
        # --------------------------------------------------------------
        r["Cooling Type"] = safe_get(p, ["utilities", "coolingType"])
        r["Heating Type"] = safe_get(p, ["utilities", "heatingType"])
        r["Energy Type"] = safe_get(p, ["utilities", "energyType"])
        r["Wall Type"] = safe_get(p, ["utilities", "wallType"])

        # --------------------------------------------------------------
        # VINTAGE
        # --------------------------------------------------------------
        r["Last Modified Date"] = safe_get(p, ["vintage", "lastModified"])
        r["Publication Date"] = safe_get(p, ["vintage", "pubDate"])

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
    return f"""
You are a verified property intelligence assistant.
Retrieve accurate factual data for: {address}

Section: {section_name}
Fields:
{field_defs}

ATTOM verified data (use to cross-check):
{attom_text}

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
# TAB 1 — GENERATE DATA
# --------------------------------------------------------------
with tab1:
    st.markdown("### 🧠 Generate Property Intelligence")
    property_address = st.text_input("🏡 Enter Full Property Address: ( Eg:2850 S Arlington Rd, Akron, OH 44312 )")

    if st.button("🚀 Generate Report", use_container_width=True):
        if not property_address.strip():
            st.warning("⚠️ Please enter an address.")
        else:
            placeholder = st.empty()
            with placeholder.container():
                st_lottie(LOTTIE_LOADING, height=220, key="loading")
                st.markdown("<h4 style='text-align:center;'>Analyzing property data with AI...</h4>", unsafe_allow_html=True)

            # hidden ATTOM + GPT fetching
            attom_props = fetch_attom_data(property_address)
            df_attom = flatten_attom_properties(attom_props) if attom_props else pd.DataFrame()
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

            placeholder.empty()
            st_lottie(LOTTIE_SUCCESS, height=200, key="success")
            st.success(f"✅ Report generated successfully for **{property_address}**")

            # Highlight NotFound values
            styled_df = df_final[["Field", "Value"]].style.applymap(lambda v: "color: red; font-weight:700;" if v == "NotFound" else "")
            st.dataframe(styled_df, use_container_width=True)

            # Excel download
            output = BytesIO()
            df_final.drop(columns=["Source"]).to_excel(output, index=False)
            st.download_button("⬇️ Download Report (Excel)", data=output.getvalue(),
                               file_name=f"ReValix_{property_address.replace(' ', '_')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --------------------------------------------------------------
# TAB 2 — HISTORY
# --------------------------------------------------------------
with tab2:
    st.markdown("### 📜 View Saved Reports")
    search_address = st.text_input("🏠 Search by Address ( Eg:2850 S Arlington Rd, Akron, OH 44312 ) ")
    if st.button("🔍 Retrieve Report", use_container_width=True):
        doc = collection.find_one({"address": search_address})
        if doc:
            df_past = pd.DataFrame(doc["records"])[["Field", "Value"]]
            st.success(f"✅ Showing saved report for {search_address}")
            st.dataframe(df_past, use_container_width=True)
        else:
            st.error("❌ No records found for this address.")

