from pymongo import MongoClient
# from motor.motor_asyncio import AsyncIOMotorClient
# from motor.motor_tornado import MotorClient


def connect_db(name=None):
    client = MongoClient('mongodb://localhost:27017')
    if not name:
        # db = client.get_database('tor_test')
        db = client.get_database('chbxdb')
    else:
        db = client.get_database(name)

    return db

# def connect_motor():
#     # client = connect_db()
#     motor_client = MotorClient('mongodb://localhost: 27017')

#     return motor_client.tor_test