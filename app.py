import streamlit as st
from meldrx_fhir_client import FHIRClient
import requests

# Define required constants
MELDRX_WORKSPACE_URL = "https://app.meldrx.com/api/fhir/8225e38e-0a11-4d2a-ac71-c372781d630d"
MELDRX_CLIENT_ID = "ffd265b9c6c8480c9f3cc81585f3ad3b"
MELDRX_CLIENT_SECRET = "c0kfvvdJ251gpptdQcb_Y0PpFjvMTf"
TOKEN_URL = "https://app.meldrx.com/connect/token"
SCOPE = "meldrx-api patient/*.read launch/patient patient/*.* cds"

# Streamlit App Configuration
st.set_page_config(page_title="MeldRX EHR Launch", page_icon="🩺", layout="wide")

st.title("MeldRX EHR Patient Viewer")

# Function to get authentication token
def get_auth_token():
    """Retrieve an authentication token from MeldRX."""
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": MELDRX_CLIENT_ID,
            "client_secret": MELDRX_CLIENT_SECRET,
            "scope": SCOPE,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        st.error(f"Failed to retrieve token: {response.text}")
        return None

# Get and display authentication token
token = get_auth_token()

if token:
    st.success("Successfully authenticated!")
    st.text_area("Current Token", token, height=150)

    # Initialize FHIRClient with the token
    fhir_client = FHIRClient(
        base_url=MELDRX_WORKSPACE_URL,
        access_token=token,
        access_token_type="Bearer",
    )

    # Fetch list of patients
    st.header("Patients List")

    try:
        patients = fhir_client.search_resource("Patient", {})
        if "entry" in patients:
            patient_list = [
                (entry["resource"]["name"][0]["given"][0], entry["resource"]["name"][0]["family"])
                for entry in patients["entry"]
            ]

            # Display patient names in a table
            st.table(patient_list)
        else:
            st.warning("No patients found in the system.")
    except Exception as e:
        st.error(f"Error fetching patients: {str(e)}")
else:
    st.warning("Could not authenticate. Check credentials and try again.")