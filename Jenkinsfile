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
				sh 'docker run --rm -p 8002:8002 -d my-rest-img'
				sh 'docker run --rm -p 8000:8000 -d my-gql-img'
            }
        }
    }
}
