import urllib.request, urllib.error, json

data = json.dumps({'company_name': 'TestCompany', 'username': 'testuser2', 'email': 'testuser2@example.com', 'password': 'password123'}).encode()
req = urllib.request.Request('https://billway-api-a9ea.onrender.com/api/auth/register/', data=data, headers={'Content-Type': 'application/json'})

try:
    urllib.request.urlopen(req)
    print("Success")
except urllib.error.HTTPError as e:
    print(e.read().decode())
