"""
combined_testing.py
Combined testing script for Web interface, REST API and Database.

Usage:
    python combined_testing.py <db_user> <db_password>
"""
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import db_connector
import time

# Read DB username/password from the command line (Part 2, Extra 3)
db_connector.init_from_argv()

# Get config from DB (Extra 4)
config = db_connector.get_config()
api_url = config['api_url']
browser_type = config['browser']
test_user = config['test_user_name']
test_id = 102

try:
    # 1. Post new user data to REST API
    post_res = requests.post(f"{api_url}/{test_id}", json={"user_name": test_user})
    if post_res.status_code != 200:
        raise Exception("POST failed")
    print("1. API POST successful")

    # 2. Submit GET request to make sure data equals posted data
    get_res = requests.get(f"{api_url}/{test_id}")
    if get_res.status_code != 200 or get_res.json().get('user_name') != test_user:
        raise Exception("GET failed or data mismatch")
    print("2. API GET successful")

    # 3. Check posted data was stored inside DB
    db_user = db_connector.get_user(test_id)
    if db_user != test_user:
        raise Exception("Database check failed")
    print("3. Database verified")

    # 4. Start Selenium Webdriver session
    if browser_type.lower() == 'chrome':
        options = Options()
        options.add_argument('--headless') # Run invisibly
        options.add_argument('--no-sandbox')  # Needed when run by Jenkins
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
    elif browser_type.lower() == 'firefox':
        driver = webdriver.Firefox()
    else:
        raise Exception(f"Unsupported browser: {browser_type}")

    # 5. Navigate to web interface URL
    driver.get(f"http://127.0.0.1:5001/users/get_user_data/{test_id}")
    time.sleep(1)

    # 6. Check that the user name is correct
    user_element = driver.find_element(By.ID, 'user')
    if user_element.text != test_user:
        raise Exception("Web interface user name mismatch")
        
    print("4. Web Interface verified")
    print("\n✅ All combined tests passed successfully!")

except Exception as e:
    print(f"Exception details: {e}")
    raise Exception("test failed")
finally:
    if 'driver' in locals():
        driver.quit()
    db_connector.delete_user(test_id)
