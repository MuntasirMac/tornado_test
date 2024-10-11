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
with open("/home/muntasir/users.json", "r") as file:
    data = json.load(file, object_hook=json_util.object_hook)

# Convert BSON types to native Python types
cleaned_data = json.loads(json.dumps(data, default=json_util.default))

# Print or further process the cleaned data
# print(type(cleaned_data['data']))
# res = db.wallets.insert_many(cleaned_data['data'])
now = datetime.now()

for data in cleaned_data.get('data'):
    data['_id'] = ObjectId(data['_id']['$oid'])
    data['organization'] = data['organization']['$oid']
    # data['assigned_org'] = data['assigned_org']['$oid'] if 'assigned_org' in data else ''
    # data['created_by_organization'] = data['created_by_organization']['$oid'] if 'created_by_organization' in data else ''
    data['created_on'] = data['created_on']['$date'] if 'created_on' in data else now
    # data['modified_on'] = data['modified_on']['$date'] if 'modified_on' else now
    # data['placed_on'] = data['placed_on']['$date'] if 'placed_on' in data else now
    # data['time_delivered'] = data['time_delivered']['$date'] if 'time_delivered' in data else now
    # data['delivery_date_time'] = data['delivery_date_time']['$date'] if 'delivery_date_time' in data else now
    if 'received_history' in data and data['received_history'] != []:
        for h in data.get('received_history'):
            h['received_date'] = h['received_date']['$date'] if 'received_date' in h else now
            h['received_entry_date'] = h['received_entry_date']['$date'] if 'received_entry_date' in h else now
    if 'payment_history' in data and data['payment_history'] != []:
        for h in data.get('payment_history'):
            h['received_date'] = h['received_date']['$date'] if 'received_date' in h else now
            h['received_entry_date'] = h['received_entry_date']['$date'] if 'received_entry_date' in h else now
    # print(data['_id'], data['wallet_deduction_history'])
    # print(data['_id'])
    # data['last_received_date'] = data.get('last_received_date')
    db.users.insert_one(data)
# print(cleaned_data)