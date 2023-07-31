import json
from datetime import datetime
from bson import json_util, ObjectId
from product import db
from tornado.web import RequestHandler


now = datetime.now()

class CreateEntityApi(RequestHandler):
	def post(self):
		data = json.loads(self.request.body.decode("utf-8"))

		status = db.entities.insert_one(data)

		if status:
			
			self.set_header('Content-Type', 'application/json')
			self.set_status(201)
			return self.finish(json.dumps({
			    'status': 'created',
			    'message': 'Order Created!',
			    'data': payload,
			    'status_code': 201,
			}, default=json_util.default))


