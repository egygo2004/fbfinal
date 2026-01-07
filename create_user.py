from appwrite.client import Client
from appwrite.services.users import Users
import os

# Configuration (using values from previous context or hardcoded if necessary for this specific run)
# Note: In a real environment, these should come from os.environ
# I will try to read them from the environment or fallback to what I see in the code
PROJECT_ID = '67645b73003020610f60' # Found in previous logs/code
API_KEY = os.environ.get('APPWRITE_API_KEY') 
ENDPOINT = 'https://cloud.appwrite.io/v1'

if not API_KEY:
    # Try to find it in a local .env file or python file if possible
    # For now, I'll ask the user to provide it if I can't find it, BUT
    # I recall seeing appwrite_worker.py. Let's assume the user runs this where env vars are set
    # or I will try to fetch it from a file if I can find one.
    # Actually, I'll rely on the user having it or hardcode it if I found it previously.
    # I don't have the API KEY in plain text in the history I can see easily right now.
    # However, I can look at appwrite_config.py or similar if it exists.
    pass

def create_user():
    client = Client()
    client.set_endpoint(ENDPOINT)
    client.set_project(PROJECT_ID)
    client.set_key(os.environ.get('APPWRITE_API_KEY')) # Needs to be set in terminal

    users = Users(client)

    email = "lolelarap@gmail.com"
    password = "lolelarap"
    name = "Lolelarap"

    try:
        # Check if user exists (by trying to create)
        result = users.create(
            user_id='unique()',
            email=email,
            password=password,
            name=name
        )
        print(f"✅ User {email} created successfully!")
        print(f"ID: {result['$id']}")
    except Exception as e:
        print(f"❌ Error creating user: {e}")

if __name__ == "__main__":
    if not os.environ.get('APPWRITE_API_KEY'):
        print("⚠️ Please set APPWRITE_API_KEY environment variable before running.")
    else:
        create_user()
