import boto3
import json
import argparse
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Configuración ──────────────────────────────────────────────
REGION = "us-east-1"
ACCOUNT_ID = "962682390364"
IDENTITY_STORE_ID = "d-90660420e7"
INSTANCE_ARN = "arn:aws:sso:::instance/ssoins-72231b2f3daa0b55"

DEVELOPER_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "CloudFormation",
            "Effect": "Allow",
            "Action": ["cloudformation:*"],
            "Resource": "*"
        },
        {
            "Sid": "Lambda",
            "Effect": "Allow",
            "Action": ["lambda:*"],
            "Resource": "*"
        },
        {
            "Sid": "DynamoDB",
            "Effect": "Allow",
            "Action": ["dynamodb:*"],
            "Resource": "*"
        },
        {
            "Sid": "IAM",
            "Effect": "Allow",
            "Action": [
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:AttachRolePolicy",
                "iam:DetachRolePolicy",
                "iam:PutRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:GetRole",
                "iam:GetRolePolicy",
                "iam:ListRoles",
                "iam:ListRolePolicies",
                "iam:ListAttachedRolePolicies",
                "iam:PassRole",
                "iam:TagRole",
                "iam:UntagRole"
            ],
            "Resource": "*"
        },
        {
            "Sid": "APIGateway",
            "Effect": "Allow",
            "Action": ["apigateway:*"],
            "Resource": "*"
        },
        {
            "Sid": "CloudWatchLogs",
            "Effect": "Allow",
            "Action": ["logs:*"],
            "Resource": "*"
        },
        {
            "Sid": "XRay",
            "Effect": "Allow",
            "Action": ["xray:*"],
            "Resource": "*"
        },
        {
            "Sid": "S3",
            "Effect": "Allow",
            "Action": ["s3:*"],
            "Resource": "*"
        }
    ]
}
# ──────────────────────────────────────────────────────────────


def get_or_create(label, find_fn, create_fn):
    result = find_fn()
    if result:
        print(f"  [~] {label} ya existe: {result}")
        return result
    result = create_fn()
    print(f"  [+] {label} creado: {result}")
    return result


# ── Identity Store (usuarios y grupos) ────────────────────────

def find_user(ids, username):
    users = ids.list_users(
        IdentityStoreId=IDENTITY_STORE_ID,
        Filters=[{"AttributePath": "UserName", "AttributeValue": username}]
    )["Users"]
    return users[0]["UserId"] if users else None


def find_group(ids, name):
    groups = ids.list_groups(
        IdentityStoreId=IDENTITY_STORE_ID,
        Filters=[{"AttributePath": "DisplayName", "AttributeValue": name}]
    )["Groups"]
    return groups[0]["GroupId"] if groups else None


def create_group(ids, name, description):
    return ids.create_group(
        IdentityStoreId=IDENTITY_STORE_ID,
        DisplayName=name,
        Description=description
    )["GroupId"]


def add_member(ids, group_id, user_id, label):
    members = ids.list_group_memberships(
        IdentityStoreId=IDENTITY_STORE_ID,
        GroupId=group_id
    )["GroupMemberships"]
    if any(m["MemberId"]["UserId"] == user_id for m in members):
        print(f"  [~] {label} ya es miembro del grupo")
        return
    ids.create_group_membership(
        IdentityStoreId=IDENTITY_STORE_ID,
        GroupId=group_id,
        MemberId={"UserId": user_id}
    )
    print(f"  [+] {label} agregado al grupo")


# ── Permission Sets ────────────────────────────────────────────

def find_permission_set(sso, name):
    paginator = sso.get_paginator("list_permission_sets")
    for page in paginator.paginate(InstanceArn=INSTANCE_ARN):
        for arn in page["PermissionSets"]:
            ps = sso.describe_permission_set(InstanceArn=INSTANCE_ARN, PermissionSetArn=arn)["PermissionSet"]
            if ps["Name"] == name:
                return arn
    return None


