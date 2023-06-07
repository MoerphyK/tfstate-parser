import json
import os
import requests
import datetime

# from state_parser import TFState
from compliance_checker import ComplianceChecker

from aws_lambda_powertools import Logger
import boto3
from boto3.dynamodb.conditions import Attr

rules_table             = os.environ['RULES_TABLE']
reporting_bucket        = os.environ['REPORTING_BUCKET']
tfe_client_secret       = os.environ['TFE_TOKEN_CREDENTIALS']
tfe_endpoint            = os.environ['TFE_ENDPOINT']

# Init secretsmanager from boto3
sm_client       = boto3.client('secretsmanager')
s3_client       = boto3.client('s3')
dynamodb        = boto3.resource('dynamodb')
table           = dynamodb.Table(rules_table)

# Default timeouts for requests to the puppet api (in seconds)
default_request_timeout = 15.0

service="tfstate-parser-rules-to-workspace"
logger = Logger(service=service)

###############
#### Input ####
###############
# id
# name
# organization
# environment
# state_version
# tag-names = [tag1,tag2,tag3]

##########################
#### Helper Functions ####
##########################

def slim_providers(full_provider):
        '''
        Extract the provider from the full provider string
        params: full_provider - full provider string
        returns: provider - provider string
        '''
        # Find the position of the first and last slashes
        start_index = full_provider.find('"')+1
        end_index = full_provider.rfind('"')

        # Extract the substring between the slashes split it by / and get the last element all in uppercase
        provider = full_provider[start_index:end_index].split('/')[-1].upper()
        return provider

def slim_down_resource_types(full_resource_types):
        '''
        Extract the resource types from the resource types : count dictionary
        params: full_resource_types - full resource types string
        returns: resource_types - list of resource types
        '''
        resource_types = []
        for resource_type in full_resource_types:
                resource_types.append(resource_type)
        return resource_types

