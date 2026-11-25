
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

        stage('Deploy Application') {
            steps {
                sh 'docker compose up -d --no-build --wait'
            }
        }

        stage('Verify Deployment') {
            steps {
                sh 'curl -fsS --max-time 15 http://localhost:5000/health'
            }
        }
    }

    post {
        success {
            echo "Application deployed successfully"
            echo "Deployed image: ${env.FLASK_IMAGE}"
        }

        failure {
            echo 'Deployment failed'
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
