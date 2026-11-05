"""
web_app.py
This module provides a Web Interface to retrieve a user's name in HTML format.
It listens on port 5001 and connects to the database via db_connector.

Usage:
    python web_app.py <db_user> <db_password>
"""

import os
import signal
import threading
from flask import Flask
import db_connector

app = Flask(__name__)


@app.route('/users/get_user_data/<int:user_id>')
def get_user_name(user_id):
    """
    Returns the user name for user_id as HTML (id='user'),
    or an error (id='error') if the user does not exist.
    """
    try:
        user_name = db_connector.get_user(user_id)
    except Exception as e:
        return f"<H1 id='error'>database error: {e}</H1>", 500
    if user_name is None:
        return f"<H1 id='error'>no such user: {user_id}</H1>"
    else:
        return f"<H1 id='user'>{user_name}</H1>"


@app.route('/stop_server')
def stop_server():
    """
    Stops the server by sending SIGINT (Ctrl+C) to its own process.
    Note: signal.CTRL_C_EVENT is Windows-only, so SIGINT is used on Linux.
    The signal is delayed by 0.5s so this response is fully sent to the
    client before the server shuts down.
    """
    threading.Timer(0.5, os.kill, args=(os.getpid(), signal.SIGINT)).start()
    return 'Server stopped'


@app.errorhandler(404)
def page_not_found(error):
    """
    Returns an HTML error page for routes that do not exist (Extra 4).
    """
    return "<H1 id='error'>404 - page not found</H1>", 404


if __name__ == '__main__':
    # Read DB username/password from command line (Extra 3)
    db_connector.init_from_argv()
    # When started in the background from a script (e.g. Jenkins: `nohup ... &`),
    # the shell makes the process IGNORE SIGINT, so /stop_server would do nothing.
    # Re-enable the normal Ctrl+C (KeyboardInterrupt) behaviour explicitly.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    # Port 5001 so it doesn't conflict with the REST API; debug off for /stop_server
    app.run(host='127.0.0.1', debug=False, port=5001)
