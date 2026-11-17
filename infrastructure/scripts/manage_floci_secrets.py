#!/usr/bin/env python3
"""
Hotel Billing System - Floci Secrets Manager Bootstrap & Verification Utility
Manages environment secrets across simulated AWS accounts in Floci:
  - Development Account (111122223333): billing-dev/app-secrets
  - QA Account (444455556666):          billing-qa/app-secrets
  - Production Account (777788889999):  billing-prod/app-secrets
"""

import sys
import json
import urllib.request
import urllib.error

DEFAULT_ENDPOINT = "http://localhost:4566"

ENV_SECRETS = {
    "develop": {
        "account_id": "111122223333",
        "secret_name": "billing-dev/app-secrets",
        "region": "us-east-1",
        "description": "Hotel Billing System - Development Secrets",
        "data": {
            "environment": "develop",
            "aws_account_id": "111122223333",
            "spring.datasource.url": "jdbc:postgresql://postgres:5432/hotel_billing_dev",
            "spring.datasource.username": "postgres",
            "spring.datasource.password": "postgres_dev",
            "jwt.secret": "5367566B59703373367639792F423F4528482B4D6251655468576D5A71347437",
            "jwt.expiration": "86400000",
            "app.frontend.url": "http://localhost:3001",
            "app.backend.url": "http://localhost:8084",
            "app.invoice.base-url": "http://localhost:3001/invoice"
        }
    },
    "qa": {
        "account_id": "444455556666",
        "secret_name": "billing-qa/app-secrets",
        "region": "us-east-1",
        "description": "Hotel Billing System - QA Secrets",
        "data": {
            "environment": "qa",
            "aws_account_id": "444455556666",
            "spring.datasource.url": "jdbc:postgresql://postgres:5432/hotel_billing_qa",
            "spring.datasource.username": "postgres",
            "spring.datasource.password": "postgres_qa",
            "jwt.secret": "6478677C6A814484478740803053405639593C5E7362766579687E6B82458548",
            "jwt.expiration": "43200000",
            "app.frontend.url": "http://localhost:3002",
            "app.backend.url": "http://localhost:8086",
            "app.invoice.base-url": "http://localhost:3002/invoice"
        }
    },
    "prod": {
        "account_id": "777788889999",
        "secret_name": "billing-prod/app-secrets",
        "region": "us-east-1",
        "description": "Hotel Billing System - Production Secrets",
        "data": {
            "environment": "prod",
            "aws_account_id": "777788889999",
            "spring.datasource.url": "jdbc:postgresql://postgres:5432/hotel_billing_prod",
            "spring.datasource.username": "postgres",
            "spring.datasource.password": "postgres_prod",
            "jwt.secret": "7589788D7B925595589851914164516740604D6F8473877680798F7C93569659",
            "jwt.expiration": "28800000",
            "app.frontend.url": "http://localhost:3003",
            "app.backend.url": "http://localhost:8088",
            "app.invoice.base-url": "http://localhost:3003/invoice"
        }
    }
}

def send_secretsmanager_request(endpoint, account_id, region, target, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint if endpoint.endswith("/") else endpoint + "/",
        data=data,
        headers={
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": f"secretsmanager.{target}",
            "Authorization": f"AWS4-HMAC-SHA256 Credential={account_id}/20261105/{region}/secretsmanager/aws4_request, SignedHeaders=content-type;host;x-amz-target, Signature=dummy"
        }
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))

def sync_secrets(endpoint=DEFAULT_ENDPOINT):
    print(f"=== Syncing Floci Secrets Manager at {endpoint} ===")
    for env, config in ENV_SECRETS.items():
        account_id = config["account_id"]
        secret_name = config["secret_name"]
        region = config["region"]
        data = config["data"]

        # 1. Try to create the secret
        try:
            res = send_secretsmanager_request(
                endpoint,
                account_id,
                region,
                "CreateSecret",
                {
                    "Name": secret_name,
                    "Description": config["description"],
                    "SecretString": json.dumps(data)
                }
            )
            print(f"[{env.upper()}] Created secret: {res.get('ARN')}")
        except urllib.error.HTTPError as he:
            # If already exists (ResourceExistsException), update it
            try:
                res = send_secretsmanager_request(
                    endpoint,
                    account_id,
                    region,
                    "PutSecretValue",
                    {
                        "SecretId": secret_name,
                        "SecretString": json.dumps(data)
                    }
                )
                print(f"[{env.upper()}] Updated existing secret: {res.get('ARN', secret_name)}")
            except Exception as e:
                print(f"[{env.upper()}] Error updating secret: {e}")

def verify_secrets(endpoint=DEFAULT_ENDPOINT, target_env=None):
    print(f"\n=== Verifying Secrets Across Multi-Account Floci Namespaces ===")
    all_ok = True
    targets = {target_env: ENV_SECRETS[target_env]} if target_env and target_env in ENV_SECRETS else ENV_SECRETS
    for env, config in targets.items():
        account_id = config["account_id"]
        secret_name = config["secret_name"]
        region = config["region"]

        try:
            res = send_secretsmanager_request(
                endpoint,
                account_id,
                region,
                "GetSecretValue",
                {"SecretId": secret_name}
            )
            arn = res.get("ARN")
            secret_data = json.loads(res.get("SecretString", "{}"))
            print(f"[{env.upper()}] Status: OK")
            print(f"  Account:    {account_id}")
            print(f"  Secret ARN: {arn}")
            print(f"  DB URL:     {secret_data.get('spring.datasource.url')}")
            print(f"  JWT Secret: {secret_data.get('jwt.secret')[:16]}... (Length: {len(secret_data.get('jwt.secret', ''))})")
        except Exception as e:
            print(f"[{env.upper()}] Verification FAILED: {e}")
            all_ok = False
    return all_ok

if __name__ == "__main__":
    ep = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ENDPOINT
    target_env = sys.argv[2] if len(sys.argv) > 2 else None
    sync_secrets(ep)
    ok = verify_secrets(ep, target_env)
    if not ok:
        sys.exit(1)
    print("All required Secrets Manager secrets verified successfully.")
