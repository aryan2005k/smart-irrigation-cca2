
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

        stage('Install Dependencies') {
    steps {
        bat '"C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" -m pip install --user -r requirements.txt'
        bat '"C:\\Users\\Lenovo\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" -m pip install --user pytest'
    }
}


        stage('Run Tests') {
    steps {
        bat '"C:/Users/Lenovo/AppData/Local/Programs/Python/Python314/python.exe" -m pytest -v'
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
