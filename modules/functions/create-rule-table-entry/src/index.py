from aws_lambda_powertools import Logger
import boto3
import json
import os
import requests

# Init secretsmanager from boto3
s3_client = boto3.client('s3')
ddb_client = boto3.client('dynamodb')

rules_bucket = os.environ['RULES_BUCKET']
rules_table = os.environ['RULES_TABLE']

# Default timeouts for requests to the puppet api (in seconds)
default_request_timeout = 15.0

service="tfstate-parser-create-rule-table-entry"
logger = Logger(service=service)

def lambda_handler(event, context):
        ## Check the origin of this call
        return "Test"