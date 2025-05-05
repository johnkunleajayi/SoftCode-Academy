import bcrypt
import jwt
import os
import datetime
from dotenv import load_dotenv
from simple_salesforce import Salesforce
from pymongo import MongoClient
from app.employee import create_employee  # Correct import

# Load environment variables
load_dotenv()

# Secret keys and URIs
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
MONGO_URI = os.getenv('MONGO_URI')

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client.Python
users_collection = db.users

# Authenticate Salesforce
def authenticate_salesforce():
    try:
        username = os.getenv("SALESFORCE_USERNAME")
        password = os.getenv("SALESFORCE_PASSWORD")
        security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
        sf = Salesforce(username=username, password=password, security_token=security_token)
        print("✅ Successfully authenticated to Salesforce.")
        return sf
    except Exception as e:
        print(f"❌ Failed to authenticate to Salesforce: {e}")
        return None

# Password hashing
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Password check
def verify_password(stored_password: str, provided_password: str) -> bool:
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

# JWT creation
def generate_jwt(user_id: str) -> str:
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    payload = {'user_id': user_id, 'exp': expiration_time}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# Signup logic
def signup(email: str, password: str, name: str, phone_number: str):
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        raise Exception(f"User with email {email} already exists.")

    hashed_password = hash_password(password)

    # Authenticate to Salesforce
    sf = authenticate_salesforce()
    if not sf:
        raise Exception("Salesforce authentication failed")

    # Create student in Salesforce
    sf_employee = create_employee(sf, name, email, phone_number, password)
    if not sf_employee:
        raise Exception("Failed to create employee in Salesforce")

    # Store user in MongoDB (with Salesforce ID)
    user_data = {
        'email': email,
        'password': hashed_password,
        'name': name,
        'phone_number': phone_number,
        'sf_id': sf_employee['id']
    }
    users_collection.insert_one(user_data)

    return {"message": "User created successfully!"}

# Signin logic
def signin(email: str, password: str):
    user = users_collection.find_one({'email': email})
    if not user or not verify_password(user['password'], password):
        raise Exception("Invalid email or password")

    token = generate_jwt(email)

    return {
        "message": "Signin successful",
        "token": token,
        "user": {
            "email": user["email"],
            "name": user["name"],
            "phone_number": user["phone_number"],
            "sf_id": user.get("sf_id", None)
        }
    }