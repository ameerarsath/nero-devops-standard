# Jenkins Shared Library

1. Put this `shared-library` directory in its own Git repository (recommended), for example `company-ci-library`.
2. In Jenkins, open **Manage Jenkins → System → Global Pipeline Libraries**.
3. Add a library named `company-ci`, configure the SCM repository URL and credentials, and select a protected default branch/tag.
4. In a Jenkinsfile, load it with:

```groovy
@Library('company-ci') _

pipeline {
    agent { label 'linux-docker' }
    stages {
        stage('Build image') {
            steps {
                script {
                    standardDockerBuild(image: 'registry.example.com/team/sample-app')
                }
            }
        }
    }
}
```

Do not let untrusted pull-request branches change a trusted shared-library revision or access privileged credentials. Review and version shared-library changes like production code.
