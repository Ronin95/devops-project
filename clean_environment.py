"""
clean_environment.py
Stops both Flask servers (REST API on 5000 and Web App on 5001)
by calling their /stop_server routes.
Errors are caught so the script never crashes if a server is not responding.
"""
import time
import requests

SERVERS = {
    "REST API": "http://127.0.0.1:5000/stop_server",
    "Web App": "http://127.0.0.1:5001/stop_server",
}


def wait_until_down(name, url, timeout=5):
    """
    Polls the server until it no longer accepts connections,
    so we can confirm it has really shut down.
    Returns True if the server went down within `timeout` seconds.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            # Any request works - we only care whether the server still answers
            requests.get(url.replace('/stop_server', '/'), timeout=1)
        except requests.exceptions.RequestException:
            print(f"{name}: confirmed stopped")
            return True
    print(f"{name}: WARNING - still running after {timeout}s")
    return False


def stop_server(name, url):
    """
    Sends a GET request to a server's /stop_server route.
    Handles the case where the server is down or not responding.
    """
    try:
        response = requests.get(url, timeout=5)
        print(f"{name}: {response.text} (status {response.status_code})")
        wait_until_down(name, url)
    except requests.exceptions.ConnectionError:
        # Either the server was already down, or it shut down before replying
        print(f"{name}: not responding (already stopped?)")
    except requests.exceptions.Timeout:
        print(f"{name}: request timed out")
    except requests.exceptions.RequestException as e:
        print(f"{name}: error while stopping server: {e}")


if __name__ == '__main__':
    for server_name, server_url in SERVERS.items():
        stop_server(server_name, server_url)
