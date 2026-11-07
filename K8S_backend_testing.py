"""
K8S_backend_testing.py
Tests the REST API deployed on the Kubernetes (minikube) cluster via Helm.

The service URL is read from k8s_url.txt, which the pipeline creates with:
    minikube service hello-python-service --url > k8s_url.txt
Example content: http://192.168.49.2:31480

Steps:
  1. Wait until the service answers
  2. POST a new user to <url>/users/<id>
  3. GET it back and check status code 200 + data
  4. DELETE it again (cleanup)

Usage:
    python K8S_backend_testing.py [path_to_url_file]   (default: k8s_url.txt)
"""
import sys
import time
import requests

URL_FILE = sys.argv[1] if len(sys.argv) > 1 else "k8s_url.txt"
TEST_ID = 300
TEST_USER = "k8s_user"


def read_service_url(path):
    """
    Returns the first line of the file that starts with 'http'
    (minikube may print extra lines), without a trailing slash.
    """
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("http"):
                    return line.rstrip("/")
    except OSError as e:
        raise Exception(f"Cannot read {path}: {e}")
    raise Exception(f"No URL found in {path}")


def wait_for_service(api_url, timeout=60):
    """
    Polls the service until it answers with ANY HTTP response.
    Raises an exception if it does not answer within `timeout` seconds.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            requests.get(f"{api_url}/{TEST_ID}", timeout=3)
            return
        except requests.exceptions.RequestException:
            time.sleep(2)
    raise Exception(f"Service {api_url} did not answer within {timeout}s")


def main():
    """
    Runs the POST -> GET -> DELETE flow against the K8S service.
    Raises Exception("test failed") on any failure.
    """
    try:
        base_url = read_service_url(URL_FILE)
        api_url = f"{base_url}/users"
        print(f"Testing K8S deployment at {api_url} with user '{TEST_USER}'")

        wait_for_service(api_url)

        # Make sure the test ID is free (leftover from an aborted run)
        requests.delete(f"{api_url}/{TEST_ID}", timeout=10)

        # 1. POST a new user
        post_res = requests.post(f"{api_url}/{TEST_ID}", json={"user_name": TEST_USER}, timeout=10)
        if post_res.status_code != 200:
            raise Exception(f"POST failed. Status: {post_res.status_code}, body: {post_res.text}")
        print("1. POST successful.")

        # 2. GET it back - status 200 and same data
        get_res = requests.get(f"{api_url}/{TEST_ID}", timeout=10)
        if get_res.status_code != 200 or get_res.json().get('user_name') != TEST_USER:
            raise Exception(f"GET failed or data mismatch. Status: {get_res.status_code}, body: {get_res.text}")
        print("2. GET successful. Data matches.")

        # 3. DELETE (cleanup) - also verifies the delete endpoint
        del_res = requests.delete(f"{api_url}/{TEST_ID}", timeout=10)
        if del_res.status_code != 200:
            raise Exception(f"DELETE failed. Status: {del_res.status_code}, body: {del_res.text}")
        print("3. DELETE successful.")
        print("\n✅ K8S backend test passed!")

    except Exception as e:
        print(f"Exception details: {e}")
        raise Exception("test failed") from e


if __name__ == '__main__':
    main()
