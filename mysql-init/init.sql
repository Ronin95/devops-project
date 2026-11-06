-- mysql-init/init.sql
-- Runs automatically the FIRST time the MySQL container starts
-- (empty data volume). Creates the tables used by rest_app.py and the tests.

USE devops_db;

CREATE TABLE IF NOT EXISTS users (
    user_id       INT PRIMARY KEY,
    user_name     VARCHAR(50) NOT NULL,
    creation_date DATETIME    NOT NULL
);

CREATE TABLE IF NOT EXISTS config (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    api_url        VARCHAR(255) NOT NULL,
    browser        VARCHAR(50)  NOT NULL,
    test_user_name VARCHAR(50)  NOT NULL
);

INSERT INTO config (api_url, browser, test_user_name)
VALUES ('http://127.0.0.1:5000/users', 'Chrome', 'docker_user');
