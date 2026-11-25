
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
    }

    environment {
        AWS_REGION = 'us-east-1'
        ECR_REPOSITORY = 'flask-app'

        MYSQL_ROOT_PASSWORD = credentials('mysql-root-password')
        MYSQL_PASSWORD = credentials('mysql-app-password')

        STATE_FILE = '/var/lib/jenkins/deployment-state/flask-app/last-good-image'
        COMPOSE_PROJECT = 'two-tier-flask-pipeline'
    }

    stages {

        stage('Initialize ECR Configuration') {
            steps {
                script {
                    env.AWS_ACCOUNT_ID = sh(
                        script: 'aws sts get-caller-identity --query Account --output text',
                        returnStdout: true
                    ).trim()

                    env.ECR_REGISTRY = "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com"

                    env.IMAGE_TAG = "build-${env.BUILD_NUMBER}"

                    env.FLASK_IMAGE = "${env.ECR_REGISTRY}/${env.ECR_REPOSITORY}:${env.IMAGE_TAG}"
                }
            }
        }

        stage('Validate Configuration') {
            steps {
                sh 'docker compose config --quiet'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker compose build flask'
            }
        }

        stage('Authenticate with ECR') {
            steps {
                sh '''#!/bin/bash
                    set -euo pipefail

                    aws ecr get-login-password --region "$AWS_REGION" | \
                    docker login --username AWS --password-stdin "$ECR_REGISTRY"
                '''
            }
        }

        stage('Push Image to ECR') {
            steps {
                sh 'docker push "$FLASK_IMAGE"'
            }
        }

        stage('Pull Image from ECR') {
            steps {
                sh 'docker compose pull flask'
            }
        }

        stage('Validate Rollback Image') {
            steps {
                sh '''
                    test -s "$STATE_FILE"

                    previous_image=$(cat "$STATE_FILE")

                    case "$previous_image" in
                        "$ECR_REGISTRY/$ECR_REPOSITORY":build-*)
                            echo "Last known good image: $previous_image"
                            ;;
                        *)
                            echo "Invalid rollback image"
                            exit 1
                            ;;
                    esac

                    docker image inspect "$previous_image" >/dev/null 2>&1 || \
                    docker pull "$previous_image"
                '''
            }
        }

        stage('Deploy and Verify Application') {
            steps {
                script {

                    def previousImage = sh(
                        script: 'cat "$STATE_FILE"',
                        returnStdout: true
                    ).trim()

                    echo "Rollback target: ${previousImage}"

                    try {
                        sh '''
                            docker compose -p "$COMPOSE_PROJECT" up \
                            -d --no-build --no-deps --wait \
                            --wait-timeout 120 flask

                            curl -fsS --max-time 15 \
                            http://localhost:5000/health

                            actual_image=$(docker inspect \
                            --format='{{.Config.Image}}' \
                            "${COMPOSE_PROJECT}-flask-1")

                            test "$actual_image" = "$FLASK_IMAGE"
                        '''

                        echo 'New deployment successful'

                    } catch (Exception deploymentError) {

                        echo 'New deployment failed'
                        echo "Initiating automatic rollback to ${previousImage}"

                        try {
                            withEnv(["FLASK_IMAGE=${previousImage}"]) {
                                sh '''
                                    docker image inspect "$FLASK_IMAGE" >/dev/null 2>&1 || \
                                    docker pull "$FLASK_IMAGE"

                                    docker compose -p "$COMPOSE_PROJECT" up \
                                    -d --no-build --no-deps --wait \
                                    --wait-timeout 120 flask

                                    curl -fsS --max-time 15 \
                                    http://localhost:5000/health

                                    actual_image=$(docker inspect \
                                    --format='{{.Config.Image}}' \
                                    "${COMPOSE_PROJECT}-flask-1")

                                    test "$actual_image" = "$FLASK_IMAGE"
                                '''
                            }

                            echo 'Automatic rollback successful'
                            echo "Restored image: ${previousImage}"

                        } catch (Exception rollbackError) {
                            error('Automatic rollback failed. Manual intervention required.')
                        }

                        error('New deployment failed. Previous stable image restored.')
                    }
                }
            }
        }

        stage('Update Last Known Good Image') {
            steps {
                sh '''
                    printf '%s\\n' "$FLASK_IMAGE" > "${STATE_FILE}.tmp"

                    mv "${STATE_FILE}.tmp" "$STATE_FILE"

                    echo "Updated last known good image:"
                    cat "$STATE_FILE"
                '''
            }
        }
    }

    post {
        success {
            echo 'Application deployed successfully'
            echo "Deployed image: ${env.FLASK_IMAGE}"
        }

        failure {
            echo 'Pipeline failed. Review console output.'
        }

        always {
            sh '''
                if [ -n "$ECR_REGISTRY" ]; then
                    docker logout "$ECR_REGISTRY" || true
                fi
            '''
        }
    }
}
