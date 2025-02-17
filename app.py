import streamlit as st
from streamlit_oauth import OAuth2Component
from meldrx_fhir_client import FHIRClient
import pandas as pd

# Streamlit page config
st.set_page_config(page_title="MeldRX EHR Launch", page_icon="🩺", layout="wide")
st.title("MeldRX EHR Patient Viewer")

# OAuth2 Configuration
AUTHORIZE_URL = "https://app.meldrx.com/connect/authorize"
TOKEN_URL = "https://app.meldrx.com/connect/token"
REFRESH_TOKEN_URL = "https://app.meldrx.com/connect/token"
CLIENT_ID = "ffd265b9c6c8480c9f3cc81585f3ad3b"
CLIENT_SECRET = "c0kfvvdJ251gpptdQcb_Y0PpFjvMTf"
SCOPE = "openid profile patient/*.read"

# Initialize OAuth2 component
oauth2 = OAuth2Component(
    CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REFRESH_TOKEN_URL
)

# Start authentication
result = oauth2.authorize_button(
    name="Login with MeldRX",
    redirect_uri="http://localhost:8501",
    scope=SCOPE,
    extras_params={'aud': "https://app.meldrx.com/api/fhir/8225e38e-0a11-4d2a-ac71-c372781d630d"},
    pkce="S256"
)

# If user is authenticated, store the token
if result and "token" in result:
    st.session_state["token"] = result.get("token")
    st.success("Successfully authenticated!")

# Display token
if "token" in st.session_state:
    access_token = st.session_state["token"]["access_token"]
    st.text_area("Current Token", access_token, height=150)

    # Initialize FHIRClient with authentication token
    fhir_client = FHIRClient(
        base_url="https://app.meldrx.com/api/fhir/8225e38e-0a11-4d2a-ac71-c372781d630d",
        access_token=access_token,
        access_token_type="Bearer",
    )

    # Fetch and display patient list
    st.header("Patients List")

    try:
        patients = fhir_client.search_resource("Patient", {})

        if "entry" in patients:
            patient_data = []
            for entry in patients["entry"]:
                resource = entry["resource"]
                
                # Extract patient details (Patient ID, First Name, Last Name)
                patient_id = resource.get("id", "N/A")
                first_name = resource.get("name", [{}])[0].get("given", ["N/A"])[0]
                last_name = resource.get("name", [{}])[0].get("family", "N/A")
                
                patient_data.append({"Patient ID": patient_id, "First Name": first_name, "Last Name": last_name})

            # Convert to DataFrame for clean display
            df = pd.DataFrame(patient_data)
            st.dataframe(df)

        else:
            st.warning("No patients found.")
    except Exception as e:
        st.error(f"Error fetching patients: {str(e)}")
else:
    st.warning("Please log in to access patient data.")