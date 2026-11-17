#!/usr/bin/env python3
"""
Syncs frontend build assets (index.html, JS, CSS, assets) to Floci S3 website bucket
for a given simulated AWS account.
"""

import os
import sys
import mimetypes
import urllib.request
import xml.etree.ElementTree as ET

def get_frontend_bucket(endpoint_url, account_id):
    headers = {
        'Authorization': f'AWS4-HMAC-SHA256 Credential={account_id}/20261105/us-east-1/s3/aws4_request, SignedHeaders=host, Signature=mock'
    }
    req = urllib.request.Request(f'{endpoint_url}/', headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_data = resp.read().decode('utf-8')
            root = ET.fromstring(xml_data)
            # Namespace handling
            ns = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}
            buckets = root.findall('.//s3:Bucket/s3:Name', ns)
            if not buckets:
                buckets = root.findall('.//Bucket/Name')
            for b in buckets:
                name = b.text
                if '-frontend-' in name:
                    return name
    except Exception as e:
        print(f"Error finding frontend bucket: {e}")
    return None

def upload_file(endpoint_url, account_id, bucket_name, local_path, s3_key):
    content_type, _ = mimetypes.guess_type(local_path)
    if not content_type:
        if local_path.endswith('.js'):
            content_type = 'application/javascript'
        elif local_path.endswith('.css'):
            content_type = 'text/css'
        else:
            content_type = 'application/octet-stream'

    with open(local_path, 'rb') as f:
        data = f.read()

    url = f"{endpoint_url}/{bucket_name}/{s3_key}"
    headers = {
        'Authorization': f'AWS4-HMAC-SHA256 Credential={account_id}/20261105/us-east-1/s3/aws4_request, SignedHeaders=host, Signature=mock',
        'Content-Type': content_type
    }

    req = urllib.request.Request(url, data=data, headers=headers, method='PUT')
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, len(data), content_type

def sync_dist(endpoint_url, account_id, dist_dir, bucket_name=None):
    if not bucket_name:
        bucket_name = get_frontend_bucket(endpoint_url, account_id)
        if not bucket_name:
            print(f"ERROR: No frontend bucket found for account {account_id} at {endpoint_url}")
            sys.exit(1)

    print(f"=== Syncing Frontend to Floci S3 ===")
    print(f"Endpoint:   {endpoint_url}")
    print(f"Account:    {account_id}")
    print(f"Bucket:     {bucket_name}")
    print(f"Dist Dir:   {dist_dir}")

    if not os.path.isdir(dist_dir):
        print(f"ERROR: Directory not found: {dist_dir}")
        sys.exit(1)

    target_accounts = [account_id]
    if account_id != '000000000000':
        # Also ensure bucket and assets are available in default account 000000000000
        # so browser can load index.html and its subresources (JS/CSS) anonymously
        target_accounts.append('000000000000')

    for target_acct in target_accounts:
        # Create bucket if not exists in target account
        try:
            req_b = urllib.request.Request(
                f"{endpoint_url}/{bucket_name}",
                headers={'Authorization': f'AWS4-HMAC-SHA256 Credential={target_acct}/20261105/us-east-1/s3/aws4_request, SignedHeaders=host, Signature=mock'},
                method='PUT'
            )
            urllib.request.urlopen(req_b, timeout=5)
        except Exception:
            pass

        uploaded = 0
        for root, _, files in os.walk(dist_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dist_dir).replace('\\', '/')
                try:
                    status, size, ctype = upload_file(endpoint_url, target_acct, bucket_name, full_path, rel_path)
                    if target_acct == account_id:
                        print(f"  [OK] {rel_path} ({size} bytes, {ctype}) -> HTTP {status}")
                    uploaded += 1
                except Exception as e:
                    print(f"  [FAIL] {rel_path} in account {target_acct}: {e}")
                    sys.exit(1)

    print(f"Successfully uploaded {uploaded} frontend objects to s3://{bucket_name}/ (Accounts: {', '.join(target_accounts)})")

if __name__ == '__main__':
    # Usage: sync_s3_frontend.py [endpoint_url] [account_id] [dist_dir] [optional_bucket_name]
    endpoint = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:4566'
    account = sys.argv[2] if len(sys.argv) > 2 else '111122223333'
    dist = sys.argv[3] if len(sys.argv) > 3 else 'frontend/dist'
    bucket = sys.argv[4] if len(sys.argv) > 4 else None

    sync_dist(endpoint, account, dist, bucket)
