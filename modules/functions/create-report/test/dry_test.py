from aws_lambda_powertools import Logger
import boto3
import json
import os
from fpdf import FPDF

# Init secretsmanager from boto3
s3_client = boto3.client('s3')

os.environ['REPORTING_BUCKET'] = "tfstate-parser-reports"
reporting_bucket = os.environ['REPORTING_BUCKET']

# PDF Colors
black = (0,0,0)
red = (209, 2, 9)
green = (0, 184, 6)
yellow = (237, 181, 28)

# Default timeouts for requests to the puppet api (in seconds)
default_request_timeout = 15.0



service="tfstate-parser-create-report"
logger = Logger(service=service)

#################
#### S3 Keys ####
#################

def get_s3_keys_by_timestamp(timestamp):
        """Get the S3 keys by timestamp"""
        # Get the list of S3 keys
        json_files = s3_client.list_objects_v2(Bucket=reporting_bucket, Prefix=timestamp)
        # Check if there are any S3 keys
        if json_files.get('Contents'):
                # Get the S3 keys
                s3_keys = [json_file['Key'] for json_file in json_files['Contents']]
                # Example json_files = ["2023-06-19-15-22-50/AXA-GroupOperations/SP-Marvin-Dummy-Resources/results.json", "2023-06-19-15-22-50/AXA-GroupOperations/SP-Compliance-Checker/results.json"]
        else:
                # Raise an exception if there are no S3 keys
                raise Exception(f'No S3 keys found for timestamp: {timestamp}')
        return s3_keys

## Return the timestamp from the SFN success event
## TODO:: Make it use the timestamp from the event instead of the timestamp from the S3 key
def get_s3_keys_from_event(event):
        output = json.loads(event['detail']['output'])
        timestamp = output[0][0].split('/')[0]
        # Example timestamp = "2023-06-19-15-22-50"
        logger.info(f'Event timestamp: {timestamp}')
        return timestamp


########################
#### Obtain Results ####
########################

def add_check_to_dict(checks, new_check):
        '''
        Add a check to the checks list. If the check already exists, add the resource_id to the check.
        params: checks - list of checks
                new_check - check to add to the list
        '''
        # Check if the check already exists in the checks list
        logger.info(f'Adding new check: {new_check}')
        if checks == []:
                new_check['resource_id'] = [new_check['resource_id']]
                checks.append(new_check)
        else:
                check_found = False
                for check in checks:
                        # If the check already exists, add the resource_id to the list
                        if check['rule_name'] == new_check['rule_name'] and check['resource_type'] == new_check['resource_type'] and check['provider'] == new_check['provider']:
                                # Check if check['resource_id'] is a list
                                check_found = True
                                if isinstance(check['resource_id'], list):
                                        check['resource_id'].append(new_check['resource_id'])
                                else:
                                        check['resource_id'] = [check['resource_id'], new_check['resource_id']]
                                break
                # If the check does not exist, add it to the list
                if not check_found:
                        new_check['resource_id'] = [new_check['resource_id']]
                        checks.append(new_check)
                        
        logger.info(f'Checks: {checks}')

