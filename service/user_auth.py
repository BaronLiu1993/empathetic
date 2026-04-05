from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from bson import ObjectId
from pymongo import AsyncMongoClient
from dotenv import load_dotenv  
import os

load_dotenv()

mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
ph = PasswordHasher(
    time_cost=3,        
    memory_cost=65536, 
    parallelism=4,
    hash_len=32,
    type=2,           
)

def get_mongo_write_client():
    uri = mongo_uri
    client = AsyncMongoClient(uri, readPreference="secondary")
    return client

def hash_password(password: str) -> bytes:
    return ph.hash(password)

def check_password(password: str, hashed: bytes) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False

def create_user(email: str, password: str) -> dict:
    doc = {
        "email": email.lower().strip(),
        "password": hash_password(password),
        "role": "user",
    }

    client = get_mongo_write_client()
    db = client["neuro"]
    collection = db["users"]
    result = collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc