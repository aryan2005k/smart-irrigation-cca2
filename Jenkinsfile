pipeline {
    agent any

    environment {
        IMAGE_NAME = 'smart-irrigation'
        IMAGE_TAG = 'cca2'

        AWS_REGION = 'ap-south-1'
        AWS_ACCOUNT_ID = '182844680094'
        ECR_REPOSITORY = 'smart-irrigation-cca2'
        EC2_HOST = '35.154.150.99'

        DOCKER_EXE = 'C:/Users/Lenovo/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe'
        PYTHON_EXE = 'C:/Users/Lenovo/AppData/Local/Programs/Python/Python314/python.exe'
        AWS_EXE = 'C:/Program Files/Amazon/AWSCLIV2/aws.exe'
    }

    stages {
        stage('Checkout SCM') {
            steps {
                checkout scm
                echo 'Source code checked out from GitHub.'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '"%PYTHON_EXE%" -m pip install --user -r requirements.txt'
                bat '"%PYTHON_EXE%" -m pip install --user pytest'
            }
        }

        stage('Run Tests') {
            steps {
                bat '"%PYTHON_EXE%" -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat '"%DOCKER_EXE%" build -t %IMAGE_NAME%:%IMAGE_TAG% .'
                bat '"%DOCKER_EXE%" image inspect %IMAGE_NAME%:%IMAGE_TAG%'
            }
        }

        stage('Push Image to ECR') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'aws-credentials',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    )
                ]) {
                    bat '''
                        set AWS_DEFAULT_REGION=%AWS_REGION%
                        set AWS_REGION=%AWS_REGION%
                        set AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID%
                        set AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY%

                        "%AWS_EXE%" ecr get-login-password --region %AWS_REGION% | "%DOCKER_EXE%" login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com

                        if errorlevel 1 exit /b 1

                        "%DOCKER_EXE%" tag %IMAGE_NAME%:%IMAGE_TAG% %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%:%IMAGE_TAG%

                        if errorlevel 1 exit /b 1

                        "%DOCKER_EXE%" push %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%:%IMAGE_TAG%

                        if errorlevel 1 exit /b 1
                    '''
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'irrigation-ec2-ssh',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    bat '''
                        ssh -i "%SSH_KEY%" -o StrictHostKeyChecking=no %SSH_USER%@%EC2_HOST% "aws ecr get-login-password --region %AWS_REGION% | sudo docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com && sudo docker pull %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%:%IMAGE_TAG% && (sudo docker rm -f smart-irrigation || true) && sudo docker run -d --restart unless-stopped --name smart-irrigation -p 5000:5000 %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPOSITORY%:%IMAGE_TAG%"
                    '''
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'irrigation-ec2-ssh',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    bat '''
                        ssh -i "%SSH_KEY%" -o StrictHostKeyChecking=no %SSH_USER%@%EC2_HOST% "sudo docker ps --filter name=smart-irrigation && curl -fsS http://localhost:5000/health"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo 'Smart Irrigation CI/CD pipeline finished.'
        }
        success {
            echo 'All CI/CD stages passed successfully.'
        }
        failure {
            echo 'Pipeline failed. Check Console Output for details.'
        }
    }
}