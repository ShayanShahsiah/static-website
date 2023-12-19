pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                sh 'docker build rest -t my-rest-img'
                sh 'docker build gql -t my-gql-img'
            }
        }
        stage('Deploy') {
            steps {
				sh 'docker run --name my-rest -p 8001:8001 -d my-rest-img'
				sh 'docker run --name my-gql -p 8000:8000 -d my-gql-img'
            }
        }
    }
}
