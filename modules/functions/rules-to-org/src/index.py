from aws_lambda_powertools import Logger
import boto3
import json
import os
import requests

# Init secretsmanager from boto3
s3_client = boto3.client('s3')

# Default timeouts for requests to the puppet api (in seconds)
default_request_timeout = 15.0

service="tfstate-parser-parameter-validation"
logger = Logger(service=service)

def lambda_handler(event, context):
        ## Check the origin of this call
        return "Test"