def results_to_dict(s3_keys,timestamp):
        '''
        Get the results from the S3 keys and sort them by entity, workspace and rule
        params: s3_keys - list of S3 keys
                timestamp - timestamp of the results
        '''
        result_dict = {
                "timestamp": timestamp,
                "checked_entity_count": 0,
                "compliant_entity_count": 0,
                "non_compliant_entity_count": 0,
                "compliant_entities": [],
                "non_compliant_entities": [],
                "entities": {}
        }

        # Get the results from the S3 keys and sort them by entity, workspace and rule
        for s3_key in s3_keys:
                logger.info(f'Getting results from S3 key: {s3_key}')
                # Get metadata from S3 key
                entity_name = s3_key.split('/')[1]
                workspace_name = s3_key.split('/')[2]
                logger.info(f'Getting results from S3 key: {s3_key}, entity_name: {entity_name}, workspace_name: {workspace_name}')
                # Check if the entity_name exists in the result_dict entity list
                if entity_name not in result_dict['entities']:
                        logger.info(f'Creating entity_name: {entity_name}')
                        # If not, create the entity_name key
                        result_dict['entities'][entity_name] = {
                                "checked_workspaces": 0,
                                "compliant_workspaces": 0,
                                "non_compliant_workspaces": 0,
                                "workspaces": {},
                                "is_compliant": True
                        }
                entity = result_dict['entities'][entity_name]

                # Create entry for workspace
                logger.info(f'Creating workspace_name: {workspace_name}')
                entity['checked_workspaces'] += 1
                # If not, create the workspace_name key
                result_dict['entities'][entity_name]['workspaces'][workspace_name] = {
                        "checks": 0,
                        "compliant_check_count": 0,
                        "non_compliant_check_count": 0,
                        "compliant_checks": [],
                        "failed_checks": [],
                        "is_compliant": True
                }
                workspace = result_dict['entities'][entity_name]['workspaces'][workspace_name]

                # Download JSON file from S3 and turn into a dict
                json_file = s3_client.get_object(Bucket=reporting_bucket, Key=s3_key)
                workspace_data = json.loads(json_file['Body'].read().decode('utf-8'))
                # Get the summary from the JSON file
                for workspace_results in workspace_data:
                        # Check if the workspace is compliant
                        for rule_result in workspace_results:
                                # logger.info(f"Checking rule_result: {rule_result}")
                                workspace['checks'] += 1
                                if rule_result['compliance_status'] == True:
                                        workspace['compliant_check_count'] += 1
                                        add_check_to_dict(workspace['compliant_checks'],rule_result)
                                elif rule_result['compliance_status'] == False:
                                        workspace['non_compliant_check_count'] += 1
                                        workspace['is_compliant'] = False
                                        add_check_to_dict(workspace['failed_checks'],rule_result)
                                        
                                else:
                                        logger.error(f"Rule {rule_result['rule_name']} is not compliant or non-compliant")
                                        raise Exception(f"Rule {rule_result['rule_name']} is not compliant or non-compliant")
                        
                # Count the number of compliant and non-compliant workspaces
                if workspace['is_compliant'] == True:
                        entity['compliant_workspaces'] += 1
                else:
                        entity['non_compliant_workspaces'] += 1
                        entity['is_compliant'] = False
                entity['workspaces'][workspace_name] = workspace

        # Count the number of compliant and non-compliant entities
        for entity_name, entity in result_dict['entities'].items():
                result_dict['checked_entity_count'] += 1
                if entity['is_compliant'] == True:
                        result_dict['compliant_entity_count'] += 1
                        result_dict['compliant_entities'].append(entity_name)
                else:
                        result_dict['non_compliant_entity_count'] += 1
                        result_dict['non_compliant_entities'].append(entity_name)

        logger.info(f"Converted results: {result_dict}")
        return result_dict

#########################
#### Report Creation ####
#########################

def create_title_page(pdf, result_dict):
        '''
        Create the title page of the report
        params: pdf - PDF object
                result_dict - dict of results
        '''
        ### Add TITLE PAGE ###
        pdf.add_page()
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(0, 10, 'Terraform Compliance Report', align='C')
        pdf.ln()
        # Add the timestamp
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, result_dict["timestamp"], align='C')
        pdf.ln()

        # Add the summary table
        pdf.set_font('Arial', 'B', 12)
        with pdf.table(first_row_as_headings=False, text_align="C", width=100, col_widths=(70, 30)) as table:
                row = table.row()
                row.cell("Entites Checked")
                row.cell(str(result_dict["checked_entity_count"]))
                
                row = table.row()
                pdf.set_font('Arial', 'B', 12)
                pdf.set_text_color(green) 
                row.cell("Compliant Entities")
                row.cell(str(result_dict["compliant_entity_count"]))
                
                row = table.row()
                pdf.set_font('Arial', 'B', 12)
                pdf.set_text_color(red)
                row.cell("Non-Compliant Entities")
                row.cell(str(result_dict["non_compliant_entity_count"]))
                pdf.set_text_color(black) 
        pdf.ln()

        # List of compliant entities
        pdf.set_font("Arial", size=12)
        with pdf.table(text_align="C", width=100, cell_fill_color=230, cell_fill_mode="ROWS") as table:
                row = table.row()
                row.cell("Compliant Entity Names")
                if len(result_dict['compliant_entities']) == 0:
                        row = table.row()
                        row.cell("N/A")   
                for compliant_entity in result_dict['compliant_entities']:
                        row = table.row()
                        row.cell(compliant_entity)
        pdf.ln()
        
        # List of non-compliant entities
        pdf.set_font("Arial", size=12)
        with pdf.table(text_align="C", width=100, cell_fill_color=230, cell_fill_mode="ROWS") as table:
                row = table.row()
                row.cell("Non-Compliant Entity Names")
                for non_compliant_entity in result_dict['non_compliant_entities']:
                        row = table.row()
                        row.cell(non_compliant_entity)
        pdf.ln()


