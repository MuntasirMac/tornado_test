from dbconnection import connect_db
from bson import ObjectId
from datetime import datetime, timedelta


db = connect_db()
roaster_plans = list(db.roaster_plans.find({'weekends': {'$exists': True}}))
print(len(roaster_plans))
for r in roaster_plans:
	# print(r['weekends'])
	roasters = list(db.roasters.find({'roaster_plan._id': str(r['_id']), 'organization': ObjectId(r['organization'])}))
	# print(f"Total {len(roasters)} roasters in this roaster_plan {r['name']}")
	if roasters:
		for roaster in roasters:
			if r['weekends'] and isinstance(r['weekends'], list):
				roaster_plan = roaster['roaster_plan']
				roaster_plan['weekends'] = r['weekends']
				# print(roaster_plan)
				payload = {'roaster_plan': roaster_plan}
				# print(payload)
				db.roasters.find_one_and_update({'_id': roaster['_id']}, {'$set': payload})
				print(f"Updated roaster {roaster['name']} as {payload}")