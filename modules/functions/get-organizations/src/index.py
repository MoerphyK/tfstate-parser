from aws_lambda_powertools import Logger
import boto3
import json
import os
import requests
import datetime

# Init secretsmanager from boto3
sm_client = boto3.client('secretsmanager')

# Get environment variables
tfe_client_secret       = os.environ['TFE_TOKEN_CREDENTIALS']
tfe_endpoint            = os.environ['TFE_ENDPOINT']
current_date            = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

# Default timeouts for requests to the puppet api (in seconds)
default_request_timeout = 15.0

service="tfstate-parser-get-organizations"
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
        
def parse_organization_ids(orgas):
        '''
        Parse the organization ids from the response
        params: orgas - list of organizations
        returns: list of organization ids
        '''
        logger.debug("Parsing organization ids from response")
        orga_ids = []
        for orga in orgas:
                orga_ids.append(orga['id'])
        logger.debug(f"Successfully parsed organization ids from response:\n{str(orga_ids)}")
        return orga_ids

def get_organizations():
        '''
        Get all organizations from Terraform Enterprise
        returns: list of organization ids
        '''
        
        logger.info("Getting all organizations from Terraform Enterprise")
        headers = {
                'authorization': "Bearer " + get_tfe_token(),
                'content-type': "application/vnd.api+json"
        }
        url = tfe_endpoint + "/organizations"

        response = requests.request("GET", url, headers=headers)
        if response.status_code == 200:
                logger.info(f"Status Code: {response.status_code}\nSuccessfully got all organizations from Terraform Enterprise")
                r = json.loads(response.text)
                return parse_organization_ids(r['data'])
        else:
                logger.error("Failed to get all organizations from Terraform Enterprise")
                raise Exception(f"Status Code: {response.status_code}\nError: {json.loads(response.text)}")

def lambda_handler(event, context):
        '''
        Get all organizations from Terraform Enterprise
        params: event (dict)
        returns: list of organization ids
        '''
        logger.info("Starting parameter validation")
        orgas = []        
        ## Check if any organizations has been passed in the event
        if 'organizations' in event and event['organizations'] != "":
                logger.debug(f"Organizations has been passed in the event.\n{str(event['organizations'])}")
                orgas = event['organizations']
        else:
                ## If no organizations has been passed, get all organizations
                orgas = get_organizations()
        
        ## Create a list of dictionaries with the organization name and the current date for the mapstate
        org_dict = []
        for org in orgas:
                org_dict.append({'organization':org, 'date': current_date})
        return org_dict