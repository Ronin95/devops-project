// Jenkinsfile  (Part 4 - CD to Kubernetes with Helm)
// 1-4   test rest_app.py locally
// 5-10  build + push Docker image, run it with docker compose (+ MySQL container), test, clean
// 11-14 deploy the image to minikube with Helm, test it via the service URL, helm delete
// Extras: K8S Secret (DB user/password), ConfigMap (DB host), MySQL StatefulSet + PV/PVC

pipeline {
    agent any

    // Poll SCM every 30 minutes for new commits on master
    triggers {
        pollSCM('H/30 * * * *')
    }

    options {
        // Log rotation: keep builds max 5 days and max 20 builds
        buildDiscarder(logRotator(daysToKeepStr: '5', numToKeepStr: '20'))
        skipDefaultCheckout()
    }

    environment {
        NOTIFY_EMAIL = 'n.badjevic@gmail.com'
        PY = "${WORKSPACE}/venv/bin/python"
        // Docker Hub repository (created on Docker Hub, credentials in Jenkins)
        DOCKER_IMAGE = 'nbadjev/devops-rest-app'
        // Private Docker config for Jenkins: uses the local Docker Engine
        // (default context) and no Docker Desktop credential helper.
        DOCKER_CONFIG = "${WORKSPACE}/.docker"
        COMPOSE_PROJECT_NAME = 'devops'
        HELM_RELEASE = 'devops-rest-app'
        HELM_CHART = 'helm/devops-rest-app'
    }

    stages {
        // ---------- 1. Pull code ----------
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

        // ---------- 2-4. Local backend ----------
        stage('Run rest_app.py') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    sh 'JENKINS_NODE_COOKIE=dontKillMe nohup $PY rest_app.py "$DB_USER" "$DB_PASS" > rest_app.log 2>&1 &'
                }
                sh 'sleep 3'
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

        stage('Run clean_environment.py') {
            steps {
                sh '$PY clean_environment.py'
            }
        }

        // ---------- 5-6. Docker image ----------
        stage('Build Docker image') {
            steps {
                sh 'docker build -t "$DOCKER_IMAGE:$BUILD_NUMBER" .'
            }
        }

        stage('Push Docker image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub_credentials',
                                                  usernameVariable: 'DH_USER',
                                                  passwordVariable: 'DH_TOKEN')]) {
                    sh '''
                        echo "$DH_TOKEN" | docker login -u "$DH_USER" --password-stdin
                        docker push "$DOCKER_IMAGE:$BUILD_NUMBER"
                    '''
                }
            }
        }

        // ---------- 7-10. docker compose ----------
        stage('Set compose image version') {
            steps {
                sh 'echo IMAGE_TAG=${BUILD_NUMBER} > .env'
                sh 'cat .env'
            }
        }

        stage('docker compose up -d') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    sh 'docker compose up -d'
                }
                // MySQL first has to pass its healthcheck, then rest_app starts.
                // curl -s succeeds on ANY HTTP answer -> the API is up.
                sh '''
                    for i in $(seq 1 45); do
                        if curl -s -o /dev/null http://127.0.0.1:5000/users/0; then
                            echo "Dockerized REST API is up"
                            docker ps --filter "name=devops-"
                            exit 0
                        fi
                        echo "Waiting for REST API container... ($i/45)"
                        sleep 2
                    done
                    echo "REST API container did not come up in time"
                    docker ps -a --filter "name=devops-"
                    exit 1
                '''
            }
        }

        stage('Test dockerized app') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    sh '$PY docker_backend_testing.py "$DB_USER" "$DB_PASS"'
                }
            }
        }

        stage('Clean compose environment') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    sh '''
                        docker compose logs --no-color > docker-compose.log 2>&1 || true
                        docker compose down -v --remove-orphans
                    '''
                }
                // minikube pulls the image from Docker Hub, the local copy is not needed
                sh 'docker rmi "$DOCKER_IMAGE:$BUILD_NUMBER"'
            }
        }

        // ---------- K8S prerequisites (Extras 1-3) ----------
        stage('Prepare K8S (Secret, ConfigMap, MySQL)') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                                  usernameVariable: 'DB_USER',
                                                  passwordVariable: 'DB_PASS')]) {
                    // Extra 1: Secret with DB user/password - created from Jenkins
                    // credentials, so the password is never stored in git
                    sh '''
                        kubectl create secret generic db-secret \
                            --from-literal=DB_USER="$DB_USER" \
                            --from-literal=DB_PASSWORD="$DB_PASS" \
                            --dry-run=client -o yaml | kubectl apply -f -
                    '''
                }
                // MySQL init script (same file docker compose uses)
                sh '''
                    kubectl create configmap mysql-initdb \
                        --from-file=init.sql=mysql-init/init.sql \
                        --dry-run=client -o yaml | kubectl apply -f -
                '''
                // Extra 2: ConfigMap db-config, Extra 3: PV, PVC, MySQL StatefulSet + Service
                sh 'kubectl apply -f k8s/'
                sh 'kubectl rollout status statefulset/mysql --timeout=300s'
            }
        }

        // ---------- 11-14. Helm / K8S ----------
        stage('Deploy HELM chart') {
            steps {
                // No "helm --wait": it also waits for the LoadBalancer to get an
                // EXTERNAL-IP, which minikube never assigns without "minikube tunnel".
                // Instead wait only until all pods of the Deployment are ready.
                sh '''
                    helm upgrade --install "$HELM_RELEASE" "$HELM_CHART" \
                        --set image.repository="$DOCKER_IMAGE:$BUILD_NUMBER"
                    kubectl rollout status deployment/hello-python --timeout=300s
                    kubectl get pods -l app=hello-python -o wide
                '''
            }
        }

        stage('Write service URL') {
            steps {
                sh 'minikube service hello-python-service --url > k8s_url.txt'
                sh 'cat k8s_url.txt'
            }
        }

        stage('Test deployed app') {
            steps {
                sh '$PY K8S_backend_testing.py k8s_url.txt'
            }
        }

        stage('Clean HELM environment') {
            steps {
                sh 'helm delete "$HELM_RELEASE"'
            }
        }
    }

    post {
        always {
            // Collect K8S info for debugging (only useful if the release still exists)
            sh '''
                kubectl get pods -o wide > k8s-pods.log 2>&1 || true
                kubectl logs -l app=hello-python --tail=50 --prefix > k8s-app.log 2>&1 || true
            '''
            // Safety net: everything below is idempotent and ignores errors,
            // so a failed build never leaves anything running.
            sh 'helm delete "$HELM_RELEASE" 2>/dev/null || true'
            withCredentials([usernamePassword(credentialsId: 'db_credentials',
                                              usernameVariable: 'DB_USER',
                                              passwordVariable: 'DB_PASS')]) {
                sh 'docker compose down -v --remove-orphans || true'
            }
            sh 'docker rmi "$DOCKER_IMAGE:$BUILD_NUMBER" 2>/dev/null || true'
            sh '[ -x "$PY" ] && $PY clean_environment.py || true'
            sh 'docker logout || true'
            archiveArtifacts artifacts: '*.log, k8s_url.txt', allowEmptyArchive: true
        }
        failure {
            mail to: "${NOTIFY_EMAIL}",
                 subject: "FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                 body: "Build failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}\nSee console output: ${env.BUILD_URL}console"
        }
    }
}
