import os
from dotenv import load_dotenv
from box_sdk_gen import BoxClient, BoxDeveloperTokenAuth

load_dotenv()

token = os.getenv("BOX_DEVELOPER_TOKEN")
print(f"Token: {token[:20]}...")

auth = BoxDeveloperTokenAuth(token=token)
client = BoxClient(auth=auth)

# Test: Get user info
user = client.users.get_user_me()
print(f"Connected as: {user.name}")