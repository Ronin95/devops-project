"""
rest_app.py
This module acts as the REST API for managing users.
It listens on port 5000 and connects to the database via db_connector.

Usage:
    python rest_app.py <db_user> <db_password>
"""

import os
import signal
import threading
from flask import Flask, request, jsonify
import db_connector

app = Flask(__name__)


@app.route('/users/<int:user_id>', methods=['POST', 'GET', 'PUT', 'DELETE'])
def manage_users(user_id):
    """
    Handles create (POST), read (GET), update (PUT) and delete (DELETE)
    operations for the user with the given user_id.
    """
    if request.method == 'POST':
        try:
            request_data = request.json
            user_name = request_data.get('user_name')

            # Check if user already exists
            existing_user = db_connector.get_user(user_id)
            if existing_user:
                # Extra 5: ID collision fallback - Find a free ID
                user_id = db_connector.get_free_id()

            db_connector.insert_user(user_id, user_name)
            return jsonify({"status": "ok", "user_added": user_name}), 200
        except Exception as e:
            return jsonify({"status": "error", "reason": str(e)}), 500

    elif request.method == 'GET':
        try:
            user_name = db_connector.get_user(user_id)
            if user_name:
                return jsonify({"status": "ok", "user_name": user_name}), 200
            else:
                return jsonify({"status": "error", "reason": "no such id"}), 500
        except Exception as e:
            return jsonify({"status": "error", "reason": str(e)}), 500

    elif request.method == 'PUT':
        try:
            request_data = request.json
            user_name = request_data.get('user_name')
            updated = db_connector.update_user(user_id, user_name)
            if updated:
                return jsonify({"status": "ok", "user_updated": user_name}), 200
            else:
                return jsonify({"status": "error", "reason": "no such id"}), 500
        except Exception as e:
            return jsonify({"status": "error", "reason": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            deleted = db_connector.delete_user(user_id)
            if deleted:
                return jsonify({"status": "ok", "user_deleted": user_id}), 200
            else:
                return jsonify({"status": "error", "reason": "no such id"}), 500
        except Exception as e:
            return jsonify({"status": "error", "reason": str(e)}), 500


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
    Returns a JSON error for routes that do not exist (Extra 4).
    """
    return jsonify({"status": "error", "reason": "route not found"}), 404


if __name__ == '__main__':
    # Read DB username/password from command line (Extra 3)
    db_connector.init_from_argv()
    # When started in the background from a script (e.g. Jenkins: `nohup ... &`),
    # the shell makes the process IGNORE SIGINT, so /stop_server would do nothing.
    # Re-enable the normal Ctrl+C (KeyboardInterrupt) behaviour explicitly.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    # debug=False: the debug reloader spawns a 2nd process, which would
    # prevent /stop_server from shutting the server down cleanly.
    app.run(host='127.0.0.1', debug=False, port=5000)
