pipeline {
    agent any

    stages {
        stage('REST') {
            steps {
                sh 'docker compose build rest'
            }
        }
        stage('GraphQL') {
            steps {
                sh 'docker compose build gql'
            }
        }
    }
}
