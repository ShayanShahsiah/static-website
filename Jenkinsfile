pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'docker build rest -t my-rest'
                sh 'docker build gql -t my-gql'
            }
        }
        stage('Deploy') {
            steps {
				sh 'docker run -p 8001:8001 -d my-rest'
				sh 'docker run -p 8000:8000 -d my-gql'
            }
        }
    }
}