def create_entity_summary(pdf, entity_name, entity):
        '''
        Create the entity summary page
        params: pdf - FPDF2 object
                entity_name - Name of the entity
                entity - Entity dict
        '''
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'Entity: {entity_name}', align='C')
        pdf.ln()

        # Add the summary for the entity
        pdf.set_font('Arial', 'B', 12)
        with pdf.table(first_row_as_headings=False, text_align="C", width=100, col_widths=(70, 30)) as table:
                row = table.row()
                row.cell("Checked Workspaces")
                row.cell(str(entity["checked_workspaces"]))
                row = table.row()
                pdf.set_text_color(green) 
                row.cell("Compliant Workspaces")
                row.cell(str(entity["compliant_workspaces"]))
                row = table.row()
                pdf.set_text_color(red) 
                row.cell("Non-Compliant Workspaces")
                row.cell(str(entity["non_compliant_workspaces"]))
                pdf.set_text_color(black) 
        pdf.ln()

        # Divide workspaces into compliant and non-compliant workspace name lists
        compliant_workspaces = []
        non_compliant_workspaces = []
        for workspace_name, workspace in entity['workspaces'].items():
                if workspace['is_compliant'] == True:
                        compliant_workspaces.append(workspace_name)
                if workspace['is_compliant'] == False:
                        non_compliant_workspaces.append(workspace_name)

        # List of compliant workspaces
        pdf.set_font("Arial", size=12)
        with pdf.table(text_align="C", cell_fill_color=230, cell_fill_mode="ROWS", width=140) as table:
                row = table.row()
                row.cell("Non-Compliant Workspaces")
                if len(non_compliant_workspaces) == 0:
                        row = table.row()
                        row.cell("N/A")
                for workspace_name in non_compliant_workspaces:
                        row = table.row()
                        row.cell(workspace_name)
        pdf.ln()
        
        # List of compliant workspaces
        pdf.set_font("Arial", size=12)
        with pdf.table(text_align="C", cell_fill_color=230, cell_fill_mode="ROWS", width=140) as table:
                row = table.row()
                row.cell("Compliant Workspaces")
                if len(compliant_workspaces) == 0:
                        row = table.row()
                        row.cell("N/A")
                for workspace_name in compliant_workspaces:
                        row = table.row()
                        row.cell(workspace_name)
        pdf.ln()

def create_workspace_title_page(pdf, workspace_name, workspace):
        '''
        Create the workspace title page
        params: pdf - FPDF2 object
                workspace_name - Name of the workspace
                workspace - Workspace dict
        '''
        # Workspace Title Page
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, f'Workspace: {workspace_name}', align='C')
        pdf.ln()
        # Add the summary for the entity
        pdf.set_font('Arial', 'B', 12)
        with pdf.table(first_row_as_headings=False, text_align="C", width=100, col_widths=(70, 30)) as table:
                row = table.row()
                row.cell("Performed Checks")
                row.cell(str(workspace["checks"]))
                row = table.row()
                pdf.set_text_color(green) 
                row.cell("Passed Checks")
                row.cell(str(workspace["compliant_check_count"]))
                row = table.row()
                pdf.set_text_color(red) 
                row.cell("Failed Checks")
                row.cell(str(workspace["non_compliant_check_count"]))
                pdf.set_text_color(black) 
        pdf.ln()

