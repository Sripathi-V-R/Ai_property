# ==============================================================
# 🏙️ ReValix AI Property Intelligence - Full Workflow
# Author: Ai Master | Powered by GPT-5
# ==============================================================

import streamlit as st
import pandas as pd
import asyncio, aiohttp, os, re, requests
from io import BytesIO
from urllib.parse import quote_plus
from openai import OpenAI
from pymongo import MongoClient
from dotenv import load_dotenv
import requests
from streamlit_lottie import st_lottie

# --------------------------------------------------------------
# ENVIRONMENT & CLIENT SETUP
# --------------------------------------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ATTOM_API_KEY = os.getenv("ATTOM_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

client = OpenAI(api_key=OPENAI_API_KEY)
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["revalix_property_intelligence"]
collection = db["property_results"]

# --------------------------------------------------------------
# FIELD TEMPLATE
# --------------------------------------------------------------
def load_field_template():
    """Return field schema (Field + Description)."""

    data = [
        ("Property ID", "Unique identifier such as parcel number, APN, or internal ID. Alphanumeric."),
        ("External Reference ID", "External system ID from lender, bank, or registry. Alphanumeric."),
        ("Property Name", "Building, project, or complex name."),
        ("Property Type", "Primary property category. Example: Residential, Commercial, Industrial, Special Purpose."),
        ("Property Subtype", "Specific subtype. Example: Single Family Home, Office Building, Warehouse, Retail."),
        ("Ownership Type", "Legal tenure. Example: Freehold, Leasehold, Co-op, Perpetual Lease."),
        ("Occupancy Status", "Current usage. Example: Occupied, Vacant, Under Construction."),
        ("Registration Status", "Official registry condition. Example: Registered, Unregistered."),
        ("Registry Reference", "Official deed or registration reference number."),
        ("Building Code / Permit ID", "Municipal or permit identification number."),
        ("Geo ID", "Geographical identifier or census code."),
        ("Address Line 1", "Street number and name, apartment or unit if any."),
        ("Street Name", "Street name only."),
        ("City", "City or municipality name."),
        ("County", "County or parish name."),
        ("Township", "Township or local administrative division."),
        ("State", "Two-letter state or province code."),
        ("Postal Code", "Postal or ZIP code."),
        ("Latitude", "Latitude coordinate (decimal format)."),
        ("Longitude", "Longitude coordinate (decimal format)."),
        ("Facing Direction", "Orientation of property front. Example: North, South, East, West."),
        ("Neighborhood Type", "Land-use mix. Example: Residential, Commercial, Mixed-Use, Institutional."),
        ("Landmark", "Nearest major point of reference (school, road, mall)."),
        ("Connectivity Score", "Numeric accessibility or transport score."),
        ("Legal Description", "Formal land description (Lot & Block, Metes & Bounds, etc.)."),
        ("Census Tract", "Census or statistical area ID."),
        ("Market", "Market  name . Example: Akron, Austin."),
        ("Submarket", "Sub-region within market."),
        ("Submarket Cluster", "Functional cluster: Industrial, Retail, Residential."),
        ("CBSA", "Core-Based Statistical Area ID."),
        ("DMA", "Designated Market Area ID."),
        ("State Class Code", "Local classification code."),
        ("Neighborhood Code", "Local or assessor neighborhood code."),
        ("Neighborhood Name", "Common neighborhood name."),
        ("Map Facet", "Map feature or layer reference."),
        ("Key Map", "Map book or key map ID."),
        ("Tax District", "Tax jurisdiction or authority name."),
        ("Tax Code", "Local tax classification code refered by assessor."),
        ("Volume", "Building volume in cubic feet or meters."),
        ("Location Type", "Urban, Suburban, or Rural classification."),
        ("Land Area(Acre)", "Total site area in acres. Numeric only."),
        ("Plot No. / Survey No.", "Official plot or survey number available with the assessor."),
        ("Land Use Code", "Land use or zoning code assigned by authorities."),
        ("Land Market Value Per Square Foot", "Market land value per square foot in USD."),
        ("Plot Shape", "Shape type. Example: Rectangular, Irregular, Square."),
        ("Topography", "Terrain level. Example: level, sloped, hilly."),
        ("Grade", "Relative elevation to street level. Example: Above, At, Below."),
        ("Soil Type", "Dominant soil type. Example: Clay, Sandy, Loamy."),
        ("Dimensions", "Frontage and depth (in feet/meters)."),
        ("Ground Coverage", "Percentage of land area covered by building."),
        ("Easements/Right of Way", "Access rights if applicable."),
        ("Encroachments", "Encroachment presence or details."),
        ("Land Use Compliance / Zoning", "Local zoning or compliance status."),
        ("FSI / FAR Allowed", "Permitted floor space index or ratio."),
        ("Flood Zone", "FEMA flood classification. Example: AE, X, V."),
        ("Flood Map Number", "Flood map panel number."),
        ("Flood Map Date", "Flood map effective date (YYYY-MM-DD)."),
        ("Flood Plain Area", "Floodplain type. Example: 100-year, 500-year, Floodway."),
        ("Flood Risk Area", "Flood risk category. Example: Low, Moderate, High."),
        ("Site Improvements", "On-site enhancements such as paving or landscaping."),
        ("Off-Site Improvements", "Nearby infrastructure like curbs, lights, sidewalks."),
        ("Immediate access to Highways/Freeways", "Yes/No; if Yes, specify route names."),
        ("Lot Position", "Corner or Non-Corner position."),
        ("Site Utility", "Overall site usability. Example: Good, Average, Poor."),
        ("Frontage Rating", "Frontage quality: Good, Average, Poor."),
        ("Access Rating", "Access quality: Good, Average, Poor."),
        ("Visibility Rating", "Visibility rating: Good, Average, Poor."),
        ("Location Rating", "Location rating: Good, Average, Poor."),
        ("Building Name", "Name of the building or tower."),
        ("Year of Construction", "Construction completion year (YYYY)."),
        ("Building Style code", "Code for architectural or construction style."),
        ("Building Design", "Design style name. Example: Colonial, Modern."),
        ("Age of Building", "Building age in years."),
        ("Stories", "Total number of above-ground floors."),
        ("Buildings", "Number of buildings in property."),
        ("Exterior", "Exterior material. Example: Brick, Concrete, Metal."),
        ("Structural System", "Primary structure type. Example: Steel, RC, Timber."),
        ("No. of Floors", "Number of floors in structure."),
        ("Lift Count", "Number of elevators."),
        ("Fire Safety Systems", "Presence of sprinklers, alarms, extinguishers, etc."),
        ("Security Systems", "Presence of CCTV, guards, access control."),
        ("Building Code", "Assessor or municipal classification code."),
        ("Building Condition", "Overall condition. Example: Excellent, Good, Fair, Poor."),
        ("GBA", "Gross Building Area in square feet (total built-up space). Numeric only."),
        ("NRA", "Net Rentable Area in square feet (leaseable space). Numeric only."),
        ("Year of Renovation", "Last renovation or major upgrade year (YYYY)."),
        ("Useful Life", "Expected total useful life of the structure in years."),
        ("Effective Age", "Functional or physical age of building in years."),
        ("Remaining Economic Life", "Estimated years of use remaining."),
        ("Building Class", "Quality classification. Example: A, B, C, D."),
        ("Foundation", "Type of foundation: Slab, Piling, Concrete, Crawl Space."),
        ("Total Rooms", "Total count of rooms in entire property."),
        ("Total Bedroom", "Total number of bedrooms."),
        ("Total Bath", "Total number of bathrooms."),
        ("Interior Flooring", "Floor finish. Example: Tile, Vinyl, Wood, Carpet."),
        ("Ceiling", "Ceiling material/type. Example: Drywall, Exposed, Suspended."),
        ("Ceiling Height", "Floor-to-ceiling height in feet or meters."),
        ("Interior Finish %", "Percentage of finished interior area."),
        ("Dock Doors", "Type or count of dock doors. Example: Roll-Up, Leveler."),
        ("Roofing", "Roof type and material. Example: Shingle, Metal, Concrete."),
        ("Heating", "Heating system type. Example: Central, Forced Air, Heat Pump."),
        ("Cooling", "Cooling system type. Example: Central, Split, Window."),
        ("Other Improvements/Extra Features", "Other physical improvements like patios, sheds, or decks."),
        ("Occupied By", "Owner or Tenant. Indicate who occupies the property."),
        ("Number of Tenants", "Count of distinct tenants or occupants."),
        ("Lease Structure", "Lease type. Example: Gross, Net, Modified Gross, Percentage, Full Service."),
        ("Occupancy at the time of sale", "Percent of occupied area at time of sale. Numeric."),
        ("Exempt %", "Portion of property exempt from tax. Percentage."),
        ("Prorated Bldg %", "Percentage of total value assigned to building."),
        ("Parking Ratio", "Parking spaces per 1,000 sqft or per unit."),
        ("Parking Spaces", "Total number of parking spaces."),
        ("Assessment Information", "Assessed values for land, building, and total with assessment year."),
        ("Unit No. / Unit Name", "Specific unit, flat, or suite identifier."),
        ("Floor No.", "Floor level number within the building."),
        ("Unit Type", "Usage type of unit. Example: Office, Retail, 2BR Apartment."),
        ("Use Type", "Usage classification. Example: Residential, Commercial, Mixed-Use."),
        ("Carpet Area", "Usable floor area inside walls in sqft."),
        ("Built-up Area", "Built-up area including walls and balconies."),
        ("Super Built-up Area", "Built-up area plus proportionate share of common spaces."),
        ("No. of Rooms", "Number of rooms in the individual unit."),
        ("Bedrooms", "Number of bedrooms in the unit."),
        ("Bathrooms", "Number of bathrooms in the unit."),
        ("Ceiling Height (Unit)", "Ceiling height specific to this unit (feet/meters)."),
        ("Furniture", "Furnishing status: Furnished, Semi-Furnished, Unfurnished."),
        ("Unit Condition", "Condition of unit: Finished, Shell, Under Construction."),
        ("Balcony / Terrace", "Presence and size of balcony or terrace."),
        ("Occupied Exempt Units", "Percentage of occupied units that are tax-exempt."),
        ("Occupied Rent-Regulated Units", "Percentage of occupied units with rent regulation."),
        ("Vacant Units", "Percentage of vacant units."),
        ("Lease Status", "Status of lease: Active, Expired, Terminated."),
        ("Tenant Name (or ID)", "Tenant full name or tenant ID."),
        ("Lease Start Date", "Start date of lease (YYYY-MM-DD)."),
        ("Lease End Date", "Lease expiry date (YYYY-MM-DD)."),
        ("Lease Term", "Duration of lease in months or years."),
        ("Renewal Options", "Whether renewal options exist and their terms."),
        ("Special Clauses", "Special clauses like early termination or exclusivity."),
        ("Appliances Included", "List of appliances included in lease or sale."),
        ("HVAC Type", "Heating, ventilation, and cooling configuration."),
        ("Parking Assigned", "Number of parking spots assigned to the unit."),
        ("Storage Unit Assigned", "Whether a storage space is assigned. Yes/No and size if available."),
        ("Internet/Cable Ready", "Availability of internet/cable. Yes/No."),
        ("ADA Accessibility", "Compliance with accessibility standards. Yes/No."),
        ("Photos / Floor Plans", "Links, filenames, or references to photos/floor plans."),
        ("Owner Name(s)", "Registered owner or entity name(s)."),
        ("Title Status", "Title clarity. Example: Clear, Disputed, Encumbered."),
        ("Registration No.", "Official registration or deed number."),
        ("Registration Date", "Date of registration (YYYY-MM-DD)."),
        ("Registrar Office", "Location or jurisdiction of registrar."),
        ("Encumbrance Certificate", "Certificate or reference number for encumbrance check."),
        ("Mortgages / Liens", "Mortgage or lien information including lender, amount, and date."),
        ("Occupancy Certificate", "Certificate number and issue date."),
        ("Fire NOC", "Fire department clearance number and issue date."),
        ("Compliance to Local By-laws", "Whether property complies with local rules. Yes/No."),
        ("Grantor", "Seller who sold the property to the current owner or buyer."),
        ("Grantee", "Buyer or transferee name."),
        ("Condition of Sale", "Nature of sale. Example: Arm’s Length, Foreclosure, Distressed, Investments, Family Transfer."),
        ("Rights Transferred", "Legal rights transferred. Example: Fee Simple, Leasehold, Easement, Covenant, leased Fee."),
        ("Qualified", "Whether verified and qualified. Example: Qualified, Pending."),
        ("Type of Deed / Instrument", "Type of conveyance deed. Example: Warranty, Quitclaim."),
        ("Covenants / Warranties", "Type of covenants or warranties in deed."),
        ("Recording Information", "Book, page, and stamp details of recording."),
        ("Miscellaneous Clauses", "Any additional clauses like restrictions or easements."),
        ("Purchase Price / Sale Price", "Sale or purchase price with currency (numeric)."),
        ("Purchase Date / Sale Date", "Transaction date (YYYY-MM-DD)."),
        ("Current Market Value", "Estimated market value in USD or local currency."),
        ("Current Appraised Value", "Value as per latest professional appraisal."),
        ("Current Land Value", "Land portion of current appraised value."),
        ("Current Improvements Value", "Improvement or building portion of current value."),
        ("Appraised Value History", "Appraisal values for last three years."),
        ("Listing Price", "Quoted listing or asking price."),
        ("No. of days on market", "Days the property has been listed for sale."),
        ("Assessed Value", "Official tax-assessed value for the property."),
        ("Land Assessed Value", "Tax-assessed land value portion."),
        ("Improvements Assessed Value", "Tax-assessed improvements value portion."),
        ("Assessed Value History", "Historical assessed values for past three years."),
        ("Guideline / Circle Rate", "Government benchmark or minimum valuation rate."),
        ("Current Rent / Lease Rate", "Actual rent rate per month or per sqft."),
        ("Market Rent", "Factual market rent available on the sources."),
        ("Lease Duration", "Length of lease in months or years."),
        ("Security Deposit Held", "Amount of security deposit held by landlord."),
        ("CAM Charges (Commercial)", "Common area maintenance charges if applicable."),
        ("Property Tax", "Annual property tax amount in USD or local currency."),
        ("Utilities Included", "Utilities covered in rent. Example: Water, Electricity, Gas, Internet."),
        ("Subsidies / Vouchers", "Any government or rent subsidy applied. Yes/No and type."),
        ("Vacancy rate (Property)", "Percent of property currently vacant. Numeric with % sign."),
        ("Tenant Incentives / TI Allowance", "Tenant improvement allowance or incentives offered."),
        ("Leasing Commission", "Commission paid to leasing agent or broker."),
        ("Reimbursements", "Amounts reimbursed by tenants for expenses."),
        ("CapEx", "Capital expenditures made on property in currency."),
        ("Cap Rate", "Capitalization rate as percentage refered in various sources."),
        ("Discount rate", "Discount rate used for valuation calculations in % found in various sources."),
        ("Mortgage Loan", "Total mortgage or loan amount in currency."),
        ("Loan Date", "Date when loan originated (YYYY-MM-DD)."),
        ("Originator", "Name of lender, bank, or financial institution."),
        ("Mortgage Rate", "Interest rate percentage for the loan found in various sources."),
        ("Rate Type", "Interest type. Example: Fixed, Variable, Adjustable found in various sources."),
        ("Loan Term", "Duration of loan in months or years found in various sources."),
        ("Monthly Mortgage Payment", "Monthly payment amount due in currency found in various sources."),
        ("Debt Service", "Total annual debt service in currency found in various sources."),
        ("Debt Service Coverage Ratio (DSCR)", "Net operating income divided by debt service. Numeric ratio found in various sources."),
        ("Equity Rate", "Return on equity rate in % found in various sources."),
        ("Current Tax Year", "Assessment or tax year (YYYY) give the current year data."),
        ("Gross Tax", "Total annual gross tax amount. get latest data."),
        ("Special Assessments", "Special district or improvement assessment charges get latest data."),
        ("Other Deductions", "Any deductions applied to property tax."),
        ("Net Tax", "Net payable tax after deductions get latest data."),
        ("Full Rate", "Mill or property tax rate applied on gross amount."),
        ("Effective Rate", "Mill or tax rate applied on net assessed value."),
        ("Tax History", "Annual property tax payments over last 3 years and get latest data."),
        ("Power Backup", "Availability of backup power. Example: Generator, Solar, UPS."),
        ("Water Supply", "Water source type. Example: Municipal, Borewell, Both."),
        ("Sewage System", "Waste disposal system. Example: Municipal, Septic, On-site Treatment."),
        ("Security", "Security features. Example: CCTV, Gated, Guarded."),
        ("Internet Connectivity", "Connection type. Example: Fiber, DSL, Satellite."),
        ("Common Areas", "Shared spaces like lobby, lounge, or terrace."),
        ("Recreational Amenities", "Amenities such as gym, pool, clubhouse."),
        ("Green Area", "Percent of plot with green or landscaped area."),
        ("Parking", "Parking type. Example: Open, Covered, Multi-level."),
        ("Lighting", "Lighting provisions. Example: Street, Common Area, Smart Lighting."),
        ("Market Segment", "Price or quality segment. Example: Luxury, Mid, Affordable."),
        ("Price Trend (12m)", "12-month appreciation or depreciation rate %."),
        ("Supply-Demand Index", "Local supply-demand ratio or index value."),
        ("Sales Trend", "Change in sales over 6m or 12m period. Percent."),
        ("Sales to Asking Price Differential", "Difference between sale and asking price in %."),
        ("For Sale Trend", "Change in active listings over 6m/12m period."),
        ("Transaction Type", "Type of transaction. Example: Individual, Portfolio, Entity Sale."),
        ("Comparable Properties", "Nearby comparable property IDs or addresses."),
        ("Avg. Comparable Price", "Average comparable price per sqft."),
        ("Price Deviation", "Difference from comparable average price in %."),
        ("Rent Trend", "Change in rental rates over 6m or 12m period."),
        ("Direct & Sublet Rent Trend", "Variation between direct and sublet rents over time."),
        ("Vacancy Rate (Market)", "Market-wide vacancy percentage."),
        ("24 Months Lease Renewal Rate", "Percentage of leases renewed in last 24 months."),
        ("RBA", "Rentable Building Area (total). Numeric in sqft."),
        ("Availability Rate", "Percentage of leasable space available."),
        ("Net Absorption SF", "Net occupied area change during period in sqft."),
        ("Months on Market (Market)", "Average listing duration in months."),
        ("Months to Lease (Market)", "Average time to lease space in months."),
        ("Months Vacant (Market)", "Average vacancy duration in months."),
        ("Probability of Leasing", "Likelihood of leasing within a given time frame (in months)."),
        ("Deliveries SF", "Square footage of newly delivered buildings."),
        ("Demolitions SF", "Square footage of demolished space."),
        ("Under Construction SF", "Square footage under active construction."),
        ("Under Construction Rate", "Percentage of inventory under construction."),
        ("Preleased Rate", "Percentage of under-construction space pre-leased."),
        ("Start Date (Project)", "Project construction start date (YYYY-MM-DD)."),
        ("Complete Date (Project)", "Project completion date (YYYY-MM-DD)."),
        ("Developer/Owner", "Name of developer or current owner entity."),
        ("Sales Volume", "Total area sold or transaction volume in sqft."),
        ("Market Sale Price per SF", "Average market sale price per square foot."),
        ("Market Asking Rent per SF", "Average asking rent per square foot."),
        ("Market Cap Rate", "Market capitalization rate percentage."),
        ("Market Employment by Industry", "Breakdown of employment by major industry sectors."),
        ("Unemployment Rate (Market)", "Current unemployment rate in %."),
        ("Net Employment Change", "Employment gain or loss (numeric)."),
        ("Predicted Value Range", "AI-predicted minimum and maximum property value range."),
        ("AI Condition Score", "AI-generated property condition score (0–100)."),
        ("Asset Value by Owner Type", "Distribution of asset ownership by owner type in %."),
        ("Sales by Buyer Type", "Share of sales by buyer type in %."),
        ("Sales by Seller Type", "Share of sales by seller type in %."),
        ("Marketing and Exposure Time", "Average months property remains listed or marketed."),
        ("Traffic Count", "Average daily vehicle traffic near property."),
        ("Population in 1, 3 & 5 miles", "Population counts within 1, 3, and 5-mile radii."),
        ("Population Growth", "Population growth rate %."),
        ("Population", "Total population current level and change rates."),
        ("Households", "Total number of households and change trends."),
        ("Average Household Size", "Average household members count."),
        ("Total Housing Units", "Number of total housing units."),
        ("Owner Occupied Housing Units", "Count or % of owner-occupied housing."),
        ("Renter Occupied Housing Units", "Count or % of renter-occupied housing."),
        ("Vacant Housing Units", "Count or % of vacant housing units."),
        ("Labor Force", "Total working population size."),
        ("Unemployment", "Unemployment rate %."),
        ("Median Household Income", "Median household income in USD."),
        ("Per Capita Income", "Per capita income in USD."),
        ("Median Home Price", "Median home sale price in USD."),
        ("Latest Population 25+ by Educational Attainment", "Distribution of adult education levels."),
        ("AI Condition Index", "AI-computed index of property condition (0–100)."),
        ("Structural Integrity Score", "AI-generated score for structural soundness (0–100)."),
        ("Market Confidence Index", "AI or ML-based market stability score (0–100)."),
        ("Price Prediction (Now)", "AI-predicted current market value in USD."),
        ("Price Prediction (12M Ahead)", "AI-predicted value 12 months ahead in USD."),
        ("Market Liquidity Score", "AI-based time-to-sell estimate score (0–100)."),
        ("Risk Classification", "Risk level. Example: Low, Moderate, High."),
        ("Anomaly Detection", "Flag for data inconsistency. Example: Yes/No."),
        ("Automated Summary", "AI-generated narrative summary of property attributes.")
    ]

    return pd.DataFrame(data, columns=["Field", "Description"])

