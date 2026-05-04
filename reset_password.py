import requests

BASE = "http://localhost:8080"

r = requests.post(
    f"{BASE}/realms/master/protocol/openid-connect/token",
    data={"grant_type":"password","client_id":"admin-cli","username":"admin","password":"admin123"}
)
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

r = requests.get(f"{BASE}/admin/realms/zerotrust/users?username=testuser", headers=H)
users = r.json()
user_id = users[0]["id"]
print(f"OK user_id={user_id}")

r = requests.put(f"{BASE}/admin/realms/zerotrust/users/{user_id}/reset-password",
    headers=H, json={"type":"password","value":"testpass123","temporary":False})
print(f"Reset password: {r.status_code}")

r = requests.post(f"{BASE}/realms/zerotrust/protocol/openid-connect/token",
    data={"grant_type":"password","client_id":"zerotrust-backend",
          "client_secret":"69IouOOmUceYG8fgZOQbrQvnIkB6h4kR",
          "username":"testuser","password":"testpass123"})
result = r.json()
if "access_token" in result:
    print(f"TOKEN OK: {result['access_token'][:80]}...")
else:
    print(f"ERREUR: {result}")
