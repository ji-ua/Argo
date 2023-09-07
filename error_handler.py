import os
import re
import shutil

import FileMake
import retry_logic

def validate_json(json_data):
    # valid data at Fork.request()
    if 'data' in json_data and json_data["data"] is not None and \
       'repository' in json_data["data"] and json_data["data"]["repository"] is not None and \
       'forks' in json_data["data"]["repository"] and json_data["data"]["repository"]["forks"] is not None and \
       'totalCount' in json_data["data"]["repository"]["forks"] and json_data["data"]["repository"]["forks"]["totalCount"] is not None and \
       'nodes' in json_data["data"]["repository"]["forks"] and json_data["data"]["repository"]["forks"]["nodes"] is not None:
        return True
    
    # valid data at Fork.countCommit()
    elif 'data' in json_data and json_data["data"] is not None and \
       'repository' in json_data["data"] and json_data["data"]["repository"] is not None and \
       'defaultBranchRef' in json_data["data"]["repository"] and json_data["data"]["repository"]["defaultBranchRef"] is not None and \
       'target' in json_data["data"]["repository"]["defaultBranchRef"] and  json_data["data"]["repository"]["defaultBranchRef"]["target"] is not None and \
       'history' in json_data["data"]["repository"]["defaultBranchRef"]["target"] and  json_data["data"]["repository"]["defaultBranchRef"]["target"]["history"] is not None and \
       'totalCount' in json_data["data"]["repository"]["defaultBranchRef"]["target"]["history"] and  json_data["data"]["repository"]["defaultBranchRef"]["target"]["history"]["totalCount"] is not None:
        return True
    
    # RATE_LIMITED
    elif 'errors' in json_data and isinstance(json_data['errors'], list) and \
         'type' in json_data['errors'][0] and json_data['errors'][0]['type'] == 'RATE_LIMITED':
        print()
        print(json_data["errors"][0]["message"])
        print()
        retry_logic.request_with_rate_limit_handling()
        print()
        return False

    # invalid
    # The repository does not exist.
    elif 'data' in json_data and json_data["data"] is not None and \
         'repository' in json_data["data"] and json_data["data"]["repository"] is None:
        print()
        message = json_data["errors"][0]["message"]
        print(message)
        matches = re.findall(r"'(.*?)'", message)

        for match in matches:
            nameWithOwner = match
        
        if os.path.isdir("cache/" + nameWithOwner):
            owner, repository = FileMake.input(nameWithOwner)
            shutil.rmtree("cache/" + nameWithOwner)
            print(f"Deleteted cache/{nameWithOwner}")
            if not os.listdir("cache/" + owner):
                os.rmdir("cache/" + owner)
                print(f"Deleteted cache/{owner}")
            exit(1)
        print()
        return False

    # invalid
    # other
    else:
        print("json_data is invalid.")
        print(f"json_data:{json_data}")
        print()
        return False