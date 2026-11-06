"""
docker_backend_testing.py
Tests the DOCKERIZED rest_app.py (running via docker compose) on the docker host:
  1. POST a new user to the REST API in the container
  2. GET it back and check status code 200 + data
  3. Check the user was stored in the MySQL CONTAINER (users table)

Usage:
    python docker_backend_testing.py <db_user> <db_password>

Environment variables (optional):
    DOCKER_HOST_IP  - docker host address (default 127.0.0.1; native Docker on Linux)
    DOCKER_API_PORT - published REST API port (default 5000)
    DB_HOST/DB_PORT - published MySQL container address (default 127.0.0.1:3307)
"""
import os

# Point db_connector at the MySQL *container* (published on host port 3307)
# BEFORE importing it, unless the caller overrides it.
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3307")

import requests
import db_connector

DOCKER_HOST_IP = os.getenv("DOCKER_HOST_IP", "127.0.0.1")
DOCKER_API_PORT = os.getenv("DOCKER_API_PORT", "5000")
API_URL = f"http://{DOCKER_HOST_IP}:{DOCKER_API_PORT}/users"
TEST_ID = 200


def main():
    """
    Runs the POST -> GET -> DB check flow against the dockerized app.
    Raises Exception("test failed") on any failure.
    """
    db_connector.init_from_argv()

    # Test user name comes from the config table (inside the MySQL container)
    config = db_connector.get_config()
    test_user = config['test_user_name']
    print(f"Testing dockerized API at {API_URL} "
          f"(DB {db_connector.DB_HOST}:{db_connector.DB_PORT}) with user '{test_user}'")

    try:
        # 1. POST a new user
        post_res = requests.post(f"{API_URL}/{TEST_ID}", json={"user_name": test_user}, timeout=10)
        if post_res.status_code != 200:
            raise Exception(f"POST failed. Status: {post_res.status_code}, body: {post_res.text}")
        print("1. POST successful.")

        # 2. GET it back - status 200 and same data
        get_res = requests.get(f"{API_URL}/{TEST_ID}", timeout=10)
        if get_res.status_code != 200 or get_res.json().get('user_name') != test_user:
            raise Exception(f"GET failed or data mismatch. Status: {get_res.status_code}, body: {get_res.text}")
        print("2. GET successful. Data matches.")

        # 3. Check the row directly in the MySQL container
        db_user = db_connector.get_user(TEST_ID)
        if db_user != test_user:
            raise Exception(f"DB check failed. Expected {test_user}, got {db_user}")
        print("3. Database (container) check successful.")
        print("\n✅ Dockerized backend test passed!")

    except Exception as e:
        print(f"Exception details: {e}")
        raise Exception("test failed") from e
    finally:
        # Cleanup - ignore errors so the original failure (if any) is reported
        try:
            db_connector.delete_user(TEST_ID)
        except Exception:
            pass


if __name__ == '__main__':
    main()
