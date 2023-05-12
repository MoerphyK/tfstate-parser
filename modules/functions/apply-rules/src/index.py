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
tfe_auth_endpoint       = os.environ['TFE_AUTH_ENDPOINT']

# Default timeouts for requests to the puppet api (in seconds)
default_request_timeout = 15.0

service="tfstate-parser-apply-rules"
logger = Logger(service=service)

def lambda_handler(event, context):
        ## Check the origin of this call
        return "Test"