def create_checks_table(pdf, rules, passed):
        '''
        Create the checks table
        params: pdf - FPDF2 object
                rules - List of rules
                passed - Boolean indicating if the checks passed or failed
        '''
        pdf.set_font('Arial', 'B', 12)
        if passed == True:
                pdf.cell(0, 10, 'Passed Checks:')
        else:
                pdf.cell(0, 10, 'Failed Checks:')
        pdf.ln()
        pdf.set_font('Arial', size=8)

        for rule in rules:
                with pdf.table(text_align="L", width=150, col_widths=(30, 120)) as table:
                        row = table.row()
                        row.cell("Rule Name")
                        row.cell(str(rule["rule_name"]))
                        row = table.row()
                        row.cell("Rule Description")
                        row.cell(str(rule["description"]))
                        row = table.row()
                        row.cell("Resource Type")
                        row.cell(str(rule["resource_type"]))
                        row = table.row()
                        row.cell("Resource ID")
                        row.cell(str(rule["resource_id"]))
                        row = table.row()
                        row.cell("Provider")
                        row.cell(str(rule["provider"]))
                        row = table.row()
                        row.cell("Level")
                        if rule["compliance_level"] == 'check':
                                pdf.set_text_color(green) 
                                row.cell("Check")
                        elif rule["compliance_level"] == 'soft_mandatory':
                                pdf.set_text_color(yellow) 
                                row.cell("Soft Mandatory")
                        elif rule["compliance_level"] == 'hard_mandatory':
                                pdf.set_text_color(red)
                                row.cell("Hard Mandatory")
                        else:
                                row.cell("Unknown")
                        pdf.set_text_color(black) 
                pdf.ln()

def create_report(result_dict):
        '''
        Create the report
        params: result_dict - Dictionary containing the results of the checks
        '''
        # Create the PDF object using the FPDF library
        pdf = FPDF()
        
        # Title Page
        create_title_page(pdf, result_dict)

        ### ENTITIES ###
        for entity_name, entity in result_dict['entities'].items():
                # Create entity summary page
                create_entity_summary(pdf, entity_name, entity)
                
                ### WORKSPACES ####
                for workspace_name, workspace in entity['workspaces'].items():
                        # Create workspace summary page
                        create_workspace_title_page(pdf, workspace_name, workspace)
                        # List failed checks
                        create_checks_table(pdf, workspace['failed_checks'], False)
                        # List passed checks
                        create_checks_table(pdf, workspace['compliant_checks'], True)
                        
        # Save the PDF to a file
        # file = f'/tmp/report_{result_dict["timestamp"]}.pdf'
        file = f'{result_dict["timestamp"]}.pdf'
        pdf.output(file, 'F')
        return file


def lambda_handler(event, context):
        '''
        Lambda handler
        params: event - Event that triggered the lambda
                context - Lambda context
        '''
        ## Check the origin of this call
        # If the call is from a stepfunction success event, get the timestamp for the json files
        if event.get('detail-type') == 'Step Functions Execution Status Change':
                timestamp = get_s3_keys_from_event(event)
        # If the call is made manually get the json files by timestamp
        elif "timestamp" in event:
                timestamp = event['timestamp']
        else:
                # Raise an exception if the event is not from a stepfunction success event
                raise Exception(f'Invalid event: {event}')
        
        # Get the S3 keys by timestamp
        s3_keys = get_s3_keys_by_timestamp(timestamp)

        # Download the JSON files from S3 and combine into a dict
        result_dict = results_to_dict(s3_keys, timestamp)

        # Create the report
        file = create_report(result_dict)
        # Upload the report to S3
        # upload_report_to_s3(file, timestamp)

        return result_dict


#################
#### Testing ####
#################

test_event = {
  "timestamp": "2023-06-19-15-22-50"
}


print(json.dumps(lambda_handler(test_event, None)))