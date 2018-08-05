# devsecops

Deploy serverless function with custom domain and Inspec test:

* create a Jenkins server in AWS using https://github.com/celidor/devsecops-jenkins
* fork the repository to your own GitHub account
* create a SCM pipeline pointing to your repository
* create a pipeline with Inspec tests
* test your pipeline in Jenkins

A fully completed Jenkins pipeline and Inspec tests can be seen at https://github.com/celidor/devsecops-pipeline

## delete serverless function

* start with a dry run
* default region is us-east-1, change if needed using --region argument
* default AWS credential profile is used, change if needed using --profile argument

```
cd resources
python delete-serverlessenv.py --env {YOUR-ENVIRONMENT-NAME} --dry_run
```
* then delete resources
```
python delete-serverlessenv.py --env {YOUR-ENVIRONMENT-NAME}
```
