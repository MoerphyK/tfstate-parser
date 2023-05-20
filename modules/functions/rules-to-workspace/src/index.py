import json
import os
import requests
import re
import operator

# from state_parser import TFState
from compliance_checker import ComplianceChecker

from aws_lambda_powertools import Logger
import boto3
from boto3.dynamodb.conditions import Attr

rules_table             = os.environ['RULES_TABLE']
tfe_client_secret       = os.environ['TFE_CLIENT_CREDENTIALS']
tfe_endpoint            = os.environ['TFE_ENDPOINT']

# Init secretsmanager from boto3
sm_client = boto3.client('secretsmanager')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(rules_table)




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

def get_operator_function(operator_str):
        '''
        Returns the operator function for a given operator string.
        param operator_str: The operator string to get the operator function for.
        Returns: The operator function.
        '''
        operator_map = {
            'eq': operator.eq,
            'neq': operator.ne,
            'contains': operator.contains,
            'not_contains': lambda a, b: not operator.contains(a, b),
            'exists': lambda a, b: isinstance(a, str) or bool(a) == b, ## Does not work with NullType
            'not_exists': lambda a, b: isinstance(a, str) or bool(a) != b, ## Does not work with NullType
            'matches': lambda a, b: bool(re.match(str(b), str(a))), ## Does not work with dict
            'not_matches': lambda a, b: not bool(re.match(str(b), str(a))), ## Does not work with dict
            'and': all, ## Works with list of bools
            'or': any ## Works with list of bools
        }
        return operator_map.get(operator_str)

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

def slim_resource_types(full_resource_types):
        '''
        Extract the resource types from the full resource types string
        params: full_resource_types - full resource types string
        returns: resource_types - list of resource types
        '''
        resource_types = []
        for resource_type in full_resource_types:
                resource_types.append(resource_type)
        return resource_types

def rearrange_tfstate(tfstate):
    '''
    Rearrange the tfstate to be grouped by provider and resource type
    params: tfstate - tfstate to rearrange
    returns: rearranged tfstate
    '''
    rearranged_dict = {}
    slimmed_rearranged_dict = {}

    for item in state['resources']:
        provider = item["provider"]
        resource_type = item["type"]

        if provider not in rearranged_dict:
            rearranged_dict[provider] = {}

        if resource_type not in rearranged_dict[provider]:
            rearranged_dict[provider][resource_type] = []

        rearranged_dict[provider][resource_type].append(item)

    for provider in rearranged_dict:
        slimmed_rearranged_dict[slim_providers(provider)] = rearranged_dict[provider]
    return slimmed_rearranged_dict

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
                        slim_resource_types = slim_resource_types(providers[provider])
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

def get_rules(entity, environment, resource_types):
        '''
        Find the rule s3 keys that match the entity, environment and resource types
        params: entity - entity to find rules for
                environment - environment to find rules for
                resource_types - dict of providers and resource types
        returns: rules - list of rule items
        '''
        # For each provider, get the resource types and find the rules
        for provider in resource_types:
                # Get the rule s3 keys that match the entity, environment, provider and resource types
                response = table.scan(
                FilterExpression=
                        Attr('Entity').eq('ALL') &
                        Attr('Environment').eq('ALL') &
                        Attr('Provider').eq('AWS') &
                        Attr('ResourceType').is_in(resource_types[provider])
                )
                if 'Items' not in response:
                        logger.info(f"No rules found for entity {entity}, environment {environment}, provider {provider} and resource types {resource_types[provider]}")
                        continue
                else:
                        logger.info(f"Found rules for entity {entity}, environment {environment}, provider {provider} and resource types {resource_types[provider]}")
                        rules = response['Items']
                        return rules
                

##############################
#### Compliance Functions ####
##############################

