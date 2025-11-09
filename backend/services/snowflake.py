import json
import sseclient

def parse_cortex_sse(resp):
    """
    Parse a Cortex SSE streaming response and return the full text.
    """
    full_text = ""

    if resp.status_code < 400:
        client = sseclient.SSEClient(resp)

        for event in client.events():
            if not event.data or event.data.strip() in ["[DONE]", ""]:
                continue

            try:
                parsed = json.loads(event.data)
                delta = parsed.get("choices", [{}])[0].get("delta", {})

                # grab either 'text' or 'content' depending on which is present
                chunk_text = delta.get("text") or delta.get("content")
                if chunk_text:
                    full_text += chunk_text

            except json.JSONDecodeError:
                # skip non-JSON lines
                continue
            except (IndexError, KeyError):
                continue

    return full_text


def format_prompt(user_query: str):
    """
    Prompt for Snowflake Cortex GenAI, formatted with the necessary context & user query
    """
#     nlq_prompt = f"""# Snowflake Cortex AI SQL Generator Prompt

# You are an AI that converts **natural language requests into SQL queries** for Snowflake.  
# Generate **syntactically correct SQL** that will run in Snowflake without errors. Be **precise, efficient, and only include the columns needed**. Use JOINs when necessary, and apply filters or aggregation if implied by the user's request.

# ---

# ## 1. Database Metadata

# ### Tables and Columns
# - Database name is PLOTHOLES. Schema name is NYC_STREET_DATA. Table name is STREET_DATA. Snowflake uses the hierarhical naming convention: DATABASE_NAME.SCHEMA_NAME.TABLE_NAME
# - STREET_DATA is the ONLY table in the database.
# #### PLOTHOLES.NYC_STREET_DATA.STREET_DATA Column Name & Description:
# - UNIQUE_KEY: Unique identifier of a Service Request (SR) in the open data set
# - CREATED_DATE: Date SR was created
# - CLOSED_DATE: Date SR was closed by responding agency
# - AGENCY: Acronym of responding City Government Agency
# - AGENCY_NAME: Full Agency name of responding City Government Agency
# - COMPLAINT_TYPE: This is the first level of a hierarchy identifying the topic of the incident or condition. Complaint Type may have a corresponding Descriptor (below) or may stand alone.
# - DESCRIPTOR: This is associated to the Complaint Type, and provides further detail on the incident or condition. Descriptor values are dependent on the Complaint Type, and are not always required in SR.
# - LOCATION_TYPE: Describes the type of location used in the address information
# - INCIDENT_ZIP: Incident location zip code, provided by geo validation.
# - INCIDENT_ADDRESS: House number of incident address provided by submitter.
# - STREET_NAME: Street name of incident address provided by the submitter
# - CROSS_STREET_1: First Cross street based on the geo validated incident location
# - CROSS_STREET_2: Second Cross Street based on the geo validated incident location
# - INTERSECTION_STREET_1: First intersecting street based on geo validated incident location
# - INTERSECTION_STREET_2: Second intersecting street based on geo validated incident location
# - ADDRESS_TYPE: Type of incident location information available.
# - CITY: City of the incident location provided by geovalidation.
# - LANDMARK: If the incident location is identified as a Landmark the name of the landmark will display here
# - FACILITY_TYPE: If available, this field describes the type of city facility associated to the SR
# - STATUS: Status of SR submitted
# - DUE_DATE: Date when responding agency is expected to update the SR. This is based on the Complaint Type and internal Service Level Agreements (SLAs).
# - RESOLUTION_DESCRIPTION: Describes the last action taken on the SR by the responding agency. May describe next or future steps.
# - RESOLUTION_ACTION_UPDATED_DATE: Date when responding agency last updated the SR.
# - COMMUNITY_BOARD: Provided by geovalidation.
# - BBL: Borough Block and Lot, provided by geovalidation. Parcel number to identify the location of location of buildings and properties in NYC.
# - BOROUGH: Provided by the submitter and confirmed by geovalidation.
# - "X Coordinate (State Plane)": Geo validated, X coordinate of the incident location.
# - "Y Coordinate (State Plane)": Geo validated, Y coordinate of the incident location.
# - OPEN_DATA_CHANNEL_TYPE: Indicates how the SR was submitted to 311. i.e. By Phone, Online, Mobile, Other or Unknown.
# - PARK_FACILITY_NAME: If the incident location is a Parks Dept facility, the Name of the facility will appear here
# - PARK_BOROUGH: The borough of incident if it is a Parks Dept facility
# - VEHICLE_TYPE: If the incident is a taxi, this field describes the type of TLC vehicle.
# - TAXI_COMPANY_BOROUGH: If the incident is identified as a taxi, this field will display the borough of the taxi company.
# - TAXI_PICK_UP_LOCATION: If the incident is identified as a taxi, this field displays the taxi pick up location
# - BRIDGE_HIGHWAY_NAME: If the incident is identified as a Bridge/Highway, the name will be displayed here.
# - BRIDGE_HIGHWAY_DIRECTION: If the incident is identified as a Bridge/Highway, the direction where the issue took place would be displayed here.
# - ROAD_RAMP: If the incident location was Bridge/Highway this column differentiates if the issue was on the Road or the Ramp.
# - BRIDGE_HIGHWAY_SEGMENT: Additional information on the section of the Bridge/Highway were the incident took place.
# - LATITUDE: Geo based Lat of the incident location
# - LONGITUDE: Geo based Long of the incident location
# - LOCATION: Combination of the geo based lat & long of the incident location

# ### Business Context
# The table is real-world 311 service request data from New York City related to Street Condition. In the case of our app, it is used to display a heatmap of all the service requests around the city. You should be able to use the table data above to answer user queries about Street Condition-related service requests in New York City in the year 2025.

# ### Constraints
# The data is restricted to only New York City, 2025.

# ---

# ## 2. User Request

# "{user_query}"

# ---

# ## 3. Instructions for SQL Generation

# - Only use the columns provided in the metadata.  
# - Generate efficient SQL, avoid unnecessary joins or subqueries.  
# - Apply filters, aggregations, or sorting if implied by the request.  
# - Use proper Snowflake SQL syntax.  
# - Output **only the SQL code**, no explanations or commentary.  
# - If the user request is ambiguous and could map to multiple interpretations, choose the one most consistent with the metadata provided.
# """
    nlq_prompt = f"""You are an AI that converts **natural language requests into SQL** for Snowflake. Generate **syntactically correct SQL** for the user request that will run in Snowflake without errors. Be precise, efficient, and include only needed columns.
    
    ## Database Metadata
    - Table: PLOTHOLES.NYC_STREET_DATA.STREET_DATA
    - Columns: UNIQUE_KEY, CREATED_DATE, CLOSED_DATE, AGENCY, COMPLAINT_TYPE, DESCRIPTOR, LOCATION_TYPE, INCIDENT_ZIP, STREET_NAME, BOROUGH, LATITUDE, LONGITUDE, STATUS, DUE_DATE, RESOLUTION_DESCRIPTION, LOCATION
    - Table contains NYC 311 street condition service requests in the year 2025
    
    ## User Request

    "{user_query}"

    ## Instructions
    - Generate **syntactically correct SQL** for the user request that will run in Snowflake without errors. Be precise, efficient, and include only needed columns.
    - Only use columns listed above.
    - Apply filters, aggregation, or sorting if implied.
    - Use proper Snowflake SQL syntax.
    - Output **only SQL**, no explanations.
"""
    
    return nlq_prompt