def create_permission_set(sso, name, description):
    return sso.create_permission_set(
        InstanceArn=INSTANCE_ARN,
        Name=name,
        Description=description,
        SessionDuration="PT8H"
    )["PermissionSet"]["PermissionSetArn"]


def put_inline_policy(sso, ps_arn, policy):
    sso.put_inline_policy_to_permission_set(
        InstanceArn=INSTANCE_ARN,
        PermissionSetArn=ps_arn,
        InlinePolicy=json.dumps(policy)
    )
    print(f"  [+] Inline policy aplicada")


# ── Account Assignments ────────────────────────────────────────

def assign_group_to_account(sso, group_id, ps_arn, label):
    assignments = sso.list_account_assignments(
        InstanceArn=INSTANCE_ARN,
        AccountId=ACCOUNT_ID,
        PermissionSetArn=ps_arn
    )["AccountAssignments"]
    if any(a["PrincipalId"] == group_id for a in assignments):
        print(f"  [~] {label} ya tiene asignación en la cuenta")
        return
    sso.create_account_assignment(
        InstanceArn=INSTANCE_ARN,
        TargetId=ACCOUNT_ID,
        TargetType="AWS_ACCOUNT",
        PermissionSetArn=ps_arn,
        PrincipalType="GROUP",
        PrincipalId=group_id
    )
    print(f"  [+] {label} asignado a la cuenta")
    time.sleep(2)  # propagación


# ── Main ───────────────────────────────────────────────────────

def main(profile):
    session = boto3.Session(profile_name=profile, region_name=REGION)
    sso = session.client("sso-admin")
    ids = session.client("identitystore")

    print("\n── Usuarios ──────────────────────────────────────────")
    admin_user_id = find_user(ids, "admin-sso")
    dev_user_id = find_user(ids, "developer")
    print(f"  admin-sso  → {admin_user_id}")
    print(f"  developer  → {dev_user_id}")

    print("\n── Permission Sets ───────────────────────────────────")
    admin_ps_arn = get_or_create(
        "AdministratorAccess",
        lambda: find_permission_set(sso, "AdministratorAccess"),
        lambda: None  # ya existe por defecto en Identity Center
    )
    dev_ps_arn = get_or_create(
        "DeveloperAccess",
        lambda: find_permission_set(sso, "DeveloperAccess"),
        lambda: create_permission_set(sso, "DeveloperAccess", "Permisos para deploy y desarrollo del proyecto")
    )
    put_inline_policy(sso, dev_ps_arn, DEVELOPER_POLICY)

    print("\n── Grupos ────────────────────────────────────────────")
    admin_group_id = get_or_create(
        "Grupo Administrators",
        lambda: find_group(ids, "Administrators"),
        lambda: create_group(ids, "Administrators", "Administradores de la cuenta")
    )
    dev_group_id = get_or_create(
        "Grupo Developers",
        lambda: find_group(ids, "Developers"),
        lambda: create_group(ids, "Developers", "Desarrolladores del proyecto")
    )

    print("\n── Membresías ────────────────────────────────────────")
    add_member(ids, admin_group_id, admin_user_id, "admin-sso")
    add_member(ids, dev_group_id, dev_user_id, "developer")

    print("\n── Asignaciones a la cuenta ──────────────────────────")
    assign_group_to_account(sso, admin_group_id, admin_ps_arn, "Administrators")
    assign_group_to_account(sso, dev_group_id, dev_ps_arn, "Developers")

    print("\n── Resumen ───────────────────────────────────────────")
    print(f"""
  Identity Center: {IDENTITY_STORE_ID}
  Cuenta: {ACCOUNT_ID}

  Grupo Administrators
  ├── Miembro : admin-sso
  └── Rol     : AdministratorAccess

  Grupo Developers
  ├── Miembro : developer
  └── Rol     : DeveloperAccess

  Perfiles CLI:
  ├── --profile AdministratorAccess-962682390364  → admin-sso
  └── --profile developer                         → developer
    """)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()
    main(args.profile)
