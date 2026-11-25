pipeline {
    agent any

    options {
        disableConcurrentBuilds()
    }

    environment {
        MYSQL_ROOT_PASSWORD = credentials('mysql-root-password')
        MYSQL_PASSWORD = credentials('mysql-app-password')
    }

    stages {

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

        stage('Deploy Application') {
            steps {
                sh 'docker compose up -d --no-build --wait'
            }
        }

        stage('Verify Deployment') {
            steps {
                sh 'curl -fsS http://localhost:5000/health'
            }
        }
    }

    post {
        success {
            echo 'Application deployed successfully'
        }

        failure {
            echo 'Deployment failed'
        }
    }
}
