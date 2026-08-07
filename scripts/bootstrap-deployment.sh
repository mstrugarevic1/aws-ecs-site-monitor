#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Create the one-time AWS and GitHub prerequisites for deployment.

Usage:
  AWS_PROFILE=my-profile \
  GITHUB_REPOSITORY=owner/aws-ecs-site-monitor \
  ./scripts/bootstrap-deployment.sh

Required:
  AWS_PROFILE          AWS CLI profile used for every AWS operation.
  GITHUB_REPOSITORY    GitHub repository in owner/name form.

Optional:
  AWS_REGION           AWS region (default: us-east-1).
  GITHUB_ENVIRONMENT   Protected deployment environment (default: aws-dev).
  NAME_PREFIX          AWS resource prefix (default: aws-ecs-site-monitor-dev).
  TF_STATE_BUCKET      Globally unique state bucket name (default includes account ID).
  TF_STATE_KEY         State object key (default: NAME_PREFIX/terraform.tfstate).
  TF_LOCK_TABLE        Terraform lock table (default: NAME_PREFIX-tf-locks).
  DEPLOY_ROLE_NAME     GitHub deployment role (default: NAME_PREFIX-github-deploy).
  BOOTSTRAP_APPROVED   Set to true to skip the interactive confirmation.

The script is idempotent. It creates or updates:
  - an encrypted, versioned, private S3 Terraform-state bucket;
  - a DynamoDB Terraform-lock table;
  - the GitHub Actions OIDC provider and deployment IAM role;
  - the GitHub environment and its non-secret deployment variables.

It never creates access keys or stores AWS credentials. Configure required reviewers
for the GitHub environment in the repository settings after it completes.
EOF
}

fail() {
  echo "error: $*" >&2
  exit 1
}

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  usage
  exit 0
fi
[[ $# -eq 0 ]] || fail "unknown argument: $1 (use --help)"

for command in aws gh; do
  command -v "$command" >/dev/null || fail "$command is required"
done

AWS_REGION=${AWS_REGION:-us-east-1}
GITHUB_ENVIRONMENT=${GITHUB_ENVIRONMENT:-aws-dev}
NAME_PREFIX=${NAME_PREFIX:-aws-ecs-site-monitor-dev}
GITHUB_REPOSITORY=${GITHUB_REPOSITORY:-}

[[ -n ${AWS_PROFILE:-} ]] || fail "AWS_PROFILE is required"
[[ $GITHUB_REPOSITORY =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || fail "GITHUB_REPOSITORY must be owner/name"
[[ $AWS_REGION =~ ^[a-z0-9-]+$ ]] || fail "AWS_REGION contains invalid characters"
[[ $GITHUB_ENVIRONMENT =~ ^[A-Za-z0-9_.-]+$ ]] || fail "GITHUB_ENVIRONMENT contains invalid characters"
[[ $NAME_PREFIX =~ ^[a-z0-9][a-z0-9-]{1,26}[a-z0-9]$ ]] || fail "NAME_PREFIX must be 3-28 lowercase letters, numbers, or hyphens"

aws_args=(--region "$AWS_REGION" --profile "$AWS_PROFILE")

account_id=$(aws "${aws_args[@]}" sts get-caller-identity --query Account --output text)
[[ $account_id =~ ^[0-9]{12}$ ]] || fail "AWS did not return a valid account ID"
gh auth status >/dev/null
gh repo view "$GITHUB_REPOSITORY" >/dev/null

TF_STATE_BUCKET=${TF_STATE_BUCKET:-"${NAME_PREFIX}-${account_id}-tfstate"}
TF_STATE_KEY=${TF_STATE_KEY:-"${NAME_PREFIX}/terraform.tfstate"}
TF_LOCK_TABLE=${TF_LOCK_TABLE:-"${NAME_PREFIX}-tf-locks"}
DEPLOY_ROLE_NAME=${DEPLOY_ROLE_NAME:-"${NAME_PREFIX}-github-deploy"}

[[ $TF_STATE_BUCKET =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]] || fail "TF_STATE_BUCKET is not a valid S3 bucket name"
[[ $TF_LOCK_TABLE =~ ^[A-Za-z0-9_.-]{3,255}$ ]] || fail "TF_LOCK_TABLE is not a valid DynamoDB table name"
[[ $DEPLOY_ROLE_NAME =~ ^[A-Za-z0-9+=,.@_-]{1,64}$ ]] || fail "DEPLOY_ROLE_NAME is not a valid IAM role name"

if [[ ${BOOTSTRAP_APPROVED:-false} != "true" ]]; then
  [[ -t 0 ]] || fail "set BOOTSTRAP_APPROVED=true for non-interactive use"
  echo "This will create or update deployment prerequisites in AWS region $AWS_REGION and GitHub environment $GITHUB_ENVIRONMENT."
  read -r -p "Continue? [y/N] " answer
  [[ $answer == "y" || $answer == "Y" ]] || exit 0
fi

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

if ! aws "${aws_args[@]}" s3api head-bucket --bucket "$TF_STATE_BUCKET" 2>/dev/null; then
  if [[ $AWS_REGION == "us-east-1" ]]; then
    aws "${aws_args[@]}" s3api create-bucket --bucket "$TF_STATE_BUCKET" >/dev/null
  else
    aws "${aws_args[@]}" s3api create-bucket \
      --bucket "$TF_STATE_BUCKET" \
      --create-bucket-configuration "LocationConstraint=$AWS_REGION" >/dev/null
  fi
fi

aws "${aws_args[@]}" s3api put-public-access-block \
  --bucket "$TF_STATE_BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws "${aws_args[@]}" s3api put-bucket-encryption \
  --bucket "$TF_STATE_BUCKET" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws "${aws_args[@]}" s3api put-bucket-versioning \
  --bucket "$TF_STATE_BUCKET" \
  --versioning-configuration Status=Enabled

if ! aws "${aws_args[@]}" dynamodb describe-table --table-name "$TF_LOCK_TABLE" >/dev/null 2>&1; then
  aws "${aws_args[@]}" dynamodb create-table \
    --table-name "$TF_LOCK_TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST >/dev/null
fi
aws "${aws_args[@]}" dynamodb wait table-exists --table-name "$TF_LOCK_TABLE"

oidc_arn="arn:aws:iam::${account_id}:oidc-provider/token.actions.githubusercontent.com"
if ! aws "${aws_args[@]}" iam get-open-id-connect-provider \
  --open-id-connect-provider-arn "$oidc_arn" >/dev/null 2>&1; then
  aws "${aws_args[@]}" iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com >/dev/null
elif [[ $(aws "${aws_args[@]}" iam get-open-id-connect-provider \
  --open-id-connect-provider-arn "$oidc_arn" \
  --query "contains(ClientIDList, 'sts.amazonaws.com')" \
  --output text) != "True" ]]; then
  aws "${aws_args[@]}" iam add-client-id-to-open-id-connect-provider \
    --open-id-connect-provider-arn "$oidc_arn" \
    --client-id sts.amazonaws.com
fi

cat >"$tmp_dir/trust-policy.json" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "$oidc_arn"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:$GITHUB_REPOSITORY:environment:$GITHUB_ENVIRONMENT"
      }
    }
  }]
}
EOF

