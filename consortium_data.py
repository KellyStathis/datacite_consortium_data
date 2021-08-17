import requests
import json
import base64
import os
from dotenv import load_dotenv
from datetime import datetime

def collapse_lists(dict_to_collapse):
    # If there are any lists in the dict_to_collapse, turn them into semicolon-delimited strings
    for key in list(dict_to_collapse.keys()):
        if isinstance(dict_to_collapse[key], dict):
            # Iterate recursively through all dicts within the dict
           dict_to_collapse[key] = collapse_lists(dict_to_collapse[key])
        elif isinstance(dict_to_collapse[key], list):
            # If the list has entries that are also dicts, get the 'id' elements and concat
            if len(dict_to_collapse[key]) and isinstance(dict_to_collapse[key][0], dict):
                new_string = ""
                for x in dict_to_collapse[key]:
                    if 'id' in x:
                        new_string = new_string + "; " + x['id']
                dict_to_collapse[key] = new_string[2:]
            # If the list doesn't have entries that are also dicts, just concat the elements
            else:
                dict_to_collapse[key] = '; '.join([str(x) for x in dict_to_collapse[key]])
    return dict_to_collapse

def get_datacite_api_response(authorization, base_url, url_extension, querystring=""):
    # Headers for all API requests
    headers = {
        "accept": "application/vnd.api+json",
        "authorization": authorization
    }
    url = base_url + url_extension
    response = requests.request("GET", url, headers=headers, params=querystring)
    return response.json()

def getEmails(email_list, account_data):
    if "attributes" in account_data:
        for emailType in ["contactEmail", "systemEmail", "groupEmail"]:
            if emailType in account_data["attributes"] and account_data["attributes"][emailType]:
                email = account_data["attributes"][emailType].lower()
                if email not in email_list:
                    email_list.append(email)
        for contactType in ["technicalContact", "secondaryTechnicalContact", "billingContact",
                            "secondaryBillingContact", "serviceContact", "secondaryServiceContact", "votingContact"]:
            if contactType in account_data["attributes"] and "email" in account_data["attributes"][contactType] and account_data["attributes"][contactType]["email"]:
                email = account_data["attributes"][contactType]["email"].lower()
                if email not in email_list:
                    email_list.append(email)
    return email_list

def main():
    load_dotenv()
    consortium_id = os.getenv('CONSORTIUM_ID')
    consortium_pass = os.getenv('CONSORTIUM_PASS')
    test_instance = os.getenv('TEST_INSTANCE')
    userpass = consortium_id + ":" + consortium_pass
    authorization = "Basic {}".format(base64.b64encode(userpass.encode()).decode())

    # Set base url (prod or test)
    if test_instance and test_instance.lower() == "true":
        instance_type = "Test"
        base_url = "https://api.test.datacite.org/"
    else:
        instance_type = "Production"
        base_url = "https://api.datacite.org/"

    # Get data for consortium
    consortium_json = get_datacite_api_response(authorization, base_url, "providers/" + consortium_id.lower())

    # Grab the list of consortium orgs from the consortium data
    consortium_orgs_list = consortium_json['data']['relationships']['consortiumOrganizations']['data']

    # List for all accounts, including both consortium organizations and repositories
    accounts_data = []
    # Email list without duplicates
    email_list = []

    # Get data for each consortium organization and its repositories
    for consortium_org in consortium_orgs_list:
        consortium_org_id = consortium_org['id']
        consortium_org_json = get_datacite_api_response(authorization, base_url, "providers/" + consortium_org_id)
        try:
            if "data" in consortium_org_json:
                consortium_org_data = consortium_org_json['data']
                # Get each repository's data
                for repo in consortium_org_data['relationships']['clients']['data']:
                    repo_id = repo['id']
                    repo_json = get_datacite_api_response(authorization, base_url, "clients/" + repo_id)
                    try:
                        repo_data = repo_json['data']
                        accounts_data.append(collapse_lists(repo_data))
                        email_list = getEmails(email_list, repo_data)
                        print("Saved data for repository: {} ({})".format(repo_id, consortium_org_id))
                    except Exception as e:
                        print("Error fetching data for repository {}.{}: {}".format(consortium_org_id, repo_id, e))
                accounts_data.append(collapse_lists(consortium_org_data))
                email_list = getEmails(email_list, consortium_org_data)
                print("Saved data for consortium organization: {}".format(consortium_org_id))
            else:
                print("Error fetching data for consortium organization {}: {}".format(consortium_org_id, consortium_org_json["errors"][0]["status"]))
        except Exception as e:
            print("Error fetching data for consortium organization {}: {}".format(consortium_org_id, e))

    # Write list of all accounts to JSON file
    accounts_data_json = json.dumps(accounts_data)
    output_filename = datetime.today().strftime('%Y%m%d') + "_" + consortium_id.upper() + "_" + instance_type + "_Accounts.json"
    print("Writing data to file: {}".format(output_filename))
    f = open(output_filename, "w")
    f.write(accounts_data_json)

    # Write email addressess to text file
    output_filename = datetime.today().strftime('%Y%m%d') + "_" + consortium_id.upper() + "_" + instance_type + "_Emails.txt"
    print("Writing data to file: {}".format(output_filename))
    with open(output_filename, 'w') as f:
        for email in sorted(email_list):
            f.write("%s\n" % email)


if __name__ == "__main__":
    main()
