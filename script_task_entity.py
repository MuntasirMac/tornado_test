from dbconnection import connect_db
from bson import ObjectId
from datetime import datetime, timedelta
d = datetime.strptime("2025-11-1", "%Y-%m-%d")

db = connect_db()
# organization = '5ef834ca70713e543a64195a'
tasks = list(db.tasks.find({
  'created_on': {'$gte': d},
  '$or': [
  	{'end_entity_id': ""},
  	{'start_entity_id': ""}
  ]
}).sort('created_on', -1).limit(5000))
# tasks = list(db.tasks.find({'organization': ObjectId(organization)}).sort('created_on', -1))
print(len(tasks))
count = 0
for task in tasks:
	payload = {
		'start_entity_id': '',
		'end_entity_id': ''
	}
	if 'start_loc' in task and task['start_loc'] and not task['start_entity_id']:
		start_loc = task['start_loc']
		start_entity = db.entities.find_one({'loc': start_loc, 'organization': task['organization']}, {'loc': 1, 'name': 1})
		
		if start_entity:
			start_entity_id = str(start_entity['_id'])
			payload['start_entity_id'] = start_entity_id

		

	if 'end_loc' in task and task['end_loc'] and not task['end_entity_id']:
		end_loc = task['end_loc']
		end_entity = db.entities.find_one({'loc': end_loc, 'organization': task['organization']}, {'loc': 1, 'name': 1})
		
		if end_entity:
			end_entity_id = str(end_entity['_id'])
			payload['end_entity_id'] = end_entity_id
		

	
	db.tasks.find_one_and_update({'_id': task['_id'], 'organization': task['organization']}, {'$set': payload})
	