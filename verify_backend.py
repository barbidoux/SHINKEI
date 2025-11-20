import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def post(url, data, token=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), method='POST')
    req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        sys.exit(1)

# 1. Login
print("Logging in...")
login_resp = post(f"{BASE_URL}/auth/login", {"email": "test@example.com", "password": "dev-password"})
token = login_resp["access_token"]
print(f"Token obtained: {token[:10]}...")

# 2. Create World
print("Creating World...")
world_resp = post(f"{BASE_URL}/worlds", {"name": "PyVerify World", "description": "Created by verification script"}, token)
world_id = world_resp["id"]
print(f"World created: {world_id}")

# 3. Create Story
print("Creating Story...")
story_resp = post(f"{BASE_URL}/worlds/{world_id}/stories", {"title": "PyVerify Story", "synopsis": "Testing story creation"}, token)
story_id = story_resp["id"]
print(f"Story created: {story_id}")

# 4. Create Beat
print("Creating Beat...")
beat_resp = post(f"{BASE_URL}/stories/{story_id}/beats", {"title": "First Beat", "content": "This is the first beat."}, token)
beat_id = beat_resp["id"]
print(f"Beat created: {beat_id}")

print("VERIFICATION SUCCESSFUL")
