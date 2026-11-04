"""
frontend_testing.py
Tests the web interface using Selenium WebDriver.

Usage:
    python frontend_testing.py <db_user> <db_password>
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import db_connector
import time

# Read DB username/password from the command line (Part 2, Extra 3)
db_connector.init_from_argv()

# Get config from DB (Extra 4)
config = db_connector.get_config()
browser_type = config['browser']
test_user = config['test_user_name']
test_id = 101

# Setup test user directly in DB
db_connector.insert_user(test_id, test_user)

try:
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

    # Navigate to web interface URL
    driver.get(f"http://127.0.0.1:5001/users/get_user_data/{test_id}")
    
    # Wait a moment for page to load
    time.sleep(1)
    
    # Check that the user name element is showing
    user_element = driver.find_element(By.ID, 'user')
    if user_element:
        print(f"Frontend test passed! User name found using locator: {user_element.text}")
    else:
        raise Exception("User element not found.")
        
except Exception as e:
    raise Exception("test failed") from e
finally:
    # Cleanup
    if 'driver' in locals():
        driver.quit()
    db_connector.delete_user(test_id)
