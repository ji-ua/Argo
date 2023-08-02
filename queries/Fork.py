import requests
from datetime import datetime
import datetime
import csv
import sys
import os
import glob
import time
import json

import FileMake
import Download_per


# Create payload for retrieving Star data
def make_payload(owner, repository):
    payload_1 = (
        "{\"query\":\"query forks {\\n  repository(owner: \\\""
        + owner
        + "\\\", name: \\\""
        + repository
        + "\\\") {\\n    forks(first: 100"
    )
    return payload_1


# Request data from GitHub GraphQL API
def request(repository, dir_path, payload_1, end_cursor, has_next_page, file_num):
    print()
    sys.setrecursionlimit(10 ** 9)  ## Change recursion limit (10^9)
    data_cpl = False
    url = "https://api.github.com/graphql"
    payload_2 = (
        ") {\\n\\t\\t\\ttotalCount\\n\\t\\t\\tnodes {\\n\\t\\t\\t\\tnameWithOwner\\n\\t\\t\\t\\turl\\n\\t\\t\\t\\tcreatedAt\\n\\t\\t\\t\\tdefaultBranchRef {\\n\\t\\t\\t\\t\\ttarget {\\n\\t\\t\\t\\t\\t\\t... on Commit {\\n\\t\\t\\t\\t\\t\\t\\tcommittedDate\\n\\t\\t\\t\\t\\t\\t}\\n\\t\\t\\t\\t\\t}\\n\\t\\t\\t\\t}\\n\\t\\t\\t}\\n\\t\\t\\tpageInfo{\\n\\t\\t\\t\\tendCursor\\n\\t\\t\\t\\thasNextPage\\n\\t\\t\\t}\\n\\t\\t}\\n\\t}\\n}\",\"operationName\":\"forks\"}"
    )
    if has_next_page == 1:
        if end_cursor != None:
            payload = (
                payload_1
                + ",after:"
                + "\\\""
                + end_cursor
                + "\\\""
                + payload_2
            )
        else:
            payload = payload_1 + payload_2
            data_cpl = True
        
        api_key = os.getenv('GITHUB_API_KEY')
        if api_key is None:
            raise Exception("Couldn't find the GitHub API key. Please set it as an environment variable.")

        headers = {
            "Authorization": "bearer " + api_key,
            "Content-Type": "application/json",
        }

        retry_limit = 5
        retry_count = 0

        while retry_count < retry_limit:
            response = requests.request("POST", url, data=payload, headers=headers)
            json_data = response.json()
            
            if 'errors' in json_data and isinstance(json_data['errors'], list) and 'type' in json_data['errors'][0] and json_data['errors'][0]['type'] == 'RATE_LIMITED':
                print()
                print(json_data["errors"][0]["message"])
                print("To retry, wait at least one hour.")
                exit(1) # プログラムを終了させる

            if json_data is None:
                print()
                print(f"json_data:{json_data}")
                retry_count += 1
                print()
                continue

            if 'data' in json_data and 'repository' in json_data["data"] and json_data["data"]["repository"] is None:
                print()
                print(json_data["errors"][0]["message"])
                print()
                exit(1)

            data = find(json_data, str(file_num), dir_path, data_cpl)
            if data is not None:
                file_nextnum = data[0]
                Download_per.download_per(data[3], int(file_nextnum))
                export(file_nextnum, dir_path)  # Convert to CSV file
                break
            else:
                retry_count += 1
                print("data is None!")
                print(f"retrying request ... ({retry_count}/{retry_limit})")
                print()
        else:
            print(f"Error occerred {retry_limit} times. Stobp retrying.")
            print()
            exit(1)
                

        return request(repository, dir_path, payload_1, data[1], data[2], file_num)
    else:
        return


