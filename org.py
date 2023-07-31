import json
from datetime import datetime
from bson import json_util, ObjectId
from product import db
from tornado.web import RequestHandler


now = datetime.now()

class CreateOrgApi(RequestHandler):
	def post(self):
		data = json.loads(self.request.body.decode("utf-8"))

		status = db.org.insert_many(data)

		if status:
			payload["_id"] = status.inserted_id
			print(payload['_id'])
			self.set_header('Content-Type', 'application/json')
			self.set_status(201)
			return self.finish(json.dumps({
			    'status': 'created',
			    'message': 'Order Created!',
			    'data': payload,
			    'status_code': 201,
			}, default=json_util.default))

