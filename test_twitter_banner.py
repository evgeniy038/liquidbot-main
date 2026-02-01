#!/usr/bin/env python3
import requests
import json

url = "https://api.twitterapi.io/twitter/user/info?userName=lumincrypto"
headers = {"X-API-Key": "8d093b1757e14ac8b11fb1790150a127"}

print("Fetching Twitter profile...")
response = requests.get(url, headers=headers, timeout=10)
data = response.json()

if data.get("status") == "success":
    user = data.get("data", {})
    print("\n✅ Success!")
    print(f"Name: {user.get('name')}")
    print(f"Username: @{user.get('userName')}")
    print(f"Followers: {user.get('followers')}")
    print(f"Profile Picture: {user.get('profilePicture')}")
    print(f"Banner URL: {user.get('coverPicture')}")
    print(f"Blue Verified: {user.get('isBlueVerified')}")
else:
    print(f"\n❌ Error: {data}")
