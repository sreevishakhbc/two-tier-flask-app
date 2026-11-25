
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

        PREVIOUS_IMAGE = ''
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
                sh '''
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

        stage('Capture Previous Stable Image') {
            steps {
                script {
                    sh 'curl -fsS --max-time 15 http://localhost:5000/health'

                    env.PREVIOUS_IMAGE = sh(
                        script: '''
                            docker inspect --format='{{.Config.Image}}' \
                            two-tier-flask-pipeline-flask-1
                        ''',
                        returnStdout: true
                    ).trim()

                    echo "Previous stable image: ${env.PREVIOUS_IMAGE}"
                }
            }
        }

        stage('Deploy and Verify Application') {
            steps {
                script {
                    try {
                        sh '''
                            docker compose -p two-tier-flask-pipeline up \
                            -d --no-build --no-deps --wait --wait-timeout 120 flask
                        '''

                        sh 'curl -fsS --max-time 15 http://localhost:5000/health'

                        echo "New deployment successful"

                    } catch (Exception deploymentError) {

                        echo 'New deployment failed'
                        echo "Initiating automatic rollback to ${env.PREVIOUS_IMAGE}"

                        try {
                            withEnv(["FLASK_IMAGE=${env.PREVIOUS_IMAGE}"]) {
                                sh '''
                                    docker compose -p two-tier-flask-pipeline pull flask

                                    docker compose -p two-tier-flask-pipeline up \
                                    -d --no-build --no-deps --wait --wait-timeout 120 flask

                                    curl -fsS --max-time 15 http://localhost:5000/health
                                '''
                            }

                            echo "Automatic rollback successful"
                            echo "Restored image: ${env.PREVIOUS_IMAGE}"

                        } catch (Exception rollbackError) {
                            error('Automatic rollback failed. Manual intervention required.')
                        }

                        error('New deployment failed. Previous stable version restored.')
                    }
                }
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
