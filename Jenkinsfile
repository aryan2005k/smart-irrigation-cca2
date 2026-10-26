```groovy
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'smart-irrigation'
        IMAGE_TAG = 'cca2'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Source code checked out from GitHub.'
                bat 'git --version'
            }
        }

        stage('Check Python') {
            steps {
                bat 'python --version'
                bat 'python -m pip --version'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                bat 'python -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t %IMAGE_NAME%:%IMAGE_TAG% .'
            }
        }

        stage('Verify Docker Image') {
            steps {
                bat 'docker image inspect %IMAGE_NAME%:%IMAGE_TAG%'
            }
        }
    }

    post {
        always {
            echo 'Smart Irrigation CI pipeline finished.'
        }
        success {
            echo 'All pipeline stages passed successfully.'
        }
        failure {
            echo 'Pipeline failed. Check the Console Output for details.'
        }
    }
}