# --------------------------------------------------------------
# STEP 1: ADDRESS NORMALIZATION USING GPT
# --------------------------------------------------------------
def normalize_address_with_gpt(raw_address):
    prompt = f"""
Normalize this address into standard US postal format:
Return strictly 2 lines:
<address1>
<city, state ZIP>

Input: "{raw_address}"
"""
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    lines = resp.choices[0].message.content.strip().split("\n")
    return ", ".join(lines).strip()

# --------------------------------------------------------------
# STEP 2: ATTOM FETCH
# --------------------------------------------------------------
def fetch_attom_data(address):
    try:
        parts = address.split(",")
        address1, address2 = parts[0].strip(), ",".join(parts[1:]).strip()
        url = f"https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/basicprofile?address1={quote_plus(address1)}&address2={quote_plus(address2)}"
        res = requests.get(url, headers={"apikey": ATTOM_API_KEY, "accept": "application/json"}, timeout=30)
        res.raise_for_status()
        return res.json().get("property", [])
    except Exception as e:
        print("ATTOM Error:", e)
        return []

# --------------------------------------------------------------
# STEP 3: FLATTEN ATTOM DATA
# --------------------------------------------------------------
def safe_get(d, keys):
    for k in keys:
        if isinstance(d, dict) and k in d:
            d = d[k]
        else:
            return None
    return d

