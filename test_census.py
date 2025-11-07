import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("CENSUS_API_KEY")

print(f"API Key loaded: {api_key[:20]}..." if api_key else "No API key found")
print()

# Test the exact request the app is making
url = "https://api.census.gov/data/2022/acs/acs5"
params = {
    "get": "B19013_001E,NAME",
    "for": "county:051",
    "in": "state:13",
    "key": api_key
}

print(f"Request URL: {url}")
print(f"Parameters: {params}")
print()

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print()
    print(f"Response Text: {response.text}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print(f"Parsed JSON:")
        for row in data:
            print(f"  {row}")
        print()
        print(f"Headers: {data[0]}")
        print(f"Values: {data[1]}")
        print(f"Median Household Income: ${data[1][0]}")
    else:
        print(f"Error response: {response.text}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

