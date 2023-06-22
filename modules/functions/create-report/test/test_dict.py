import json


d1 = {
    "AGO-0001": {
        "compliant": 1,
        "non_compliant": 2,
        "checked": 3,
        "workspaces": {
            "workspace1-1": {
                "checks": 4,
                "failed_checks": 2,
                "rules": [
                    {"rule1": [{"name":"regel_name_1", "compliance_status":True}, {"name":"regel_name_2", "compliance_status":True}]}
                ]
            },
            "workspace1-2": {
                "checks": 4,
                "failed_checks": 2,
                "rules": [
                    {"rule1": [{"name":"regel_name_1", "compliance_status":True}, {"name":"regel_name_2", "compliance_status":True}]}
                ]
            }
        }
    },
    "AGO-0002": {
        "compliant": 1,
        "non_compliant": 2,
        "checked": 3,
        "workspaces": {
            "workspace2-1": {
                "checks": 4,
                "failed_checks": 2,
                "rules": [
                    {"rule1": [{"name":"regel_name_1", "compliance_status":True}, {"name":"regel_name_2", "compliance_status":True}]}
                ]
            },
            "workspace2-2": {
                "checks": 4,
                "failed_checks": 2,
                "rules": [
                    {"rule1": [{"name":"regel_name_1", "compliance_status":True}, {"name":"regel_name_2", "compliance_status":True}]}
                ]
            }
        }
    }
}

# for d in d1:
#     for ws in d1[d]['workspaces']:
#         print(d1[d]['workspaces'][ws])


l1 = [1,2,3,4,5,6,7,8,9,10]
sum_dict = {}

for i in l1:
    sum_dict[f'foo-{i}'] = 0

sum_dict['foo-11']['test'] = {}
print(sum_dict)