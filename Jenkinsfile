pipeline {
    agent {
        kubernetes {
            label 'music_app'
            yamlFile 'build-pod.yaml'
        }
    }
    environment {
        DOCKER_IMAGE = "cheffen/music-site"
        IMAGE_TAG = "1.0.${env.BUILD_NUMBER}"
        DOCKER_CREDENTIAL_ID = 'dockerhub' // Ensure this ID matches your Jenkins credentials
        GITHUB_TOKEN_ID = 'guthub-api' // Ensure this ID matches your Jenkins credentials
    }
    stages {
        stage('Checkout SCM') {
            steps {
                checkout scm
                script {
                    sh "git config --global --add safe.directory ${WORKSPACE}"
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                container('ez-docker-helm-build') {
                    sh """
                        docker build -t ${DOCKER_IMAGE}:latest --no-cache .
                        docker tag ${DOCKER_IMAGE}:latest ${DOCKER_IMAGE}:${IMAGE_TAG}
                    """
                }
            }
        }
        stage('Push Docker Image') {
            steps {
                container('ez-docker-helm-build') {
                    withDockerRegistry([ 
                        credentialsId: "${DOCKER_CREDENTIAL_ID}", 
                        url: 'https://index.docker.io/v1/' 
                    ]) {
                        sh """
                            docker push ${DOCKER_IMAGE}:latest
                            docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }
        stage('Update Helm values.yaml') {
            steps {
                withCredentials([string(credentialsId: "${GITHUB_TOKEN_ID}", variable: 'GITHUB_TOKEN')]) {
                    script {
                        def valuesFilePath = "music-site/values.yaml"
                        if (fileExists(valuesFilePath)) {
                            echo "Updating Helm values.yaml..."
                            def valuesYaml = readFile(valuesFilePath)
                            def updatedYaml = valuesYaml.replaceAll(/(?<=tag: ).*/, "\"${IMAGE_TAG}\"")
                            writeFile(file: valuesFilePath, text: updatedYaml)
                            
                            // Configure Git user
                            sh """
                                git config user.name "Jenkins CI"
                                git config user.email "jenkins@example.com"
                            """
                            
                            // Stage and commit changes
                            sh """
                                git add ${valuesFilePath}
                                git commit -m "[skip-ci] Update Helm chart image tag to ${IMAGE_TAG}"
                            """
                            
                            // Fetch latest changes from remote master
                            sh """
                                git fetch origin master
                                git rebase origin/master
                            """
                            
                            // Push changes to remote master using HEAD:master to handle detached HEAD
                            sh """
                                git push https://${GITHUB_TOKEN}@github.com/cheffen/Application.git HEAD:master
                            """
                        } else {
                            echo "File not found: ${valuesFilePath}. Skipping update."
                        }
                    }
                }
            }
        }
        stage('Create Merge Request') {
            steps {
                echo "Stage 'Create Merge Request' skipped because pushing directly to master."
            }
        }
    }
    post {
        success {
            echo "Pipeline executed successfully."
        }
        failure {
            echo "Pipeline failed. Check logs for details."
        }
    }
}
