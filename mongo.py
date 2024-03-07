from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os

load_dotenv()
mongo_url = os.getenv('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)

db = client['usersdb']

collection = db['users']


async def add_one(first_name, telegram_id, url):
    doc = {
        "first_name": first_name,
        "telegram_id": telegram_id,
        "url": url,
        "schedule": False
    }
    await collection.insert_one(doc)


async def get_url(telegram_id):
    doc = await collection.find_one({"telegram_id": telegram_id})
    return doc.get("url")


async def user_exist(telegram_id):
    return bool(await collection.find_one({"telegram_id": telegram_id}))


async def update_url(telegram_id, new_url):
    result = await collection.update_one({"telegram_id": telegram_id}, {"$set": {"url": new_url}})
    return bool(result.modified_count)


async def is_schedule(telegram_id):
    doc = await collection.find_one({"telegram_id": telegram_id})
    return doc['schedule']


async def update_schedule(telegram_id):
    doc = await collection.find_one({"telegram_id": telegram_id})
    current_schedule = doc.get("schedule")
    await collection.update_one(
        {"telegram_id": telegram_id},
        {"$set": {'schedule': not current_schedule}})
