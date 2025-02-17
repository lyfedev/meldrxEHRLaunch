import requests
import base64
import json

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FHIRClient:
    def __init__(self, base_url, access_token, access_token_type):
        self.base_url = base_url
        self.access_token = access_token
        self.access_token_type = access_token_type

    # Initialize the FHIRClient with no authentication...
    @staticmethod
    def for_no_auth(base_url):
        return FHIRClient(base_url, None, None)

    # Initialize the FHIRClient with a Bearer token...
    @staticmethod
    def for_bearer_token(base_url, accessToken):
        return FHIRClient(base_url, accessToken, "Bearer")

    # Initialize the FHIRClient for Basic Auth...
    @staticmethod
    def for_basic_auth(base_url, user, pwd):
        # Create the access token by combining user/pwd...
        access_token = user + ':' + pwd
        access_token = base64.b64encode(access_token.encode('utf-8')).decode('utf-8')
        return FHIRClient(base_url, access_token, "Basic")

    # Initialize the FHIRClient with a client secret...
    @staticmethod
    def for_client_secret(meldrx_base_url, workspace_id, client_id, client_secret, scope):
        token_url = meldrx_base_url + '/' + workspace_id + '/connect/token'
        fhir_url = meldrx_base_url + '/api/fhir/' + workspace_id
        print(token_url)
        print(fhir_url)
        print(client_id)

        theAuth = 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode('utf-8')).decode('utf-8')
        print(theAuth)

        # Do a client secret post to get an access token...
        data = {
            'grant_type': 'client_credentials',
            'scope': scope,
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode('utf-8')).decode('utf-8')
        }
        verify = False
        print(data)
        print(headers)
        response = requests.post(token_url, data, headers=headers, verify=verify)
        print(response)
        response = response.json()
        print(response)

        access_token = response['access_token']

        return FHIRClient.for_bearer_token(fhir_url, access_token)

    # Read a FHIR resource...
    def read_resource(self, resourceType, resourceId):
        url = self.__construct_fhir_url(resourceType, resourceId)
        response = requests.get(url, headers=self.__get_headers())
        return response.json()

    # Search for a FHIR resource...
    def search_resource(self, resourceType, params):
        url = self.__construct_fhir_url(resourceType)
        response = requests.get(url, params, headers=self.__get_headers())
        return response.json()

    # Create a FHIR resource...
    def create_resource(self, resourceType, data):
        url = self.__construct_fhir_url(resourceType)
        body = json.dumps(data)
        response = requests.post(url, body, headers=self.__get_headers())
        return response.json()

    # Update a FHIR resource...
    def update_resource(self, resourceType, resourceId, data):
        url = self.__construct_fhir_url(resourceType, resourceId)
        body = json.dumps(data)
        response = requests.put(url, body, headers=self.__get_headers())
        return response.json()

    # Delete a FHIR resource...
    def delete_resource(self, resourceType, resourceId):
        url = self.__construct_fhir_url(resourceType, resourceId)
        response = requests.delete(url, headers=self.__get_headers())
        return response.json()

    # Get the authorization header for this instance...
    def __get_auth_header_value(self):
        return self.access_token_type + ' ' + self.access_token

    # Get headers needed for requests
    def __get_headers(self):
        headers = {
            'Content-Type': 'application/json'
        }

        # If there's an access token, add it to the headers...
        if (self.access_token) and (self.access_token_type):
            headers['Authorization'] = self.__get_auth_header_value()

        return headers

    # Construct the FHIR URL...
    def __construct_fhir_url(self, resourceType, resourceId = None, historyVersion = None):
        url = self.base_url + '/' + resourceType
        if resourceId:
            url += '/' + resourceId

        if historyVersion:
            url += '/_history/' + historyVersion

        return url