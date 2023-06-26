import json
from datetime import datetime
from bson import json_util, ObjectId
from product import db
from tornado.web import RequestHandler


now = datetime.now()

class CreateOrderApi(RequestHandler):
	def post(self):
		data = json.loads(self.request.body.decode("utf-8"))
		product_id = data["product_id"]
		quantity = int(data["qty"])
		details = data["details"]
		product = db.product.find_one({"_id": ObjectId(product_id)})
		unit_price = product["product_price"]
		net_price = unit_price*quantity
		created_at = now

		print(data)
		print(unit_price)

		payload = {
			"product_name": product["product_name"],
			"product_size": product["product_size"],
			"product_color": product["product_color"],
			"quantity": quantity,
			"unit_price": unit_price,
			"net_price": net_price,
			"created_at": created_at
		}

		status = db.order.insert_one(payload)

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

