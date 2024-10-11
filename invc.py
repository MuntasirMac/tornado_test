import json
from io import BytesIO
from time import time
from datetime import datetime
from dbconnection import connect_db
from bson import ObjectId, json_util
import re

db = connect_db()
print((db.list_collection_names()))

# Load data from Postman-exported JSON file
with open("/home/muntasir/wals.json", "r") as file:
    data = json.load(file, object_hook=json_util.object_hook)

# Convert BSON types to native Python types
cleaned_data = json.loads(json.dumps(data, default=json_util.default))

# Print or further process the cleaned data
# print(type(cleaned_data['data']))
# res = db.wallets.insert_many(cleaned_data['data'])

for data in cleaned_data.get('data'):
    data['_id'] = ObjectId(data['_id']['$oid'])
    data['organization'] = ObjectId(data['organization']['$oid'])
    data['created_on'] = data['created_on']['$date']
    data['modified_on'] = data['modified_on']['$date']
    if 'wallet_add_history' in data:
        for h in data.get('wallet_add_history'):
            h['modified_on'] = h['modified_on']['$date']
    if 'wallet_deduction_history' in data:
        for h in data.get('wallet_deduction_history'):
            h['modified_on'] = h['modified_on']['$date']
    # print(data['_id'], data['wallet_deduction_history'])
    # print(data['_id'])
    # data['last_received_date'] = data.get('last_received_date')
    db.wallets.insert_one(data)
# print(cleaned_data)