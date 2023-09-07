import requests
import os
import threading
import datetime
import time


def request_with_rate_limit_handling():
    global wait_time_seconds

    url = "https://api.github.com/graphql"

    """
    query {
        rateLimit {
            limit
            cost
            remaining
            resetAt
        }
    }
    """
    query = "{\"query\":\"query{\\n\\trateLimit{\\n\\t\\tlimit\\n\\t\\tcost\\n\\t\\tremaining\\n\\t\\tresetAt\\n\\t}\\n}\"}"

    api_key = os.getenv('GITHUB_API_KEY')
    if api_key is None:
        raise Exception("Couldn't find the GitHub API key. Please set it as an environment variable.")

    headers = {
        "Authorization": "bearer " + api_key,
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, data=query, headers=headers)
    json_data = response.json()

    reset_at_str = json_data["data"]["rateLimit"]["resetAt"]
    reset_at = datetime.datetime.strptime(reset_at_str, "%Y-%m-%dT%H:%M:%SZ")
    wait_time_seconds = (reset_at - datetime.datetime.utcnow()).total_seconds()

    interrupt_event = threading.Event()
    # キー入力監視のスレッドを作成
    t1 = threading.Thread(target=key_capture_thread, args=(interrupt_event,))
    t1.daemon = True
    t1.start()

    start_time = time.time()
    while time.time() - start_time < wait_time_seconds:
        if interrupt_event.is_set():
            print("\rInterrupted by user")
            break
        remaining_time = wait_time_seconds - (time.time() - start_time)
        minutes, seconds = divmod(remaining_time, 60)
        print(f"\rWaiting for {int(minutes)} minutes and {int(seconds)} seconds...", end="")
        time.sleep(1)

    time.sleep(5)
    return

def key_capture_thread(event):
    print("Press Enter to interrupt waiting:", end="", flush=True)
    print()
    input()
    event.set()