def upload_results_to_s3(results, workspace):
        # Upload results to S3, while the key is generated from the workspace information
        logger.info("Uploading results to S3")
        # Generate current date for the s3 key
        # TODO: Upload the results as a csv file
        key = f"{workspace['report_date']}/{workspace['organization']}/{workspace['name']}/results.json"
        # Upload the results to S3
        response = s3_client.put_object(
                Body=json.dumps(results),
                Bucket=reporting_bucket,
                Key=key
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                return key
        else:
                logger.error(f"Failed to upload results to S3. Key = {key}")
                raise Exception(f"Failed to upload results to S3. Key = {key}")

#######################
#### TFE Functions ####
#######################

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

def get_tf_state(state_download_url):
        '''
        Get the tfstate from Terraform Enterprise
        params: state_download_url - url to download the tfstate from
        returns: tfstate
        '''
        logger.info(f"Getting tfstate from url: {state_download_url}")
        response = requests.get(state_download_url, timeout=default_request_timeout)
        if response.status_code == 200:
                logger.info(f"Successfully got tfstate from url: {state_download_url}")
                tf_state = json.loads(response.text)
                return tf_state
        else:
                logger.error(f"Failed to get tfstate from url: {state_download_url}")
                raise Exception(f"Failed to get tfstate from url: {state_download_url}")

########################
#### Main Functions ####
########################

def get_resource_types(state_version):
        '''
        Extract the resource types from the state version
        params: state_version - state version to extract resource types from
        returns: resource_types - dict of providers and resource types
        '''
        logger.info(f"Getting providers from state version {state_version['id']}")
        resource_types = {}
        # Get the providers from the state version
        providers = state_version['attributes']['providers']

        # If there are no providers, return an empty dict
        if providers == []:
                logger.info(f"No providers found in state version {state_version['id']}")
                return resource_types
        # If there are providers, extract the provider and resource types
        else:
                for provider in providers:
                        slim_provider = slim_providers(provider)
                        slim_resource_types = slim_down_resource_types(providers[provider])
                        resource_types[slim_provider] = slim_resource_types

        ## Output format
        # { 
        #        { "AWS": ["aws_vpc", "aws_subnet", "aws_iam_role"] },
        #        { "AZURE": ["azure_storage", "azure_iam_user"] }
        # }

        return resource_types

# def find_rule_keys(entity, environment, resource_types):
#         '''
#         Find the rule s3 keys that match the entity, environment and resource types
#         params: entity - entity to find rules for
#                 environment - environment to find rules for
#                 resource_types - dict of providers and resource types
#         returns: filtered_rule_keys - list of rule s3 keys
#         '''
#         filtered_rule_keys = []
#         # For each provider, get the resource types and find the rules
#         for provider in resource_types:
#                 # Get the rule s3 keys that match the entity, environment, provider and resource types
#                 response = table.scan(
#                 FilterExpression=
#                         Attr('Entity').eq('ALL') &
#                         Attr('Environment').eq('ALL') &
#                         Attr('Provider').eq('AWS') &
#                         Attr('ResourceType').is_in(resource_types[provider])
#                 )
#                 if 'Items' not in response:
#                         logger.info(f"No rules found for entity {entity}, environment {environment}, provider {provider} and resource types {resource_types[provider]}")
#                         continue
#                 else:
#                         items = response['Items']
#                         # For each found rule, add the s3 key to the list of filtered rule keys
#                         for item in items:
#                                 filtered_rule_keys.append(item['S3Key'])

#         return filtered_rule_keys

def get_rules(workspace, resource_types):
        '''
        Find the rule s3 keys that match the entity, environment and resource types
        params: entity - entity to find rules for
                environment - environment to find rules for
                resource_types - dict of providers and resource types
        returns: rules - list of rule items
        '''
        entity = workspace['entity']
        environment = workspace['environment']

        # For each provider, get the resource types and find the rules
        for provider in resource_types:
                # Get the rule s3 keys that match the entity, environment, provider and resource types
                ## TODO:: Add second scan for entity and environment
                response = table.scan(
                        FilterExpression = (
                                (Attr('Entity').eq('ALL') | Attr('Entity').eq(entity.upper())) &
                                (Attr('Environment').eq('ALL') | Attr('Environment').eq(environment.upper())) &
                                Attr('Provider').eq(provider) &
                                Attr('ResourceType').is_in(resource_types[provider])
                        )
                )
                if 'Items' not in response:
                        logger.info(f"No rules found for entity {entity}, environment {environment}, provider {provider} and resource types {resource_types[provider]}")
                        continue
                else:
                        logger.info(f"Found rules for entity {entity}, environment {environment}, provider {provider} and resource types {resource_types[provider]}")
                        rules = response['Items']
                        return rules

def lambda_handler(event, context):
        '''
        params: event - event data
                context - lambda context
        returns: workspace data
        '''
        workspace = event
        
        ## Load state version from Terraform Enterprise API
        state_version = get_state_version(workspace['state_version'])
        
        ## Store state download url
        # TODO: Check which download URL is more useful
        # "hosted-state-download-url": "downloadurl"
        # "hosted-json-state-download-url": "downloadurl"
        workspace['state_download_url'] = state_version['attributes']['hosted-state-download-url']

        ## Extract provider names and resource types from state version
        resource_types = get_resource_types(state_version)

        ## Find rules for entity, environment and resource types
        rules = get_rules(workspace, resource_types)
        results = []
        if rules == []:
                return results
        else:
                tf_state = get_tf_state(workspace['state_download_url'])
                cc = ComplianceChecker()
                sorted_state = cc.rearrange_tfstate(tf_state)
                for rule in rules:
                        logger.info(f"Apply rule {rule['S3Key']} for entity {rule['Entity']}, environment {rule['Environment']}, provider {rule['Provider']} and resource type {rule['ResourceType']}")
                        results.append(cc.check_compliance(rule, sorted_state))
        # TODO: Format the results to be converted more easily
        result_s3_key = upload_results_to_s3(results, workspace)

        return result_s3_key