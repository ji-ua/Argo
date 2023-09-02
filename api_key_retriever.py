import os

def get_api_key():
    api_key = os.getenv('GITHUB_API_KEY')
    if api_key is None:
        api_key = os.environ.get("API_KEY")

    return api_key