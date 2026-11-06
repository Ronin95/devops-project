# Dockerfile - image for the REST API (rest_app.py)
FROM python:3.12-slim

WORKDIR /app

# Only the packages the REST API needs (no Selenium)
RUN pip install --no-cache-dir flask pymysql cryptography pypika

COPY db_connector.py rest_app.py ./

# Listen on all interfaces so the API is reachable from outside the container
ENV FLASK_HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# DB user/password are passed as arguments (sys.argv) by docker compose:
#   command: ["python", "rest_app.py", "<db_user>", "<db_password>"]
ENTRYPOINT ["python", "rest_app.py"]
