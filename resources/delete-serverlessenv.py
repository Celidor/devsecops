#!/usr/bin/env python
#dry run: python delete-serverlesstraining.py --env {ENVIRONMENT_NAME} --dry_run
#usage: python delete-serverlesstraining.py --env {ENVIRONMENT_NAME}
#optional arguments: --profile (AWS Profile) and --region (AWS Region)
import boto3
import sys
import time
import json
import argparse

from botocore.exceptions import ClientError
from datetime import datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")

class s3:
  def __init__(self, profile, env, dry_run):
    self.profile = profile
    self.env = env
    self.dry_run = dry_run

    self.session = boto3.session.Session(profile_name=self.profile)
    self.client = self.session.client('s3',region_name=region)

    print("Searching for S3 buckets")

    buckets = self.client.list_buckets()['Buckets']
    #print json.dumps(buckets, sort_keys=True, indent=2, default=json_serial)
    for bucket in buckets:
        if bucket['Name'].startswith('serverless-') and self.env in bucket['Name']:
            print("Deleting objects in S3 bucket %s" % (bucket['Name']))
            bucketobjects = self.client.list_objects_v2(Bucket=bucket['Name'])['Contents']
            #print json.dumps(bucketobjects, sort_keys=True, indent=2, default=json_serial)
            for bucketobject in bucketobjects:
                if self.dry_run is None:
                    self.client.delete_object(Bucket=bucket['Name'],Key=bucketobject['Key'])
            print("Deleting S3 bucket %s" % (bucket['Name']))
            if self.dry_run is None:
                self.client.delete_bucket(Bucket=bucket['Name'])

class cloudformation:
  def __init__(self, profile, region, env, dry_run):
    self.profile = profile
    self.region = region
    self.env = env
    self.dry_run = dry_run

    print("Searching for CloudFormation stacks in " + region + " region")
    self.session = boto3.session.Session(profile_name=self.profile, region_name=region)
    self.client = self.session.client('cloudformation', region_name=region)
    stacks = self.client.list_stacks(StackStatusFilter=[
        'CREATE_IN_PROGRESS','CREATE_FAILED','CREATE_COMPLETE','ROLLBACK_IN_PROGRESS',
        'ROLLBACK_FAILED','ROLLBACK_COMPLETE','DELETE_FAILED',
        'UPDATE_IN_PROGRESS','UPDATE_COMPLETE_CLEANUP_IN_PROGRESS','UPDATE_COMPLETE',
        'UPDATE_ROLLBACK_IN_PROGRESS','UPDATE_ROLLBACK_FAILED',
        'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS','UPDATE_ROLLBACK_COMPLETE',
        'REVIEW_IN_PROGRESS',])['StackSummaries']
    #print json.dumps(stacks, sort_keys=True, indent=2, default=json_serial)
    for stack in stacks:
        if stack['StackName'].startswith('serverless-') and self.env in stack['StackName']:
            print("Deleting CloudFormation stack %s in us-east-1 region" % (stack['StackName']))
            if self.dry_run is None:
                self.client.delete_stack(StackName=stack['StackName'])

class iam:
  def __init__(self, profile, env, dry_run):

    self.profile = profile
    self.env = env
    self.dry_run = dry_run

    print("Searching for IAM roles")

    self.session = boto3.session.Session(profile_name=self.profile)
    self.client = self.session.client('iam')

    allroles = []
    allpolicies = []
    allusers = []

    response = self.client.get_account_authorization_details(MaxItems=1000)
    #print json.dumps(response, sort_keys=True, indent=2, default=json_serial)

    allroles = response['RoleDetailList']
    allusers = response['UserDetailList']

    while response['IsTruncated'] == True:
      marker = response['Marker']
      response = self.client.get_account_authorization_details(Marker=marker)
      allroles.extend(response['RoleDetailList'])
      allusers.extend(response['UserDetailList'])

    for role in allroles:
      if role['RoleName'].startswith('serverless-') and self.env in role['RoleName']:
        #print json.dumps(role, sort_keys=True, indent=2, default=json_serial)
        for role_policy in role ['RolePolicyList']:
          print("Delete inline role policy %s from role %s" % (role_policy['PolicyName'], role['RoleName']))
          if self.dry_run is None:
            self.client.delete_role_policy(RoleName=role ['RoleName'], PolicyName= role_policy['PolicyName'])
        for policy in role['AttachedManagedPolicies']:
          print("Detach policy %s from role %s" % (policy['PolicyArn'], role['RoleName']))
          if self.dry_run is None:
            self.client.detach_role_policy(RoleName=role['RoleName'], PolicyArn=policy['PolicyArn'])
        for ip in role['InstanceProfileList']:
          print("Remove role %s from instance profile %s" % (role['RoleName'], ip['InstanceProfileName']))
          if self.dry_run is None:
            self.client.remove_role_from_instance_profile(InstanceProfileName=ip['InstanceProfileName'], RoleName=role['RoleName'])
        print("Delete role %s" % role['RoleName'])
        if self.dry_run is None:
          self.client.delete_role(RoleName=role['RoleName'])


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="Delete AWS Lab")
  parser.add_argument('--profile', required=False, default='default')
  parser.add_argument('--region', required=False, default='us-east-1')
  parser.add_argument('--env', required=True)
  parser.add_argument('--dry_run', action='count')
  args = parser.parse_args()
  profile = args.profile
  region = args.region
  env = args.env
  dry_run = args.dry_run

  s3(profile, env, dry_run)
  cloudformation(profile, region, env, dry_run)
  iam(profile, env, dry_run)
