pipeline {
    agent {
        kubernetes {
            label "weather-app-agent"
            idleMinutes 5
            yamlFile 'build-pod.yaml'
            defaultContainer 'ez-docker-helm-build'
        }
    }
    environment {
        DOCKER_IMAGE = 'winterzone2/weather-app'
        GITHUB_API_URL = 'https://api.github.com'
        GITHUB_REPO = 'DaryAkerman/weather-app'
        GITHUB_TOKEN = credentials('github-token')
    }

    stages {
        stage("Checkout code") {
            steps {
                script {
                    sh "git config --global --add safe.directory ${env.WORKSPACE}"
                    checkout scm
                    def commitMessage = sh(
                        script: "git log -1 --pretty=%B",
                        returnStdout: true
                    ).trim()

                    if (commitMessage.contains("[skip-ci]")) {
                        echo "Skipping build due to commit message: ${commitMessage}"
                        error("Build aborted due to [skip-ci] in commit message.") 
                    }
                    
                    echo "Proceeding with build. Commit message: ${commitMessage}"
                }
            }
        }

        stage("Build docker image") {
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_IMAGE}:latest", "--no-cache .")
                    dockerImage.tag("1.0.${env.BUILD_NUMBER}")
                }
            }
        }

        stage('Push Docker image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-creds') {
                        dockerImage.push("latest")
                        dockerImage.push("1.0.${env.BUILD_NUMBER}")
                    }
                }
            }
        }

        stage('Update Helm values.yaml') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([string(credentialsId: 'github-secret', variable: 'GITHUB_TOKEN')]) {
                    script {
                        def valuesFilePath = "applic/values.yaml"
                        def valuesYaml = readFile(valuesFilePath)
                        def updatedYaml = valuesYaml.replaceAll(/(?<=tag: ).*/, "\"1.0.${env.BUILD_NUMBER}\"")
                        writeFile(file: valuesFilePath, text: updatedYaml)
                        sh """
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@example.com"
                            git add ${valuesFilePath}
                            git commit -m "[skip-ci] Update Helm chart image tag to 1.0.${env.BUILD_NUMBER}"
                            git push https://$GITHUB_TOKEN@github.com/${GITHUB_REPO}.git HEAD:main
                        """
                    }
                }
            }
        }

        stage('Create merge request') {
            when {
                not {
                    branch 'main'
                }
            }
            steps {
                withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
                    script {
                        def branchName = env.BRANCH_NAME
                        def pullRequestTitle = "Merge ${branchName} into main"
                        def pullRequestBody = "Automatically generated merge request for branch ${branchName}"

                        sh """
                            curl -X POST -H "Authorization: token ${GITHUB_TOKEN}" \
                            -d '{ "title": "${pullRequestTitle}", "body": "${pullRequestBody}", "head": "${branchName}", "base": "main" }' \
                            ${GITHUB_API_URL}/repos/${GITHUB_REPO}/pulls
                        """
                    }
                }
            }
        }
    }
}