# Check if existing files exist
def find(json_data, file_name, dir_path, data_cpl):
    list_of_files = glob.glob(os.path.join(dir_path, "json", "*.json"))  # Get the list of files from the specified folder

    if len(list_of_files) == 0:  # When referring for the first time (no json files in the folder)
        FileMake.jsonMake(json_data, file_name, dir_path)
        print("First Survey")
        f = open(os.path.join(dir_path, "json", file_name + ".json"), "r")
        file_nextnum = 2

    else:  # Refer to the latest file from the cached directory
        file_intlist = []
        for file in list_of_files:  # Get only the file name without the extension from the absolute path
            filename, fileext = os.path.splitext(os.path.basename(file))
            file_intlist.append(filename)
        file_int = [int(s) for s in file_intlist]
        file_nextnum = str(max(file_int) + 1)
        FileMake.jsonMake(json_data, file_nextnum, dir_path)
        f = open(os.path.join(dir_path, "json", file_nextnum + ".json"), "r")
    json_dict = json.load(f)

    try:
        # エラーが起きうる可能性のあるコード
        totalCount = json_dict["data"]["repository"]["forks"]["totalCount"]
        end_cursor = json_dict["data"]["repository"]["forks"]["pageInfo"]["endCursor"]
        has_next_page = json_dict["data"]["repository"]["forks"]["pageInfo"]["hasNextPage"]
    except TypeError:
        removeLastTwoJson(dir_path)
        print(f"TypeError occurred at find().")
        print(f"json_dict:{json_dict}")
        print()
        return None
    except KeyError:
        removeLastTwoJson(dir_path)
        print(f"KeyError occurred at find().")
        print()                        
        return None

    return file_nextnum, end_cursor, has_next_page, totalCount


# Convert to CSV file
def export(file_name, dir_path):
    file_json = int(file_name) - 1
    json_filename = str(file_json) + ".json"
    csv_filename = str(file_json) + ".csv"
    f = open(os.path.join(dir_path, "json", json_filename), "r")
    data = json.load(f)

    # Set nodes Dictionary
    nodes = []
    temp_n = []
    for node in data["data"]["repository"]["forks"]["nodes"]:
        nameWithOwner = node["nameWithOwner"]
        url = node["url"]
        createdAt = node["createdAt"]

        created_utc = createdAt.replace("Z", "")
        d = datetime.datetime.fromisoformat(created_utc)
        createdt = d.strftime("%Y-%m/%d %H:%M:%S")

        if node["defaultBranchRef"] != None:
            committedDate = node["defaultBranchRef"]["target"]["committedDate"]

            committed_utc = committedDate.replace("Z", "")
            d = datetime.datetime.fromisoformat(committed_utc)
            committedt = d.strftime("%Y-%m/%d %H:%M:%S")

            commitCountAfterFork = countCommit(nameWithOwner, createdAt, dir_path)
        else:
            print()
            print("TypeError occured at export().")
            print("defaultBranchRef is None.")
            print(f"\"{nameWithOwner}\" is probably empty.")
            print(f"Check {url}")
            print()
            committedDate = ""
            committedt = ""
            commitCountAfterFork = -1

        node["commitCountAfterFork"] = commitCountAfterFork
            
        temp_n = [nameWithOwner, url, createdt, committedt, commitCountAfterFork]
        nodes.append(temp_n)

    # Write CSV
    with open(os.path.join(dir_path, "csv", csv_filename), "w", newline="") as csvFile:
        csvwriter = csv.writer(
            csvFile, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONNUMERIC
        )
        csvwriter.writerow(["nameWithOwner", "url", "createdAt", "committedDate", "commitCountAfterFork"])
        for value in nodes:
            csvwriter.writerow(value)

