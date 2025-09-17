import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "bingo_db")

client = AsyncIOMotorClient(MONGODB_URL)
db = client[MONGO_DB_NAME]


async def get_db():
    yield db