def flatten_attom(p_list):
    rows = []
    for p in p_list:
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
        r["Legal Description"] = safe_get(p, ["summary", "legal1"])

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
# STEP 4: MAPPING
# --------------------------------------------------------------
def map_attom_to_fields(df_attom):
    mapping = {
    # --------------------------------------------------------------
    # IDENTIFIERS
    # --------------------------------------------------------------
    "Property ID": "APN",
    "FIPS Code": "FIPS Code",
    "Identifier ID": "Identifier ID",

    # --------------------------------------------------------------
    # ADDRESS
    # --------------------------------------------------------------
    "Country": "Address Country",
    "State": "Address State",
    "Address Line 1": "Address Line 1",
    "Address Line 2": "Address Line 2",
    "City": "Address City",
    "Postal Code": "Postal Code 1",
    "Secondary Postal Code": "Postal Code 2",
    "Address Match Code": "Address Match Code",
    "Full Address": "Address OneLine",
    "Legal Description": "Legal Description",

    # --------------------------------------------------------------
    # AREA
    # --------------------------------------------------------------
    "Census Block Group": "Census Block Group",
    "Census Tract": "Census Tract Ident",
    "County Subdivision": "Country Sec Subd",
    "Subdivision Name": "Subdivision Name",
    "Subdivision Tract Number": "Subdivision Tract Num",

    # --------------------------------------------------------------
    # ASSESSMENT
    # --------------------------------------------------------------
    "Current Appraised Value": "Appraised Value",
    "Improvements Assessed Value": "Assessed Improvement Value",
    "Land Assessed Value": "Assessed Land Value",
    "Assessed Value": "Assessed Total Value",
    "Improvement Percent": "Improvement Percent",
    "Current Improvements Value": "Market Improvement Value",
    "Current Land Value": "Market Land Value",
    "Current Market Value": "Market Total Value",
    "Delinquent Year": "Delinquent Year",

    # --------------------------------------------------------------
    # MORTGAGE
    # --------------------------------------------------------------
    "First Mortgage Amount": "First Mortgage Amount",
    "First Mortgage Lender First Name": "First Mortgage Lender First Name",
    "First Mortgage Lender Last Name": "First Mortgage Lender Last Name",
    "First Mortgage Document Number": "First Mortgage Document Number",
    "Second Mortgage Amount": "Second Mortgage Amount",
    "Second Mortgage Lender First Name": "Second Mortgage Lender First Name",
    "Second Mortgage Lender Last Name": "Second Mortgage Lender Last Name",
    "Second Mortgage Document Number": "Second Mortgage Document Number",

    # --------------------------------------------------------------
    # OWNER
    # --------------------------------------------------------------
    "Absentee Owner Status": "Absentee Owner Status",
    "Corporate Owner Indicator": "Corporate Owner Indicator",
    "Mailing Address": "Mailing Address OneLine",
    "Owner 1 Name": "Owner 1 Name",
    "Owner 2 Name": "Owner 2 Name",
    "Owner 3 Name": "Owner 3 Name",
    "Owner 4 Name": "Owner 4 Name",

    # --------------------------------------------------------------
    # TAX
    # --------------------------------------------------------------
    "Property Tax": "Tax Amount",
    "Current Tax Year": "Tax Year",
    "Tax Exemption": "Tax Exemption",
    "Homeowner Exemption": "Homeowner Exemption",
    "Veteran Exemption": "Veteran Exemption",

    # --------------------------------------------------------------
    # BUILDING (CONSTRUCTION & INTERIOR)
    # --------------------------------------------------------------
    "Building Condition": "Building Condition",
    "Construction Type": "Construction Type",
    "Foundation": "Foundation Type",
    "Structural System": "Frame Type",
    "Basement Finished Percent": "Basement Finished Percent",
    "Basement Size": "Basement Size",
    "Fireplace Count": "Fireplace Count",
    "Fireplace Type": "Fireplace Type",

    # --------------------------------------------------------------
    # PARKING & ROOMS
    # --------------------------------------------------------------
    "Garage Type": "Garage Type",
    "Parking Size": "Parking Size",
    "Total Bedroom": "Bedrooms",
    "Total Bath": "Bathrooms Total",
    "Total Rooms": "Rooms Total",

    # --------------------------------------------------------------
    # SIZE & SUMMARY
    # --------------------------------------------------------------
    "Building Area": "Building Size",
    "GBA": "Gross Size",
    "RBA": "Building Size",
    "NRA": "Living Size",
    "Building Levels": "Building Levels",
    "Building View": "Building View",
    "Building View Code": "Building View Code",
    "Stories": "Building Levels",

    # --------------------------------------------------------------
    # LOT
    # --------------------------------------------------------------
    "Lot Number": "Lot Number",
    "Land Area(Acre)": "Lot Size 1",
    "Lot Size (Alt)": "Lot Size 2",
    "Land Use Compliance / Zoning": "Zoning Type",

    # --------------------------------------------------------------
    # SALE
    # --------------------------------------------------------------
    "Purchase Price / Sale Price": "Sale Amount",
    "Purchase Date / Sale Date": "Sale Record Date",
    "Sale Document Number": "Sale Document Number",
    "Sale Transaction Date": "Sale Transaction Date",
    "Sale Transaction ID": "Sale Transaction ID",

    # --------------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------------
    "Property Type": "Property Subtype",
    "Property Subtype": "Property Type",
    "Property Land Use": "Property Land Use",
    "Year Built": "Year Built",

    # --------------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------------
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    "Geo ID": "GeoID",
    "Geo Accuracy": "Geo Accuracy",

    # --------------------------------------------------------------
    # UTILITIES
    # --------------------------------------------------------------
    "Cooling": "Cooling Type",
    "Heating": "Heating Type",
    "Energy Type": "Energy Type",
    "Wall Type": "Wall Type",

    # --------------------------------------------------------------
    # VINTAGE
    # --------------------------------------------------------------
    "Last Modified Date": "Last Modified Date",
    "Publication Date": "Publication Date",
}
    mapped = []
    for field, attom_field in mapping.items():
        if attom_field in df_attom.columns:
            val = df_attom.iloc[0][attom_field]
            if pd.notna(val):
                mapped.append({"Field": field, "Value": val, "Source": "ATTOM"})
    return pd.DataFrame(mapped)

