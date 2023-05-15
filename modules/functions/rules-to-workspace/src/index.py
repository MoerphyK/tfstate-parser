from aws_lambda_powertools import Logger
import boto3
import json
import os
import requests

# Init secretsmanager from boto3
sm_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')

rules_bucket            = os.environ['RULES_BUCKET']
tfe_client_secret       = os.environ['TFE_CLIENT_CREDENTIALS']
tfe_endpoint            = os.environ['TFE_ENDPOINT']


# Default timeouts for requests to the puppet api (in seconds)
default_request_timeout = 15.0

service="tfstate-parser-rules-to-workspace"
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

def get_state_version(state_id):
        '''
        Useful documentation:
                https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-versions#show-a-state-version
                        GET  https://app.terraform.io/api/v2/state-versions/<state_id>
        Get the state version from Terraform Enterprise
        params: state_id - id of the state version to retrieve
        returns: state version
        '''

        logger.info(f"Checking state version {state_id} for providers")
        headers = {
                "authorization": "Bearer " + get_tfe_token(),
                "content-type": "application/vnd.api+json"
        }
        url = tfe_endpoint + f"/state-versions/{state_id}"
        response = requests.get(url, headers=headers, timeout=default_request_timeout)
        if response.status_code == 200:
                logger.info(f"Successfully got state version {state_id}")
                return json.loads(response.text)['data']
        else:
                logger.error(f"Failed to get state version {state_id}")
                raise Exception(f"Failed to get state version {state_id}")
        
def get_state_providers(state_version):
        '''
        Get the providers from the state version
        params: state_version - state version to get providers from
        returns: list of providers
        '''
        logger.info(f"Getting providers from workspace {state_version['relationships']['workspace']['data']['id']}")
        # Implement logic to transform state version providers into a list of provider names
        providers = state_version['attributes']['providers']
        return providers

def generate_s3_keys(workspace, provider):
        '''
        Generate S3 keys based on the workspace data
        params: workspace - workspace data
                provider - provider to generate keys for
        returns: list of S3 keys
        '''
        environment = workspace['environment']
        entity = workspace['organization']
        csp = workspace['csp']
        # TODO: Get CSP from provider list

        # Global rules
        global_rules_prefix = f'/all/{csp}/'
        # Entity rules
        entity_rules_prefix = f'/{entity}/{csp}/{environment}/'

        # Look for s3 objects based on prefix
        # TODO: Implement logic to check if the object exists
        global_rules = s3_client.list_objects_v2(Bucket=rules_bucket, Prefix=global_rules_prefix)
        entity_rules = s3_client.list_objects_v2(Bucket=rules_bucket, Prefix=entity_rules_prefix)
        rule_keys = []
        return rule_keys

def lambda_handler(event, context):
        '''
        params: event - event data
                context - lambda context
        returns: workspace data
        '''
        workspace = event
        # Load state version from Terraform Enterprise API
        state_version = get_state_version(workspace['state_version'])
        providers = get_state_providers(state_version)

        # Generate S3 Keys based on workspace data
        s3_keys = generate_s3_keys(workspace, providers)
        if s3_keys != []:
                workspace['rule_keys'] = s3_keys

        return workspace