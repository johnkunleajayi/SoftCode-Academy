import bcrypt
import jwt
import os
import datetime
from dotenv import load_dotenv
from simple_salesforce import Salesforce
from pymongo import MongoClient
from app.state import employee_users  # Import from app.state instead

# Load environment variables from .env file
load_dotenv()

# Load secret key and MongoDB URI from environment variables
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
MONGO_URI = os.getenv('MONGO_URI')

# Setup MongoDB connection
client = MongoClient(MONGO_URI)
db = client.Python  # database name
users_collection = db.users  # collection name

# Salesforce authentication
def authenticate_salesforce():
    try:
        username = os.getenv("SALESFORCE_USERNAME")
        password = os.getenv("SALESFORCE_PASSWORD")
        security_token = os.getenv("SALESFORCE_SECURITY_TOKEN")
        sf = Salesforce(username=username, password=password, security_token=security_token)
        print("Successfully authenticated to Salesforce.")
        return sf
    except Exception as e:
        print(f"Failed to authenticate to Salesforce: {e}")
        return None

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(stored_password: str, provided_password: str) -> bool:
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def generate_jwt(user_id: str) -> str:
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    payload = {'user_id': user_id, 'exp': expiration_time}
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def signup(email: str, password: str, name: str, phone_number: str):
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        raise Exception(f"User with email {email} already exists.")
    
    hashed_password = hash_password(password)
    user_data = {
        'email': email,
        'password': hashed_password,
        'name': name,
        'phone_number': phone_number
    }

    # Insert user into MongoDB
    users_collection.insert_one(user_data)

    # Create employee in Salesforce and store sf_id
    sf = authenticate_salesforce()
    if sf:
        sf_employee = create_employee(sf, name, email, phone_number)
        if sf_employee:
            employee_users[email] = {
                "sf_id": sf_employee["id"],
                "name": name,
                "phone_number": phone_number
            }

    return {"message": "User created successfully!"}

def signin(email: str, password: str):
    user = users_collection.find_one({'email': email})
    if not user or not verify_password(user['password'], password):
        raise Exception("Invalid email or password")
    
    token = generate_jwt(email)
    return {"message": "Signin successful", "token": token}

def create_employee(sf, name, email, phone_number):
    try:
        employee = sf.Student__c.create({
            'Full_Name__c': name,
            'Email__c': email,
            'Phone_Number__c': phone_number
        })
        print(f"Student created in Salesforce with ID: {employee['id']}")
        return employee
    except Exception as e:
        print(f"Error creating employee in Salesforce: {e}")
        return None