# --------------------------------------------------------------
# STEP 5: COUNTY DISCOVERY USING GPT
# --------------------------------------------------------------
def get_county_site(address):
    prompt = f"""
Find the official county government website for this address:
Address: {address}
Return only the full URL (like https://www.kingcountywa.gov)
"""
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return resp.choices[0].message.content.strip()

# --------------------------------------------------------------
# STEP 6–8: ASYNC GPT FETCH FOR REMAINING FIELDS
# --------------------------------------------------------------
async def fetch_section(session, address, section_fields, county_site, df_attom):
    field_defs = "\n".join([f"{f}: {d}" for f, d in section_fields])
    attom_summary = df_attom.to_dict(orient="records")[0] if not df_attom.empty else {}
    prompt = f"""
You are an expert property intelligence assistant.
Retrieve factual data for:
{address}

Use verified real estate and government sources.
County site: {county_site}

The following fields are needed:
{field_defs}

ATTOM verified info (for context): {attom_summary}

Return only this format:
| Field | Value | Source |
"""
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {"model": "gpt-4.1-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
    try:
        async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=120) as r:
            data = await r.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        print("Section Error:", e)
        return ""

def parse_output(txt):
    rows = []
    for line in txt.split("\n"):
        if "|" in line and not line.lower().startswith("| field"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) == 3:
                rows.append({"Field": parts[0], "Value": parts[1], "Source": parts[2]})
    return rows