if aws "${aws_args[@]}" iam get-role --role-name "$DEPLOY_ROLE_NAME" >/dev/null 2>&1; then
  aws "${aws_args[@]}" iam update-assume-role-policy \
    --role-name "$DEPLOY_ROLE_NAME" \
    --policy-document "file://$tmp_dir/trust-policy.json"
else
  aws "${aws_args[@]}" iam create-role \
    --role-name "$DEPLOY_ROLE_NAME" \
    --description "GitHub Actions deployment role for $GITHUB_REPOSITORY" \
    --assume-role-policy-document "file://$tmp_dir/trust-policy.json" >/dev/null
fi

cat >"$tmp_dir/deploy-policy.json" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "TerraformStateBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket", "s3:GetBucketLocation", "s3:GetBucketVersioning"],
      "Resource": "arn:aws:s3:::$TF_STATE_BUCKET"
    },
    {
      "Sid": "TerraformStateObjects",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::$TF_STATE_BUCKET/$TF_STATE_KEY"
    },
    {
      "Sid": "TerraformStateLock",
      "Effect": "Allow",
      "Action": ["dynamodb:DescribeTable", "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem"],
      "Resource": "arn:aws:dynamodb:$AWS_REGION:$account_id:table/$TF_LOCK_TABLE"
    },
    {
      "Sid": "ApplicationInfrastructure",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:*", "dynamodb:*", "ec2:*", "ecr:*", "ecs:*",
        "elasticloadbalancing:*", "events:*", "logs:*", "sns:*", "sqs:*",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    },
    {
      "Sid": "ApplicationRoles",
      "Effect": "Allow",
      "Action": [
        "iam:AttachRolePolicy", "iam:CreateRole", "iam:DeleteRole",
        "iam:DeleteRolePolicy", "iam:DetachRolePolicy", "iam:GetRole",
        "iam:GetRolePolicy", "iam:ListAttachedRolePolicies", "iam:ListRolePolicies",
        "iam:PutRolePolicy", "iam:TagRole", "iam:UntagRole",
        "iam:UpdateAssumeRolePolicy"
      ],
      "Resource": "arn:aws:iam::$account_id:role/$NAME_PREFIX-*"
    },
    {
      "Sid": "PassApplicationRoles",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::$account_id:role/$NAME_PREFIX-*",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": ["ecs-tasks.amazonaws.com", "events.amazonaws.com"]
        }
      }
    },
    {
      "Sid": "CreateRequiredServiceLinkedRoles",
      "Effect": "Allow",
      "Action": "iam:CreateServiceLinkedRole",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "iam:AWSServiceName": ["ecs.amazonaws.com", "elasticloadbalancing.amazonaws.com"]
        }
      }
    },
    {
      "Sid": "ReadEcsExecutionPolicy",
      "Effect": "Allow",
      "Action": ["iam:GetPolicy", "iam:GetPolicyVersion"],
      "Resource": "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
    }
  ]
}
EOF

aws "${aws_args[@]}" iam put-role-policy \
  --role-name "$DEPLOY_ROLE_NAME" \
  --policy-name "${NAME_PREFIX}-deploy" \
  --policy-document "file://$tmp_dir/deploy-policy.json"

role_arn=$(aws "${aws_args[@]}" iam get-role \
  --role-name "$DEPLOY_ROLE_NAME" \
  --query Role.Arn \
  --output text)

gh api --method PUT "repos/$GITHUB_REPOSITORY/environments/$GITHUB_ENVIRONMENT" >/dev/null
for variable in AWS_REGION TF_STATE_BUCKET TF_STATE_KEY TF_LOCK_TABLE NAME_PREFIX; do
  gh variable set "$variable" \
    --repo "$GITHUB_REPOSITORY" \
    --env "$GITHUB_ENVIRONMENT" \
    --body "${!variable}"
done
gh variable set AWS_DEPLOY_ROLE_ARN \
  --repo "$GITHUB_REPOSITORY" \
  --env "$GITHUB_ENVIRONMENT" \
  --body "$role_arn"

echo "Bootstrap complete. Configure required reviewers for the '$GITHUB_ENVIRONMENT' GitHub environment."
