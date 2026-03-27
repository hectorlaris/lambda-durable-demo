import boto3
import json
import argparse

# ── Configuración ──────────────────────────────────────────────
REGION = "us-east-1"

parser = argparse.ArgumentParser()
parser.add_argument("--profile", default=None)
args = parser.parse_args()

session = boto3.Session(profile_name=args.profile, region_name=REGION)

USER = {
    "UserName": "developer",
    "DisplayName": "Developer",
    "Emails": [{"Value": "hectorlaris.architect@gmail.com", "Type": "work", "Primary": True}],
    "Name": {"GivenName": "Developer", "FamilyName": "Serrano"},
}
# ──────────────────────────────────────────────────────────────


def get_identity_store_id():
    sso = session.client("sso-admin")
    instances = sso.list_instances()["Instances"]
    if not instances:
        raise RuntimeError("No IAM Identity Center instance found in this account/region.")
    return instances[0]["IdentityStoreId"]


def create_user(identity_store_id: str):
    ids = session.client("identitystore")

    # Verificar si ya existe
    existing = ids.list_users(
        IdentityStoreId=identity_store_id,
        Filters=[{"AttributePath": "UserName", "AttributeValue": USER["UserName"]}],
    )["Users"]

    if existing:
        print(f"[!] El usuario '{USER['UserName']}' ya existe: {existing[0]['UserId']}")
        return existing[0]

    response = ids.create_user(
        IdentityStoreId=identity_store_id,
        UserName=USER["UserName"],
        DisplayName=USER["DisplayName"],
        Emails=USER["Emails"],
        Name=USER["Name"],
    )

    print(f"[✓] Usuario creado exitosamente")
    print(json.dumps(response, indent=2, default=str))
    return response


if __name__ == "__main__":
    identity_store_id = get_identity_store_id()
    print(f"[i] IdentityStoreId: {identity_store_id}")
    create_user(identity_store_id)
