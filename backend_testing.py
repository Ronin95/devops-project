"""
backend_testing.py
Tests the REST API and Database by POSTing a new user, checking it via GET,
and verifying it directly in the database.

Usage:
    python backend_testing.py <db_user> <db_password>
"""
import requests
import db_connector

# Read DB username/password from the command line (Part 2, Extra 3)
db_connector.init_from_argv()

# Get config from DB (Extra 4)
config = db_connector.get_config()
api_url = config['api_url']
test_user = config['test_user_name']
test_id = 100  # Arbitrary ID for testing

print(f"Testing with API URL: {api_url} and User Name: {test_user}")

try:
    # 1. Post a new user data to the REST API
    post_res = requests.post(f"{api_url}/{test_id}", json={"user_name": test_user})
    if post_res.status_code != 200:
        raise Exception(f"POST request failed. Status: {post_res.status_code}")
    print("1. POST successful.")

    # 2. Submit a GET request to make sure status code is 200 and data equals posted data
    get_res = requests.get(f"{api_url}/{test_id}")
    if get_res.status_code != 200 or get_res.json().get('user_name') != test_user:
        raise Exception(f"GET request failed or data mismatch.")
    print("2. GET successful. Data matches.")

    # 3. Check posted data was stored inside DB
    db_user = db_connector.get_user(test_id)
    if db_user != test_user:
        raise Exception(f"Database check failed. Expected {test_user}, got {db_user}")
    print("3. Database check successful.")
    
except Exception as e:
    # The requirement specifically says to throw this exception on failure
    raise Exception("test failed") from e
finally:
    # Cleanup after test
    db_connector.delete_user(test_id)
