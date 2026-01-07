from dbconnection import connect_db
from bson import ObjectId

db = connect_db()

visit_plans = db.visiting_plans.find({'organization': ObjectId('674eafcdea682e275149c904')})

for vp in visit_plans:
	# print(vp)
	payload = {}
	if 'recommended' in vp and vp['recommended'] == False:
		payload['recommended'] = 'pending'

	if 'authorized' in vp and vp['authorized'] == False:
		payload['authorized'] = 'pending'

	if 'approved' in vp and vp['approved'] == False:
		payload['approved'] = 'pending'

	visiting_dates = vp['visiting_dates']
	for vd in visiting_dates:
		v_date = vd['date']
		print(f'visiting date is {v_date}')
		if 'task_generated' not in vd:
			vd['task_generated'] = False
		
	payload['visiting_dates'] = visiting_dates
	payload['task_type'] = 'IFC'

	status = db.visiting_plans.find_one_and_update({'_id': ObjectId(vp['_id'])}, {'$set': payload})
	