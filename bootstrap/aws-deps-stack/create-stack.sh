#!/usr/bin/env bash

set -e

script_dir=$(cd "$(dirname "$0")" ; pwd -P)

REPO_NAME=$([[ $(git ls-remote --get-url origin) =~ [\/|\:](.*).git ]] && echo "${BASH_REMATCH[1]}")
aws_profile=data-derp

create-update() {
  pushd "${script_dir}" > /dev/null
    project_name="${1}"
    module_name="${2}"
    github_username="${3}"

    for i in project_name module_name github_username; do
      if [ -z "!{i}" ]; then
        echo "${i} not set. Usage <func> PROJECT_NAME MODULE_NAME GITHUB_USERNAME"
        exit 1
      fi
    done


    token=$(fetch-github-registration-token ${github_username})
    if [ "${token}" == null ]; then
      echo "Token is NULL. Are you sure you entered your Personal Access Token correctly?"
      exit 1
    fi
    create-update-ssm-parameter ${project_name} ${module_name} "${token}"
    create-update-stack ${project_name} ${module_name}
  popd > /dev/null
}

fetch-github-registration-token() {
    username="${1}"

    if [ -z "${username}" ]; then
      echo "USERNAME not set. Usage <func> USERNAME"
      exit 1
    fi

    response=$(curl \
      -u $username \
      -X POST \
      -H "Accept: application/vnd.github.v3+json" \
      https://api.github.com/repos/${REPO_NAME}/actions/runners/registration-token)

    echo $response | jq -r .token
}

create-update-ssm-parameter() {
    project_name="${1}"
    module_name="${2}"
    token="${3}"
    for i in project_name module_name token; do
      if [ -z "!{i}" ]; then
        echo "${i} not set. Usage <func> PROJECT_NAME MODULE_NAME TOKEN"
        exit 1
      fi
    done

    parameter="/${project_name}/${module_name}/github-runner-reg-token"
    if [[ ! $(AWS_PROFILE=${aws_profile} aws ssm get-parameter --name "${parameter}" --region eu-central-1) ]]; then
      echo "Parameter (${parameter}) does not exist. Creating..."
      AWS_PROFILE=${aws_profile} aws ssm put-parameter \
        --name "${parameter}" \
        --value "${token}" \
        --type SecureString \
        --region eu-central-1
    else
      echo "Parameter (${parameter}) exists. Updating..."
      AWS_PROFILE=${aws_profile} aws ssm put-parameter \
        --name "${parameter}" \
        --value "${token}" \
        --overwrite \
        --region eu-central-1
    fi
}

create-update-stack() {
  project_name="${1}"
  module_name="${2}"

  pushd "${script_dir}" > /dev/null
    stack_name="${project_name}-${module_name}-stack"
    if [[ ! $(AWS_PROFILE=${aws_profile}  aws cloudformation describe-stacks --stack-name "${stack_name}" --region eu-central-1) ]]; then
      echo "Stack (${stack_name}) does not exist. Creating..."
      AWS_PROFILE=${aws_profile} aws cloudformation create-stack --stack-name "${stack_name}" \
        --template-body file://./template.yaml \
        --capabilities CAPABILITY_NAMED_IAM \
        --region eu-central-1 \
        --parameters ParameterKey=ProjectName,ParameterValue=${project_name} ParameterKey=ModuleName,ParameterValue=${module_name} ParameterKey=InstanceType,ParameterValue=t3.medium ParameterKey=GithubRepoUrl,ParameterValue=https://github.com/${REPO_NAME}
    else
      echo "Stack (${stack_name}) exists. Creating ChangeSet..."
      now=$(date +%s)
      AWS_PROFILE=${aws_profile} aws cloudformation create-change-set \
        --stack-name "${stack_name}" \
        --change-set-name "update-${now}" \
        --template-body file://./template.yaml \
        --capabilities CAPABILITY_NAMED_IAM \
        --region eu-central-1 \
        --parameters ParameterKey=ProjectName,ParameterValue=${project_name} ParameterKey=ModuleName,ParameterValue=${module_name} ParameterKey=InstanceType,ParameterValue=t3.medium ParameterKey=GithubRepoUrl,ParameterValue=https://github.com/${REPO_NAME}

      echo "Waiting 20 seconds for the ChangeSet to create..."
      sleep 20
      echo "Executing ChangeSet..."
      AWS_PROFILE=${aws_profile} aws cloudformation execute-change-set \
        --change-set-name "update-${now}" \
        --stack-name "${stack_name}" \
        --region eu-central-1
      echo "ChangeSet execution complete."
    fi
  popd > /dev/null

}

project_name="${1}"
module_name="${2}"
github_username="${3}"

for i in project_name module_name github_username; do
  if [ -z "!{i}" ]; then
    echo "${i} not set. Usage <func> PROJECT_NAME MODULE_NAME GITHUB_USERNAME"
    exit 1
  fi
done

create-update ${project_name} ${module_name} ${github_username}
