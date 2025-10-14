# ==============================================================
#  🏙️ ReValix AI Property Intelligence
#  (Async Section Calls + Smart Retry + Animated UI)
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
# STREAMLIT CONFIG + CSS THEME
# --------------------------------------------------------------
st.set_page_config(page_title="ReValix AI Property Intelligence", layout="wide")

st.markdown("""
    <style>
    /* General Page Theme */
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
    /* Tabs */
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
    /* Loader */
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
    /* Title */
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
    /* DataFrame colors */
    .dataframe td {
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='revalix-header'>🏙️ ReValix AI Property Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='revalix-sub'>Property Insights with Real Data with AI </div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🧠 Generate Intelligence", "📜 View Historical Records"])

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
# SECTIONS
# --------------------------------------------------------------
def get_field_sections(df_fields):
    sections = {
        # ----------------------------------------------------------
        # 1️⃣ Identification & Basic Property Info
        # ----------------------------------------------------------
        "Identification": [
            "Property ID", "External Reference ID"
        ],
        
        "Basic Property Info" :  [ "Property Name",
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
# CORE FUNCTIONS
# --------------------------------------------------------------
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
You are a professional property data intelligence engine.
Fetch verified and factual information for this property: {address}

Section: {section_name}
Fields:
{field_defs}

Use these sources: any of the sources available on web using gpt which could provide better results 


{county_info}

Return ONLY:
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


