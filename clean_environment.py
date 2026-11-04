"""
clean_environment.py
Stops both Flask servers (REST API on 5000 and Web App on 5001)
by calling their /stop_server routes.
Errors are caught so the script never crashes if a server is not responding.
"""
import requests

SERVERS = {
    "REST API": "http://127.0.0.1:5000/stop_server",
    "Web App": "http://127.0.0.1:5001/stop_server",
}


def stop_server(name, url):
    """
    Sends a GET request to a server's /stop_server route.
    Handles the case where the server is down or not responding.
    """
    try:
        response = requests.get(url, timeout=5)
        print(f"{name}: {response.text} (status {response.status_code})")
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
