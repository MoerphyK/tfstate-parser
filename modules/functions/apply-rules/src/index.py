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

service="tfstate-parser-apply-rules"
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
        
def get_rules(s3_keys):
        '''
        Get the rules from S3
        params: s3_keys - list of S3 keys to retrieve
        returns: list of rules
        '''
        logger.info(f"Getting rules from S3 bucket: {rules_bucket}")
        rules = []
        for s3_key in s3_keys:
                logger.info(f"Getting rule from S3 bucket: {rules_bucket} with key: {s3_key}")
                response = s3_client.get_object(
                        Bucket=rules_bucket,
                        Key=s3_key
                )
                rules.append(json.loads(response['Body'].read()))

        logger.info(f"Successfully got rules from S3 bucket: {rules_bucket}")
        return rules

def get_tfstate(workspace):
        '''
        Get the tfstate from Terraform Enterprise
        params: workspace - dictionary containing workspace information
        returns: tfstate
        '''
        logger.info(f"Getting tfstate from workspace: {workspace['workspace_name']}")
        state_url = workspace['state_url']
        logger.debug(f"Getting tfstate from url: {state_url}")
        # TODO: Download tfstate from TFE with requests package
        response = requests.get(state_url)
        
        logger.info(f"Successfully got tfstate from workspace: {workspace['workspace_name']}")
        return json.loads(response['Body'].read())

def apply_rules(rules, tfstate):
        '''
        Apply the rules on the tfstate
        params: rules - list of rules to apply
        params: tfstate - tfstate to apply the rules on
        returns: results - list of results
        '''
        logger.info(f"Applying rules on tfstate")
        results = []
        for rule in rules:
                logger.info(f"Applying rule: {rule['name']} on tfstate")
                #TODO: Apply rule on tfstate
                results.append(rule)

        logger.info(f"Successfully applied rules on tfstate")
        return results


def lambda_handler(event, context):
        '''
        Retrieve the rules from S3 and tfstate from Terraform Enterprise.
        Apply the rules on the tfstate and output the results.
        '''
        workspace = event
        logger.info(f"Received event:\n{str(workspace)}")

        rules = get_rules(workspace['rule_keys'])
        tfstate = get_tfstate(workspace)
        results = apply_rules(rules, tfstate)

        logger.info(f"Returning results")
        return results