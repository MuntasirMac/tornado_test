import json
from datetime import datetime
from bson import json_util, ObjectId
from product import db
from tornado.web import RequestHandler


now = datetime.now()

class CreateWalletApi(RequestHandler):
	def post(self):
		data = json.loads(self.request.body.decode("utf-8"))
		

		status = db.wallets.insert_one(data)

		if status:
			# payload["_id"] = status.inserted_id
			# print(payload['_id'])
			self.set_header('Content-Type', 'application/json')
			self.set_status(201)
			return self.finish(json.dumps({
			    'status': 'created',
			    'message': 'Order Created!',
			    'data': data,
			    'status_code': 201,
			}, default=json_util.default))


class AddMoneyToWalletApi(RequestHandler):

	def put(self, wallet_id):

		data = json.loads(self.request.body.decode('utf-8'))

		amount_to_add = data['amount_to_add'] if 'amount_to_add' in data else 0

		if not 'amount_to_add' in data and data['amount_to_add'] <= 0:
		    self.set_header('Content-Type', 'application/json')
		    self.set_status(400)
		    self.finish(json.dumps({
		        'status': 'error',
		        'message': 'You must add amounts greater than 0!',
		        'status_code': 400,
		    }, default=json_util.default))
		    return
        
		auto_adjust_to_dues = data['auto_adjust_to_dues'] if 'auto_adjust_to_dues' in data else False

		wallet_data = db.wallets.find_one({'_id': ObjectId(wallet_id)})

		wallet_balance = wallet_data['wallet_balance'] + amount_to_add

		if auto_adjust_to_dues == True:
		    entity_id = wallet_data['entity_id']

		    orders = db.order.find({'end_entity.id': entity_id}).sort('created_on', 1)

		    for order in orders:
		        if wallet_balance and wallet_balance > order['due_amount']:
		            wallet_balance -= order['due_amount']
		            wallet_data['total_due_amount'] -= order['due_amount']
		            order['total_received_amount'] += order['due_amount']
		            wallet_data['total_received_amount'] += order['due_amount']
		            order['due_amount'] = 0

		        # elif wallet_balance and wallet_balance < order['due_amount']:
		        #     order['due_amount'] -= wallet_balance
		        #     wallet_data['total_due_amount'] -= wallet_balance
		        #     order['total_received_amount'] += wallet_balance
		        #     wallet_data['total_received_amount'] += wallet_balance
		        #     wallet_balance = 0

		        else:
		            pass

		        order_payload = {
		            'total_received_amount': order['total_received_amount'],
		            'due_amount': order['due_amount']
		        }

		        order_status = db.order.find_one_and_update({'_id': ObjectId(order['_id'])}, {'$set': order_payload})
		        if order_status:
		            print(f"Order {order['_id']} has been updated with info {order_payload}")

		    payload = {
		        "total_received_amount": wallet_data['total_received_amount'],
		        "total_due_amount": wallet_data['total_due_amount'] if wallet_data['total_due_amount'] > 0 else 0,
		        "wallet_balance": wallet_balance
		    }

		    print(payload)

		    status = db.wallets.find_one_and_update({'_id': ObjectId(wallet_id)}, {'$set': payload})

		    if status:
		        payload['_id'] = str(wallet_id)
		        self.set_header('Content-Type', 'application/json')
		        self.set_status(200)
		        self.finish(json.dumps({
		            'status': 'success',
		            'message': 'Orders adjusted with wallet!',
		            'data': payload,
		            'status_code': 200,
		        }, default=json_util.default))
		        return
		    
		    else:
		        self.set_header('Content-Type', 'application/json')
		        self.set_status(400)
		        self.finish(json.dumps({
		            'status': 'error',
		            'message': 'Unknown error occured!',
		            'status_code': 400,
		        }, default=json_util.default))
		        return
		    
		else:
		    payload = {
		        "wallet_balance": wallet_balance
		    }

		    status = db.wallets.find_one_and_update({'_id': ObjectId(str(wallet_id))}, {'$set': payload})

		    if status:
		        payload['_id'] = str(wallet_id)
		        self.set_header('Content-Type', 'application/json')
		        self.set_status(200)
		        self.finish(json.dumps({
		            'status': 'success',
		            'message': 'Successfully added money in wallet!',
		            'data': payload,
		            'status_code': 200,
		        }, default=json_util.default))
		        return
		    
		    else:
		        self.set_header('Content-Type', 'application/json')
		        self.set_status(400)
		        self.finish(json.dumps({
		            'status': 'error',
		            'message': 'Unknown error occured!',
		            'status_code': 400,
		        }, default=json_util.default))
		        return