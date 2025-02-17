import streamlit as st
from streamlit_oauth import OAuth2Component
from meldrx_fhir_client import FHIRClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Streamlit page config
st.set_page_config(page_title="MeldRX EHR Launch", page_icon="🩺", layout="wide")
st.title("MeldRX EHR Patient Viewer")

# Load OAuth2 Configuration from .env
AUTHORIZE_URL = os.getenv("AUTHORIZE_URL")
TOKEN_URL = os.getenv("TOKEN_URL")
REFRESH_TOKEN_URL = os.getenv("REFRESH_TOKEN_URL")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Load API and workspace details from .env
MELDRX_BASE_URL = os.getenv("MELDRX_BASE_URL")
MELDRX_WORKSPACE_URL = os.getenv("MELDRX_WORKSPACE_URL")
MELDRX_WORKSPACE_ID = os.getenv("MELDRX_WORKSPACE_ID")

# OAuth2 Scope
SCOPE = os.getenv("SCOPE")

# Initialize OAuth2 component
oauth2 = OAuth2Component(
    CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REFRESH_TOKEN_URL
)

# Function to retrieve CarePlan details (only active plans)
def get_careplan(fhir_client, patient_id):
    """Fetches and filters active CarePlans for a given patient."""
    try:
        careplans = fhir_client.search_resource("CarePlan", {"patient": patient_id})
        if "entry" in careplans:
            return [
                entry["resource"] for entry in careplans["entry"] if entry["resource"].get("status") == "active"
            ]
    except Exception:
        return []
    return []

# Function to fetch the Location Name
def get_location_name(fhir_client, location_reference):
    """Fetches Location details by ID and returns the name."""
    if not location_reference:
        return "N/A"

    try:
        location_id = location_reference.split("/")[-1]
        location = fhir_client.read_resource("Location", location_id)

        if location and "name" in location:
            return location["name"]
    except Exception:
        return "N/A"

    return "N/A"

# Ensure session state for authentication
if "token" not in st.session_state:
    st.warning("You must log in to view patient data.")

    result = oauth2.authorize_button(
        name="Login with MeldRX",
        redirect_uri="http://localhost:8501",
        scope=SCOPE,
        extras_params={'aud': MELDRX_WORKSPACE_URL},
        pkce="S256"
    )

    if result and "token" in result:
        st.session_state["token"] = result.get("token")
        st.rerun()

# If authenticated, proceed to display patient data
if "token" in st.session_state:
    access_token = st.session_state["token"]["access_token"]
    st.text_area("Current Token", access_token, height=150)

    # Initialize FHIRClient with authentication token
    fhir_client = FHIRClient(
        base_url=MELDRX_WORKSPACE_URL,
        access_token=access_token,
        access_token_type="Bearer",
    )

    # Fetch and display patient list
    st.header("Patients List")

    try:
        patients = fhir_client.search_resource("Patient", {})

        if "entry" in patients:
            for entry in patients["entry"]:
                resource = entry["resource"]
                
                # Extract patient details
                patient_id = resource.get("id", "N/A")
                first_name = resource.get("name", [{}])[0].get("given", ["N/A"])[0]
                last_name = resource.get("name", [{}])[0].get("family", "N/A")
                birth_date = resource.get("birthDate", "N/A")

                # Fetch Location Name
                location_reference = resource.get("managingOrganization", {}).get("reference", "")
                location_name = get_location_name(fhir_client, location_reference)

                # Retrieve CarePlan details (only active ones)
                careplans = get_careplan(fhir_client, patient_id)

                # Display patient details
                with st.expander(f"Patient: {first_name} {last_name} (ID: {patient_id})"):
                    st.write(f"**Date of Birth:** {birth_date}")
                    st.write(f"**Location Name:** {location_name}")

                    # Display CarePlan details
                    st.subheader("Active Care Plans")
                    if careplans:
                        for careplan in careplans:
                            st.write("📌 **CarePlan Details:**")

                            # Extract Category Display
                            categories = [
                                cat["coding"][0].get("display", "N/A") 
                                for cat in careplan.get("category", []) if "coding" in cat
                            ]
                            st.write(f"**Category:** {', '.join(categories) if categories else 'N/A'}")

                            # Extract Period
                            period = careplan.get("period", {})
                            period_text = f"Start: {period.get('start', 'N/A')}, End: {period.get('end', 'N/A')}"
                            st.write(f"**Period:** {period_text}")

                            # Extract Activity Details (detail > code > text)
                            activities = [
                                act["detail"]["code"].get("text", "N/A") 
                                for act in careplan.get("activity", []) 
                                if "detail" in act and "code" in act["detail"]
                            ]
                            st.write("**Activities:**")
                            if activities:
                                for activity in activities:
                                    st.markdown(f"- {activity}")
                            else:
                                st.write("No activities listed.")

                    else:
                        st.write("No active Care Plans available.")

        else:
            st.warning("No patients found.")
    except Exception as e:
        st.error(f"Error fetching patients: {str(e)}")