// Jenkinsfile
// CI pipeline: pull code -> start REST API + Web App -> run backend, frontend
// and combined tests -> stop the servers (clean_environment.py).

pipeline {
    agent any

    // Poll SCM every 30 minutes for new commits on master
    triggers {
        pollSCM('H/30 * * * *')
    }

    options {
        // Log rotation: keep builds max 5 days and max 20 builds
        buildDiscarder(logRotator(daysToKeepStr: '5', numToKeepStr: '20'))
        // We do the checkout ourselves in the "Pull code" stage
        skipDefaultCheckout()
    }

    environment {
        // Address that receives an email on failure (Extra 1)
        NOTIFY_EMAIL = 'n.badjevic@gmail.com'
        // Path to the Python interpreter of the venv created by this pipeline
        PY = "${WORKSPACE}/venv/bin/python"
    }

    stages {
        stage('Pull code') {
            steps {
                checkout scm
            }
        }

        stage('Set up Python environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    venv/bin/pip install --upgrade pip
                    venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Run backend server (rest_app.py)') {
            steps {
                // DB credentials come from the Jenkins global credential 'db_credentials' (Extra 3B)
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    // JENKINS_NODE_COOKIE=dontKillMe stops Jenkins from killing the
                    // background server between stages; clean_environment.py stops it.
                    sh 'JENKINS_NODE_COOKIE=dontKillMe nohup $PY rest_app.py "$DB_USER" "$DB_PASS" > rest_app.log 2>&1 &'
                }
            }
        }

        stage('Run frontend server (web_app.py)') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    sh 'JENKINS_NODE_COOKIE=dontKillMe nohup $PY web_app.py "$DB_USER" "$DB_PASS" > web_app.log 2>&1 &'
                }
                // Give both servers a moment to start listening
                sh 'sleep 5'
            }
        }

        stage('Run backend_testing.py') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    sh '$PY backend_testing.py "$DB_USER" "$DB_PASS"'
                }
            }
        }

        stage('Run frontend_testing.py') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    sh '$PY frontend_testing.py "$DB_USER" "$DB_PASS"'
                }
            }
        }

        stage('Run combined_testing.py') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    sh '$PY combined_testing.py "$DB_USER" "$DB_PASS"'
                }
            }
        }

        stage('Run clean_environment.py') {
            steps {
                sh '$PY clean_environment.py'
            }
        }
    }

    post {
        always {
            // Make sure servers are stopped even if a test failed.
            // clean_environment.py handles "server not responding" gracefully.
            sh '$PY clean_environment.py || true'
            archiveArtifacts artifacts: '*.log', allowEmptyArchive: true
        }
        failure {
            // Extra 1: email on failure (requires SMTP configured in Jenkins)
            mail to: "${NOTIFY_EMAIL}",
                 subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: "Build failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}\nSee console output: ${env.BUILD_URL}console"
        }
    }
}