# Get the number of commits after "fork" was created.
def countCommit(nameWithOwner, createdAt, dir_path):
    url = "https://api.github.com/graphql"
    onwer_repository = FileMake.input(nameWithOwner)

    payload = ("{\"query\":\"query commit{\\n\\trepository(owner:\\\""
               + onwer_repository[0]
               + "\\\", name:\\\""
               + onwer_repository[1]
               + "\\\") {\\n\\t\\tdefaultBranchRef {\\n\\t\\t\\ttarget {\\n\\t\\t\\t\\t... on Commit {\\n\\t\\t\\t\\t\\thistory(since: \\\""
               + createdAt
               + "\\\"){\\n\\t\\t\\t\\t\\t\\ttotalCount\\n\\t\\t\\t\\t\\t}\\n\\t\\t\\t\\t}\\n\\t\\t\\t}\\n\\t\\t}\\n\\t}\\n}\",\"operationName\":\"commit\"}")

    api_key = os.getenv('GITHUB_API_KEY')
    if api_key is None:
        raise Exception("Couldn't find the GitHub API key. Please set it as an environment variable.")
    headers = {
        "Authorization": "bearer " + api_key,
        "Content-Type": "application/json",
    }
    
    retry_limit = 5
    retry_count = 0
    
    while retry_count < retry_limit:
        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            json_data = response.json()

            if 'errors' in json_data and isinstance(json_data['errors'], list) and 'type' in json_data['errors'][0] and json_data['errors'][0]['type'] == 'RATE_LIMITED':
                removeLastTwoJson(dir_path)
                print()
                print(json_data["errors"][0]["message"])
                print("To retry, wait at least one hour.")
                exit(1) # プログラムを終了させる

            if 'data' in json_data and json_data["data"]["repository"] == None:
                print()
                print(json_data["errors"][0]["message"])
                print()
                return -1
            
            totalCount = json_data["data"]["repository"]["defaultBranchRef"]["target"]["history"]["totalCount"]
            break
        except TypeError:
            retry_count += 1
            print(f"TypeError occurred at countCommit(), retrying... ({retry_count}/{retry_limit})")
            print(f"json_data:{json_data}")
        except KeyError:
            retry_count += 1
            print(f"KeyError occurred at countCommit(), retrying... ({retry_count}/{retry_limit})")
            print(f"json_data:{json_data}")
    else:
        print()
        print(f"Error occerred {retry_limit} times. Stobp retrying.")
        print(f"json_data:{json_data}")
        print()
        return -1

    return totalCount

def removeLastTwoJson(dir_path):
    list_of_files = glob.glob(os.path.join(dir_path, "json", "*.json"))  # Get the list of files from the specified folder

    if len(list_of_files) == 0:
        file_nextnum = 2
    else:  
        file_intlist = []
        for file in list_of_files:
            filename, fileext = os.path.splitext(os.path.basename(file))
            file_intlist.append(filename)
        file_int = [int(s) for s in file_intlist]
        file_nextnum = str(max(file_int) + 1)

    json_file_path = os.path.join(dir_path, "json", str(int(file_nextnum) - 1) + ".json")
    json_file_path_next =os.path.join(dir_path, "json", str(file_nextnum) + ".json")

    if os.path.isfile(json_file_path):
        os.remove(json_file_path)
    if os.path.isfile(json_file_path_next):
        os.remove(json_file_path_next)

    print(f"Deleteted \"{json_file_path}\".")
    print(f"Deleteted \"{json_file_path_next}\".")

    return

def main(repository, make_path, dir_stored):
    start_time = time.perf_counter()

    for i in range(len(repository)):
        # Make File, Payload
        print("Download repository: " + repository[i])
        repo_data = FileMake.input(repository[i])  # owner, repository
        if make_path:
            dir_path = FileMake.makedir(repo_data[0], repo_data[1], "Fork")
        else:
            dir_path = FileMake.newmakedir(make_path)
        payload = make_payload(repo_data[0], repo_data[1])

        # Get json_data
        json_data = FileMake.findCursor(dir_path, "forks")  # endCursor, hasNextPage, file_num
        request(
            repo_data[1], dir_path, payload, json_data[0], json_data[1], json_data[2]
        )  # Retrieve stargazers

        # Export csv_data
        file_num = FileMake.csvPrep(dir_path)
        export(file_num + 1, dir_path)  # Convert to CSV file
        FileMake.merge(dir_path)

        # Delete cache
        if dir_stored:
            FileMake.deletedir(dir_path)

    end_time = time.perf_counter()
    print("Data acquisition completed! Duration: " + str(end_time - start_time) + "s")


if __name__ == "__main__":
    repositories = sys.argv  # owner/repository are stored from repository[1] onwards
    repositories.pop(0)  # Remove repositories[0] (~.py)
    dir_path = True
    dir_stored = False
    main(repositories, dir_path, dir_stored)
