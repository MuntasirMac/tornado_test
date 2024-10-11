import json
from io import BytesIO
from time import time
from datetime import datetime
from dbconnection import connect_db
from bson import ObjectId, json_util
import re

db = connect_db()
# print((db.list_collection_names()))

data_list = list(db.users.find({'is_active': True}))
count = 0

for datum in data_list:
	sub_org_dict = datum.get('sub_org')
	if sub_org_dict:
		print(f"Sub Org Type is {type(sub_org_dict)} and name is {sub_org_dict.get('name')}")
		count += 1 #if is_active_status != 'NA' else 0
	sub_org = sub_org_dict['name'] if sub_org_dict and type(sub_org_dict) == dict and 'name' in sub_org_dict else 'NA'
	# print(sub_org)
	# active_status = 'Active' if is_active_status == True else 'Inactive'
	# print(active_status)
	# if 'status_updated_on' in data_list:
	# 	print(active_status, datum.get('status_updated_on').get('$date'))
print(count)