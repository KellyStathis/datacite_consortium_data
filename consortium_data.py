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

def main():
    load_dotenv()
    consortium_id = os.getenv('CONSORTIUM_ID')
    consortium_pass = os.getenv('CONSORTIUM_PASS')
    test_instance = os.getenv('TEST_INSTANCE')
    authorization = "Basic " + str(base64.encodebytes(bytes(consortium_id + ":" + consortium_pass, 'utf8')))[2:-3]

    # Set base url (prod or test)
    if test_instance and test_instance.lower() == "true":
        instance_type = "Test"
        base_url = "https://api.test.datacite.org/"
    else:
        instance_type = "Production"
        base_url = "https://api.datacite.org/"

    # Headers for all API requests
    headers = {
        'accept': "application/vnd.api+json",
        'authorization': authorization
        }

    # Get data for consortium
    url_providers_consortium = base_url + "providers/" + consortium_id.lower()
    r = requests.request("GET", url_providers_consortium, headers=headers)
    consortium_json = r.json()

    # Grab the list of consortium orgs from the consortium data
    consortium_orgs_list = consortium_json['data']['relationships']['consortiumOrganizations']['data']

    # List for all accounts, including both consortium organizations and repositories
    accounts_data = []

    # Get data for each consortium organization and its repositories
    for consortium_org in consortium_orgs_list:
        consortium_org_id = consortium_org['id']
        url_providers_consortium_org = base_url + "providers/" + consortium_org_id
        r = requests.request("GET", url_providers_consortium_org, headers=headers)
        consortium_org_json = r.json()
        try:
            if "data" in consortium_org_json:
                consortium_org_data = consortium_org_json['data']
                # Get each repository's data
                for repo in consortium_org_data['relationships']['clients']['data']:
                    repo_id = repo['id']
                    url_clients_repo = base_url + "clients/" + repo_id
                    r = requests.request("GET", url_clients_repo, headers=headers)
                    repo_json = r.json()
                    try:
                        repo_data = repo_json['data']
                        accounts_data.append(collapse_lists(repo_data))
                        print("Saved data for repository: {} ({})".format(repo_id, consortium_org_id))
                    except Exception as e:
                        print("Error fetching data for repository {}.{}: {}".format(consortium_org_id, repo_id, e))
                accounts_data.append(collapse_lists(consortium_org_data))
                print("Saved data for consortium: {}".format(consortium_org_id))
            else:
                print("Error fetching data for consortium organization {}: {}".format(consortium_org_id, consortium_org_json["errors"][0]["status"]))
        except Exception as e:
            print("Error fetching data for consortium organization {}: {}".format(consortium_org_id, e))

    # Write list of all accounts to JSON file
    accounts_data_json = json.dumps(accounts_data)
    output_filename = datetime.today().strftime('%Y-%m-%d') + "_" + consortium_id + "_" + instance_type + "_Accounts.json"
    print("Writing data to file: {}".format(output_filename))
    f = open(output_filename, "w")
    f.write(accounts_data_json)

if __name__ == "__main__":
    main()