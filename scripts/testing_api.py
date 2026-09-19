import requests

base_url = "http://127.0.0.1:8000/api"

# Language Setting
response = requests.post(f"{base_url}/set_language", json={"lang": "ar"})
print(response.json())

# Login
response = requests.post(f"{base_url}/login", json={"username": "testuser@example.com", "password": "password123"})
print(response.json())

# Signup
response = requests.post(f"{base_url}/signup", json={
    "username": "newuser@example.com",
    "password": "password123",
    "full_name": "New User",
    "mobile": "1234567890",
    "address": "123 Test Street"
})
print(response.json())

# Logout
response = requests.post(f"{base_url}/logout")
print(response.json())
