pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds() }
  environment {
    AWS_DEFAULT_REGION = 'ap-south-1'
    AWS_ACCOUNT_ID = credentials('aws-account-id')
    ECR_REPOSITORY = 'smart-irrigation-cca2'
    IMAGE_TAG = "${BUILD_NUMBER}"
    EC2_HOST = credentials('irrigation-ec2-host')
    EC2_USER = 'ubuntu'
  }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Test') {
      steps {
        sh 'python3 -m venv .venv'
        sh '. .venv/bin/activate && pip install -r requirements.txt && pytest -q'
      }
    }
    stage('Build') { steps { sh 'docker build -t $ECR_REPOSITORY:$IMAGE_TAG .' } }
    stage('Push to ECR') {
      steps {
        withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-credentials']]) {
          sh 'aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_DEFAULT_REGION >/dev/null 2>&1 || aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_DEFAULT_REGION'
          sh 'aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com'
          sh 'docker tag $ECR_REPOSITORY:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG'
          sh 'docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG'
        }
      }
    }
    stage('Deploy to EC2') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'irrigation-ec2-ssh', keyFileVariable: 'SSH_KEY')]) {
          sh 'ssh -o StrictHostKeyChecking=no -i $SSH_KEY $EC2_USER@$EC2_HOST docker pull $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG'
          sh 'ssh -o StrictHostKeyChecking=no -i $SSH_KEY $EC2_USER@$EC2_HOST docker stop smart-irrigation || true'
          sh 'ssh -o StrictHostKeyChecking=no -i $SSH_KEY $EC2_USER@$EC2_HOST docker rm smart-irrigation || true'
          sh 'ssh -o StrictHostKeyChecking=no -i $SSH_KEY $EC2_USER@$EC2_HOST docker run -d --name smart-irrigation --restart unless-stopped -p 80:5000 -v irrigation-data:/app/data $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$ECR_REPOSITORY:$IMAGE_TAG'
        }
      }
    }
    stage('Verify') { steps { echo 'Verify http://<EC2-public-ip>/health after deployment.' } }
  }
  post { always { sh 'docker image prune -f || true' } }
}