# --------------------------------------------------------------
# FINAL MERGE + SAVE
# --------------------------------------------------------------
def merge_all(df_attom_map, df_gpt, fields_df, address):
    df_all = pd.concat([df_attom_map, df_gpt], ignore_index=True)
    merged = (
        df_all.groupby("Field", as_index=False)
        .agg({
            "Value": lambda v: next((x for x in v if pd.notna(x) and x not in ["", "NotFound"]), "NotFound"),
            "Source": lambda s: next((x for x in s if pd.notna(x) and x.strip() != ""), "Verified Data"),
        })
    )

    df_final = pd.merge(fields_df, merged, on="Field", how="left")
    df_final["Value"].fillna("NotFound", inplace=True)
    df_final["Source"].fillna("Verified Data", inplace=True)

    # Save to MongoDB
    collection.replace_one(
        {"address": address},
        {"address": address, "records": df_final.to_dict("records")},
        upsert=True
    )
    return df_final

# --------------------------------------------------------------
# MAIN EXECUTION (Streamlit with Enhanced UI)
# -----------------------------------------------------------

# --- PAGE CONFIG & STYLING ---
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
.revalix-header { font-size: 2.4rem; text-align: center; color: #0ea5e9; font-weight: 800; margin-bottom: 0.2rem; }
.revalix-sub { text-align: center; font-size: 1.1rem; color: #334155; margin-bottom: 35px; }
.dataframe td { font-weight: 500; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='revalix-header'>🏙️ ReValix AI Property Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='revalix-sub'>AI-Powered Property Data Enrichment</div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🧠 Generate Intelligence", "📜 View Past Reports"])

# --------------------------------------------------------------
# LOTTIE ANIMATION HELPERS
# --------------------------------------------------------------
def load_lottie_url(url: str):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None

LOTTIE_LOADING = load_lottie_url("https://assets10.lottiefiles.com/packages/lf20_j1adxtyb.json")
LOTTIE_SUCCESS = load_lottie_url("https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json")

# --------------------------------------------------------------
# TAB 1: MAIN WORKFLOW
# --------------------------------------------------------------
with tab1:
    st.markdown("### 🧠 Generate Property Intelligence")
    raw_addr = st.text_input("🏡 Enter Full Property Address:")

    if st.button("🚀 Generate Report", use_container_width=True):
        if not raw_addr.strip():
            st.warning("Please enter a valid property address.")
        else:
            # Show loading animation while running workflow
            loading_placeholder = st.empty()
            with loading_placeholder:
                st_lottie(LOTTIE_LOADING, height=200, key="loading")

            with st.spinner("Normalizing address..."):
                normalized = normalize_address_with_gpt(raw_addr)
            st.success(f"Normalized Address: {normalized}")

            with st.spinner("Fetching ATTOM data..."):
                attom_data = fetch_attom_data(normalized)
                df_attom = flatten_attom(attom_data)
            # ⛔ Removed st.write(df_attom) display

            df_fields = load_field_template()
            df_attom_map = map_attom_to_fields(df_attom)

            with st.spinner("Locating county website..."):
                county_site = get_county_site(normalized)
            st.info(f"Official County Site: {county_site}")

            # Remaining fields for GPT
            attom_fields = df_attom_map["Field"].tolist()
            remaining = df_fields[~df_fields["Field"].isin(attom_fields)]
            chunks = [remaining.iloc[i:i+10] for i in range(0, len(remaining), 10)]

            async def run_all_sections():
                async with aiohttp.ClientSession() as s:
                    tasks = [fetch_section(s, normalized, c.values.tolist(), county_site, df_attom) for c in chunks]
                    out = await asyncio.gather(*tasks)
                    return out

            with st.spinner("Fetching remaining fields via GPT..."):
                results = asyncio.run(run_all_sections())

            all_recs = []
            for res in results:
                all_recs.extend(parse_output(res))
            df_gpt = pd.DataFrame(all_recs)

            df_final = merge_all(df_attom_map, df_gpt, df_fields, normalized)

            # ✅ Stop loading animation
            loading_placeholder.empty()
            st_lottie(LOTTIE_SUCCESS, height=180, key="success")

            st.success("✅ All data merged successfully")

            # ✅ Show only Fields & Values
            st.dataframe(df_final[["Field", "Value"]], use_container_width=True)

            # ✅ Download only Field + Value, file name = property address
            out = BytesIO()
            df_final[["Field", "Value"]].to_excel(out, index=False)
            clean_filename = re.sub(r'[^A-Za-z0-9_]+', '_', normalized)
            file_name = f"{clean_filename}.xlsx"
            st.download_button(
                "⬇️ Download Full Report",
                data=out.getvalue(),
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# --------------------------------------------------------------
# TAB 2: VIEW PAST REPORTS
# --------------------------------------------------------------
with tab2:
    st.markdown("### 📜 View Past Reports")
    search_address = st.text_input("🔍 Search Property Address:")

    if st.button("Retrieve Report", use_container_width=True):
        if not search_address.strip():
            st.warning("Please enter a valid address to search.")
        else:
            doc = collection.find_one({"address": search_address})
            if doc:
                df_past = pd.DataFrame(doc["records"])[["Field", "Value"]]
                st.success(f"✅ Showing saved report for {search_address}")
                st.dataframe(df_past, use_container_width=True)
            else:
                st.error("❌ No records found for this address.")
