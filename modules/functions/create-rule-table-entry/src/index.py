from aws_lambda_powertools import Logger
import boto3
import json
import os

# Init service clients from boto3
s3_client = boto3.client('s3')
ddb_client = boto3.client('dynamodb')

rules_bucket = os.environ['RULES_BUCKET']
rules_table = os.environ['RULES_TABLE']

service="tfstate-parser-create-rule-table-entry"
logger = Logger(service=service)

####################
#### Attributes ####
####################
compliance_levels = ['hard_mandatory', 'soft_mandatory', 'check']
rule_structure = ['provider', 'resource_type', 'description', 'compliance_level', 'condition']

##########################
#### Helper Functions ####
##########################

def validate_object(record):
        '''
        Validate the object that triggered the lambda
        params: record - the record from the event
        return: None
        '''
        # Check object originated from the correct bucket
        if record['s3']['bucket']['name'] != rules_bucket:
                logger.error(f"Received record from unexpected bucket: {record['s3']['bucket']['name']}")
                raise Exception(f"Received record from unexpected bucket: {record['s3']['bucket']['name']}")

        # Check if object is a json file
        if record['s3']['object']['key'].split('.')[-1] != 'json':
                logger.error(f"Received object is not a json file: {record['s3']['object']['key']}")
                raise Exception(f"Received object is not a json file: {record['s3']['object']['key']}")

        # Check if object is in the correct location
        key_structure = record['s3']['object']['key'].split('/')
        if len(key_structure) != 4 or key_structure[2] not in ['DEV','QA','PROD', 'ALL']:
                logger.error(f"Received object is not in a valid location: {record['s3']['object']['key']}")
                raise Exception(f"Received object is not in the valid location: {record['s3']['object']['key']}")
        
def validate_rule_object(rule, object_key):
        '''
        Validate the rule object
        params: rule - the rule object
                object_key - the key of the object that triggered the lambda
        return: None
        '''
        # Check if rule has the correct structure
        for key in rule_structure:
                if key not in rule:
                        logger.error(f"Rule object is missing required fields: {key}")
                        raise Exception(f"Rule object is missing required fields: {key}")              
        if 'rules' not in rule['condition']:
                logger.error(f"Rule object is missing required fields: {rule}")
                raise Exception(f"Rule object is missing required fields: {rule}")
        if len(rule['condition']['rules']) > 1 and 'operator' not in rule['condition']:
                # TODO: Check if operator is valid for the number of rules
                logger.error(f"Rule object has multiple rules but not operator: {rule}")
                raise Exception(f"Rule object has multiple rules but not operator: {rule}")
                        
        # Validate provider
        if rule['provider'].split('/')[-1].upper() != object_key.split('/')[1]:
                logger.error(f"Rule object does not match s3_key provider: {object_key} & {rule['provider'].split('/')[-1].upper()}")
                raise Exception(f"Rule object does not match s3_key provider: {object_key} & {rule['provider'].split('/')[-1].upper()}")
        # Validate compliance level
        if rule['compliance_level'] not in compliance_levels:
                logger.error(f"Rule object has invalid compliance level: {rule['compliance_level']} must be one of {compliance_levels}")
                raise Exception(f"Rule object has invalid compliance level: {rule['compliance_level']} must be one of {compliance_levels}")
        # Validate condition
        # TODO: Validate condition

def load_rule(object_key):
        '''
        Load the rule from the bucket and convert into dictionary
        params: object_key - the key of the object that triggered the lambda
        return: rule - the rule object
        '''
        # Load the rule from the bucket and convert into dictionary
        rule = json.loads(s3_client.get_object(Bucket=rules_bucket, Key=object_key)['Body'].read().decode('utf-8'))
        logger.info(f"Loaded rule: {rule}")
        validate_rule_object(rule, object_key)
        return rule

def convert_rule_to_ddb_item(rule, object_key):
        '''
        Convert the rule object into a DynamoDB item
        params: rule - the rule object
                object_key - the key of the object that triggered the lambda
        return: item_data - the DynamoDB item
        '''
        split_object_key = object_key.split('/')
        provider = split_object_key[1]
        entity = split_object_key[0]
        environment = split_object_key[2]
        rule_name = split_object_key[3].split('.')[0]
        item_data = {
                'S3Key': {'S': object_key},
                'ResourceType': {'S': rule['resource_type']},
                'RuleName' : {'S': rule_name},
                'Description': {'S': rule['description']},
                'ComplianceLevel': {'S': rule['compliance_level']},
                'Provider': {'S': provider},
                'Entity': {'S': entity},
                'Environment': {'S': environment},
                'Rule': {'S': json.dumps(rule['condition'])}
        }
        return item_data


###################
#### Functions ####
###################


def create_rule(object_key):
        '''
        Create a rule in the DynamoDB table
        params: object_key - the key of the object that triggered the lambda
        return: None
        '''
        rule = load_rule(object_key)
        item = convert_rule_to_ddb_item(rule, object_key)

        response = ddb_client.put_item(
                TableName=rules_table,
                Item=item,
                ReturnValues='ALL_OLD')
        logger.info(f"DynamoDB response: {response}")

def remove_rule(object_key):
        '''
        Remove a rule from the DynamoDB table
        params: object_key - the key of the object that triggered the lambda
        return: None
        '''
        logger.info(f'Removing rule for object: {object_key}')
        # Query the DynamoDB table for sorting key ResourceType -> necessary to delete the item
        query = ddb_client.query(
                TableName=rules_table,
                KeyConditionExpression='S3Key = :partition_value',
                ExpressionAttributeValues={
                        ':partition_value': {'S': object_key}
                },
                ProjectionExpression='S3Key, ResourceType'
                )

        # Check if the item was found
        if 'Items' in query:
                if len(query['Items']) == 1:
                        item = query['Items'][0]
                        response = ddb_client.delete_item(
                                TableName=rules_table,
                                Key=item,
                                ReturnValues='ALL_OLD')
                elif len(query['Items']) > 1:
                        logger.error(f"Multiple rules found for object: {object_key}")
                        raise Exception(f"Multiple rules found for object: {object_key}")
                else:
                        logger.error(f"Item not found: {object_key}")
                        raise Exception(f"Item not found: {object_key}")
        else:
                logger.error(f"Item not found: {object_key}")
                raise Exception(f"Item not found: {object_key}")
        
        logger.info(f"DynamoDB response: {response}")

def lambda_handler(event, context):
        logger.info(event)
        for record in event['Records']:
                validate_object(record)
                
                # Check record type
                if 'ObjectRemoved' in record['eventName']:
                        logger.info(f"Received record for object removal")
                        remove_rule(record['s3']['object']['key'])
                
                elif 'ObjectCreated' in record['eventName']:
                        logger.info(f"Received record for object creation, processing")
                        create_rule(record['s3']['object']['key'])
                
                else:
                        logger.error(f"Received unexpected record: {record['eventName']}")
                        raise Exception(f"Received unexpected record: {record['eventName']}")