def get_attribute_value(attributes, key):
        '''
        Returns the value of a key in a dictionary.
        param attributes: The attributes of the resources parsed from the Terraform state file.
        param key: The key of the resource to search for in the attributes dictionary.
        Returns: The value of the key in the dictionary.
        '''
        keys = key.split('.')
        value = attributes.get(keys[0])

        for k in keys[1:]:
            if isinstance(value, list):
                if k.isdigit() and int(k) < len(value):
                    value = value[int(k)]
                else:
                    value = None
            elif isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
            if value is None:
                break

        return value

def check_rule(rule, attributes):
        '''
        Checks if a rule is valid.
        param rule: The rule to check.
        param attributes: The attributes of the resources parsed from the Terraform state file.
        Returns: A tuple containing a boolean indicating if the rule is valid and a string containing the error message if the rule is invalid.
        '''
        logger.info(f'## Called check_rule ##\n# Attributes:\n{attributes}\n# Rule:\n{rule}')
        # Extract infos from rule
        operator_str = rule.get('operator', '')
        key = rule.get('key', '')
        value = rule.get('value')

        # Get operator
        operator_fn = get_operator_function(operator_str)
        logger.info(f'check_rule - operator: {operator_str}')
        # Check rule inputs validity
        if not key or not operator_str:
            return False, 'Invalid rule'

        actual_value = get_attribute_value(attributes, key)

        if operator_fn is None:
            return False, f'Invalid operator: {operator_str}'
        elif actual_value == None and operator_str == 'contains':
            return False, "Key can't be found in resource attributes."
        elif actual_value == None and operator_str == 'not_contains':
            return True, "Key can't be found in resource attributes."

        return operator_fn(actual_value, value),''

def check_condition(attributes, condition):
        '''
        Checks if a condition is valid.
        param condition: The condition to check.
        param attributes: The attributes of the resources parsed from the Terraform state file.
        Returns: A tuple containing a boolean indicating if the condition is valid and a string containing the error message if the condition is invalid.
        '''
        logger.info(f'## Called check_condition ##\n# Attributes:\n{attributes}\n# Condition:\n{condition}')
        operator_fn = None

        for key, value in condition.items():
            if key == 'operator':
                operator_fn = get_operator_function(value)
                logger.info(f'check_condition - operator: {value}')
            elif key == 'rules':
                rules = value

        if operator_fn is None:
            return False, 'Invalid operator'

        rule_results = []
        for rule in rules:
            result,_ = check_rule(rule,attributes)
            rule_results.append(result)

        logger.info(f'check_condition - results: {rule_results}')
        return operator_fn(rule_results), ''


def check_compliance(state_resources, rule):
        '''
        Checks if a Terraform state file is compliant with a compliance file.
        param state_resources: The pre sorted resources from the Terraform state.
        param rule: The rule.
        Returns: A dictionary containing the compliance result.
        '''
        results = []
        provider = rule['Provider']
        resource_type = rule['ResourceType']
        condition = json.loads(rule['Rule'])
        resources = state_resources[provider][resource_type]

        for resource in resources:
                ## Check if there are multiple instances of the resource, in case of count or for_each
                for instance in resource['instances']:
                        attributes = resource['attributes']
                        is_compliant, reason = check_condition(attributes, condition)

                        result = {
                                'rule_name': rule['RuleName'],
                                'description': rule['Description'],
                                'compliance_level': rule['ComplianceLevel'],
                                'provider': provider,
                                'resource_type': resource_type,
                                'resource_id': attributes.get('id', 'no id found'),
                                'compliance_status': is_compliant,
                                'reason': reason
                        }
                results.append(result)
        ## TODO: Add second return value to indicate if there are any non compliant results
        return results

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
                sorted_state = rearrange_tfstate(tf_state)
                for rule in rules:
                        logger.info(f"Apply rule {rule['S3Key']} for entity {rule['Entity']}, environment {rule['Environment']}, provider {rule['Provider']} and resource type {rule['ResourceType']}")
                        results.append(check_compliance(rule, sorted_state))
        # TODO: Check if the compliance check is working, if so outsource the methods to a separate file
        # TODO: Format the results to be converted more easily
        # TODO: Upload the results to S3
        return results