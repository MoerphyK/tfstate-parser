from aws_lambda_powertools import Logger
import boto3
import json
import os
import requests

# Init secretsmanager from boto3
sm_client = boto3.client('secretsmanager')

tfe_client_secret       = os.environ['TFE_CLIENT_CREDENTIALS']
tfe_endpoint            = os.environ['TFE_ENDPOINT']

# Default timeouts for requests to the puppet api (in seconds)
default_request_timeout = 15.0

service="tfstate-parser-get-workspaces"
logger = Logger(service=service)

def get_tfe_token():
        '''
        Get the TFE token from Secrets Manager
        '''
        logger.info("Getting TFE token from Secrets Manager")
        response = sm_client.get_secret_value(
                SecretId=tfe_client_secret
        )
        if 'SecretString' in response:
                logger.info("Successfully got TFE token from Secrets Manager")
                return json.loads(response['SecretString'])['token']
        else:
                logger.error("Failed to get TFE token from Secrets Manager")
                raise Exception("Failed to get TFE token from Secrets Manager")
        
def parse_workspace_infos(workspaces):
        '''
        Parse the workspaces from the Terraform Enterprise API response
        into a list of dictionaries with the following attributes:
        id, name, organization, csp, environment, state_version, tags
        params: workspaces (list)
        return value: short_workspaces (list)
        '''
        # Parse the workspace for important attributes
        logger.debug(f"Parsing workspaces from {workspaces} response")
        short_workspaces = []
        for workspace in workspaces:
                # TODO: Verify None is the correct check
                # Skip workspaces that currently do not have a state
                if workspace['relationships']['current-state-version']['data'] == None:
                        continue
                short_workspace = {}
                short_workspace['id'] = workspace['id']
                short_workspace['name'] = workspace['attributes']['name']
                short_workspace['organization'] = workspace['relationships']['organization']['data']['id']
                short_workspace['environment'] = short_workspace['name'].split('-')[-1]
                short_workspace['state_version'] = workspace['relationships']['current-state-version']['data']['id']
                # TODO: Get Environment from workspace tags
                if 'tag-names' in workspace['attributes']:
                        short_workspace['tags'] = workspace['attributes']['tag-names']

                short_workspaces.append(short_workspace)
        return short_workspaces

def get_workspaces(org_id):
        '''
        Get all workspaces from a Terraform Enterprise organization
        params: org_id (string)
        return value: workspaces (list)
        '''
        # Get all workspaces from a Terraform Enterprise organization
        logger.info(f"Getting all workspaces from {org_id}")
        headers = {
                'authorization': "Bearer " + get_tfe_token(),
                'content-type': "application/vnd.api+json"
        }
        url = tfe_endpoint + f"/organizations/{org_id}/workspaces"

        response = requests.request("GET", url, headers=headers)
        if response.status_code == 200:
                logger.info(f"Status Code: {response.status_code}\nSuccessfully got all workspaces from {org_id}")
                r = json.loads(response.text)
                return parse_workspace_infos(r['data'])
        else:
                logger.error(f"Failed to get all workspace from Terraform Enterprise organization '{org_id}'")
                raise Exception(f"Status Code: {response.status_code}\nError: {json.loads(response.text)}")


def lambda_handler(event, context):
        '''
        Retrieve all workspaces from the current organization
        '''
        logger.info("Retrieving all workspaces from the current organization")
        org_id = event['organization']
        return get_workspaces(org_id)