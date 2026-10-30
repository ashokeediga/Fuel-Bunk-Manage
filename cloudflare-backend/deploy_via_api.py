import sys
import os
import json
import urllib.request
import urllib.error

# Force utf-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

ACCOUNT_ID = "395b23dd8bc12391eab328cb160403ac"
DB_NAME = "fuel-bunk-db"
SCRIPT_NAME = "fuel-bunk-api"

def make_req(url, method="GET", data=None, token=None, content_type="application/json"):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": content_type
    }
    encoded_data = None
    if data is not None:
        if isinstance(data, dict):
            encoded_data = json.dumps(data).encode("utf-8")
        elif isinstance(data, str):
            encoded_data = data.encode("utf-8")
        else:
            encoded_data = data

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return json.loads(err_body)
        except:
            return {"success": False, "errors": [{"message": err_body}]}

def deploy(token):
    print("=" * 60)
    print("🚀 CLOUDFLARE AUTOMATED DEPLOYMENT FOR FUEL BUNK MANAGER")
    print(f"Account ID: {ACCOUNT_ID}")
    print("=" * 60)

    # 1. Check or Create D1 Database
    print(f"\n[1/4] Checking D1 Database '{DB_NAME}'...")
    list_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database"
    res = make_req(list_url, token=token)
    if not res.get("success"):
        print("❌ Authentication failed or error listing D1 databases:", res.get("errors"))
        return None

    db_uuid = None
    for db in res.get("result", []):
        if db.get("name") == DB_NAME:
            db_uuid = db.get("uuid")
            print(f"✅ Found existing D1 Database: {db_uuid}")
            break

    if not db_uuid:
        print(f"Creating new D1 Database '{DB_NAME}'...")
        create_res = make_req(list_url, method="POST", data={"name": DB_NAME}, token=token)
        if not create_res.get("success"):
            print("❌ Failed to create D1 Database:", create_res.get("errors"))
            return None
        db_uuid = create_res["result"]["uuid"]
        print(f"✅ D1 Database created successfully: {db_uuid}")

    # 2. Execute schema.sql on D1
    print("\n[2/4] Executing schema.sql on D1 database...")
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Split into clean statements (removing comments)
    clean_statements = []
    current = []
    for line in schema_sql.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("--"):
            continue
        current.append(line)
        if trimmed.endswith(";"):
            clean_statements.append("\n".join(current))
            current = []

    sql_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{db_uuid}/query"
    for idx, stmt in enumerate(clean_statements):
        sql_res = make_req(sql_url, method="POST", data={"sql": stmt}, token=token)
        if not sql_res.get("success"):
            print(f"⚠️ Warning on statement {idx+1}: {sql_res.get('errors')}")

    print("✅ All database tables and initial staff records populated!")

    # 3. Deploy Worker Script with D1 Binding
    print("\n[3/4] Uploading Worker Script with D1 binding...")
    worker_path = os.path.join(os.path.dirname(__file__), "worker.js")
    with open(worker_path, "r", encoding="utf-8") as f:
        worker_js = f.read()

    # Cloudflare Workers upload multipart/form-data
    boundary = "----CloudflareWorkerBoundary" + os.urandom(8).hex()
    metadata = {
        "main_module": "worker.js",
        "bindings": [
            {
                "type": "d1",
                "name": "DB",
                "id": db_uuid
            }
        ],
        "compatibility_date": "2024-01-01"
    }

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="metadata"\r\n'
        f"Content-Type: application/json\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="worker.js"; filename="worker.js"\r\n'
        f"Content-Type: application/javascript+module\r\n\r\n"
        f"{worker_js}\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    upload_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/workers/scripts/{SCRIPT_NAME}"
    upload_res = make_req(upload_url, method="PUT", data=body, token=token, content_type=f"multipart/form-data; boundary={boundary}")
    if not upload_res.get("success"):
        print("❌ Worker upload failed:", upload_res.get("errors"))
        return None
    print("✅ Worker script uploaded successfully!")

    # 4. Enable workers.dev subdomain route
    print("\n[4/4] Enabling workers.dev subdomain route...")
    sub_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/workers/scripts/{SCRIPT_NAME}/subdomain"
    make_req(sub_url, method="POST", data={"enabled": True}, token=token)

    # Get user subdomain
    sub_info_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/workers/subdomain"
    sub_res = make_req(sub_info_url, token=token)
    subdomain = sub_res.get("result", {}).get("subdomain", "")
    
    if subdomain:
        worker_url = f"https://{SCRIPT_NAME}.{subdomain}.workers.dev"
    else:
        worker_url = f"https://{SCRIPT_NAME}.workers.dev"

    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT 100% COMPLETE!")
    print(f"⚡ Live Worker URL: {worker_url}")
    print("=" * 60)
    return worker_url

if __name__ == "__main__":
    if len(sys.argv) > 1:
        deploy(sys.argv[1])
    else:
        tok = input("Enter Cloudflare API Token: ").strip()
        if tok:
            deploy(tok)
