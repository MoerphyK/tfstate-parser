import json
import re
import operator
import logging

logging.basicConfig(filename='tfstate-compliance-checker.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger('tfstate-compliance-checker')

##########################
### Compliance Checker ###
##########################

class ComplianceChecker:
    '''
    This class is used to check the compliance of a Terraform state file against a compliance file.
    '''

    def __init__(self) -> None:
        '''
        Constructor for the ComplianceChecker class.
        '''
        pass

    ############################
    #### Compliance Checker ####
    ############################

    def check_compliance(self, rule, state_resources):
            '''
            Checks if a Terraform state file is compliant with a compliance file.
            param state_resources: The pre sorted resources from the Terraform state.
            param rule: The rule.
            Returns: A dictionary containing the compliance result.
            '''
            logger.info(f'Rule: {rule}\n\nState Resources: {state_resources}')
            results = []
            provider = rule['Provider']
            resource_type = rule['ResourceType']
            condition = json.loads(rule['Rule'])
            resources = state_resources[provider][resource_type]

            for resource in resources:
                    ## Check if there are multiple instances of the resource, in case of count or for_each
                    for instance in resource['instances']:
                            attributes = instance['attributes']
                            is_compliant, errors = self.check_condition(attributes, condition)

                            result = {
                                    'rule_name': rule['RuleName'],
                                    'description': rule['Description'],
                                    'compliance_level': rule['ComplianceLevel'],
                                    'provider': provider,
                                    'resource_type': resource_type,
                                    'resource_id': attributes.get('id', 'no id found'),
                                    'compliance_status': is_compliant,
                                    'errors': errors
                            }
                    results.append(result)
            return results

    def check_condition(self, attributes, condition):
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
                    operator_fn = self.get_operator_function(value)
                    logger.info(f'check_condition - operator: {value}')
                elif key == 'rules':
                    rules = value

            if operator_fn is None:
                return False, 'Invalid condition operator'

            rule_results = []
            errors = []
            for rule in rules:
                result, error = self.check_rule(rule,attributes)
                rule_results.append(result)
                errors.append(error)

            logger.info(f'check_condition - results: {rule_results}')
            return operator_fn(rule_results), errors

    def check_rule(self, rule, attributes):
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
            
            # Check rule inputs validity
            if not key or not operator_str:
                return False, 'Invalid rule'

            # Get operator
            operator_fn = self.get_operator_function(operator_str)
            logger.info(f'check_rule - operator: {operator_str}')


            actual_value = self.get_attribute_value(attributes, key)

            if operator_fn is None:
                return False, f'Invalid operator: {operator_str}'
            elif actual_value == None and operator_str == 'contains':
                return False, "Key can't be found in resource attributes."
            elif actual_value == None and operator_str == 'not_contains':
                return True, "Value can't be found in resource attributes."

            return operator_fn(actual_value, value),''
            
    ##########################
    #### Helper Functions ####
    ##########################

    def slim_providers(self, full_provider):
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

    def rearrange_tfstate(self, tfstate):
        '''
        Rearrange the tfstate to be grouped by provider and resource type
        params: tfstate - tfstate as dictionary to rearrange
        returns: rearranged tfstate
        '''
        rearranged_dict = {}
        slimmed_rearranged_dict = {}

        for item in tfstate['resources']:
            provider = item["provider"]
            resource_type = item["type"]

            if provider not in rearranged_dict:
                rearranged_dict[provider] = {}

            if resource_type not in rearranged_dict[provider]:
                rearranged_dict[provider][resource_type] = []

            rearranged_dict[provider][resource_type].append(item)

        for provider in rearranged_dict:
            slimmed_rearranged_dict[self.slim_providers(provider)] = rearranged_dict[provider]
        return slimmed_rearranged_dict

    def get_operator_function(self, operator_str):
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
                'nand': lambda iterable: not all(iterable), ## Works with list of bools
                'or': any, ## Works with list of bools
                'nor': lambda iterable: not any(iterable) ## Works with list of bools
            }
            return operator_map.get(operator_str)

    def get_attribute_value(self, attributes, key):
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