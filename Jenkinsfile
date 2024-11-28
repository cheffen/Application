pipeline {
    agent {
        kubernetes {
            label "music app"
            idleMinutes 5
            yamlFile 'build-pod.yaml'
            defaultContainer 'ez-docker-helm-build'
        }
    }
    environment {
        DOCKER_IMAGE = 'cheffen/music-site'
        GITHUB_API_URL = 'https://api.github.com'
        GITHUB_REPO = 'cheffen/Application'
        GITHUB_TOKEN = credentials('guthub-api')
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
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'dockerhub') {
                        dockerImage.push("latest")
                        dockerImage.push("1.0.${env.BUILD_NUMBER}")
                    }
                }
            }
        }

        stage('Update Helm values.yaml') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                withCredentials([string(credentialsId: 'guthub-api', variable: 'GITHUB_TOKEN')]) {
                    script {
                        def valuesFilePath = "music-site/values.yaml"
                        def valuesYaml = readFile(valuesFilePath)
                        def updatedYaml = valuesYaml.replaceAll(/(?<=tag: ).*/, "\"1.0.${env.BUILD_NUMBER}\"")
                        writeFile(file: valuesFilePath, text: updatedYaml)
                        sh """
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@example.com"
                            git add ${valuesFilePath}
                            git commit -m "[skip-ci] Update Helm chart image tag to 1.0.${env.BUILD_NUMBER}"
                            git push https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git HEAD:main
                        """
                    }
                }
            }
        }

        stage('Create merge request') {
            when {
                not {
                    anyOf {
                        branch 'main'
                        branch 'master'
                    }
                }
            }
            steps {
                withCredentials([string(credentialsId: 'guthub-api', variable: 'GITHUB_TOKEN')]) {
                    script {
                        def branchName = env.BRANCH_NAME
                        def baseBranch = "main" // Change to "master" if necessary
                        def pullRequestTitle = "Merge ${branchName} into ${baseBranch}"
                        def pullRequestBody = "Automatically generated merge request for branch ${branchName}"

                        sh """
                            curl -X POST -H "Authorization: token ${GITHUB_TOKEN.toString()}" \
                            -d '{
                                "title": "${pullRequestTitle}",
                                "body": "${pullRequestBody}",
                                "head": "${branchName}",
                                "base": "${baseBranch}"
                            }' \
                            ${GITHUB_API_URL}/repos/${GITHUB_REPO}/pulls
                        """
                    }
                }
            }
        }
    }
}
