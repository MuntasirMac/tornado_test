from pymongo import MongoClient
# from motor.motor_asyncio import AsyncIOMotorClient
# from motor.motor_tornado import MotorClient


def connect_db():
    client = MongoClient('mongodb://localhost:27017')
    db = client.get_database('tor_test')

    return db

# def connect_motor():
#     # client = connect_db()
#     motor_client = MotorClient('mongodb://localhost: 27017')

#     return motor_client.tor_test