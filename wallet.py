import json, random, string
from random import randint
import os
import weasyprint
from datetime import datetime, timedelta, timezone
from time import time
from bson import json_util, ObjectId
from product import db
from tornado.web import RequestHandler
from tornado.log import app_log as log
from jinja2 import Environment, FileSystemLoader

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLAT_SRC = os.path.join(ROOT, 'templates')

def pdf_assets(template, CSS=None):
    env = Environment(loader=FileSystemLoader(TEMPLAT_SRC))
    # CSS_SRC = os.path.join(ROOT, 'static/css')
    template = env.get_template(template)
    # css = os.path.join(CSS_SRC, CSS)
    return template, CSS


now = datetime.now()
user = {
	"_id": "641a9b1fea0c1cd5e5ed2a81",
	"name": "Benoy Kumar Roy"
}

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
		add_method = data['add_method'] if 'add_method' in data else None

		valid_methods = [
		    "cash",
		    "cheque",
		    "debit or credit card",
		    "mobile wallet"
		]

		if add_method == None or add_method not in valid_methods:
		    self.set_header('Content-Type', 'application/json')
		    self.set_status(200)
		    self.finish(json.dumps({
		        'status': 'error',
		        'message': 'You must enter a valid method!',
		        'status_code': 200,
		    }, default=json_util.default))
		    return

		wallet_data = db.wallets.find_one({'_id': ObjectId(wallet_id)})
		wallet_add_history = wallet_data['wallet_add_history'] if 'wallet_add_history' in wallet_data else []
		wallet_deduction_history = wallet_data['wallet_deduction_history'] if 'wallet_deduction_history' in wallet_data else []
		last_received_date = wallet_data['last_received_date'] if 'last_received_date' in wallet_data else None
		total_current_due = wallet_data['total_due_amount']

		wallet_balance = wallet_data['wallet_balance'] + amount_to_add

		wallet_add_history_data = {
		    'id': ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12)),
		    'previous_balance': wallet_data['wallet_balance'],
		    'added_method': add_method,
		    'added_amount': amount_to_add,
		    'total_current_due': total_current_due,
		    'current_balance': wallet_balance,
		    'modified_on': datetime.now(timezone.utc).replace(tzinfo=None),
		    'modified_by': str(user['_id']),
		    'modified_by_name': str(user['name'])
		}

		last_received_date = datetime.now(timezone.utc).replace(tzinfo=None)
		wallet_add_history.append(wallet_add_history_data)

		if auto_adjust_to_dues == True:
		    entity_id = str(wallet_data['entity_id'])

		    orders = db.orders.find({'end_entity.id': entity_id, 'order_status.seq_no': {'$lt': 9}, 'due_amount': {'$gt': 0}}).sort('created_on', 1)
		    # orders = db.orders.find({'organization': ObjectId(organization), 'end_entity.id': entity_id, 'order_status.seq_no': {'$lt': 9}, 'due_amount': {'$gt': 0}}).sort('created_on', 1)
		    order_list = list(orders)

		    if len(order_list) == 0:
		        self.set_header('Content-Type', 'application/json')
		        self.set_status(200)
		        self.finish(json.dumps({
		            'status': 'error!',
		            'message': 'No orders found in this entity!',
		            'status_code': 200,
		        }, default=json_util.default))
		        return
		    
		    net_bill_amount = 0
		    previous_due = wallet_data['total_due_amount']
		    total_received_now = 0
		    entity = order_list[0]['end_entity']
		    total_discount = 0
		    contact_no = order_list[0]['drop_contact_no']
		    invoice_order_list = []

		    for order in order_list:
		        total_previous_due = wallet_data['total_due_amount']
		        order_previous_due = order['due_amount']
		        previous_wallet_balance = wallet_balance
		        if wallet_balance > 0 and order['due_amount'] > 0:
		            invoice_order_list.append(order)

		            if wallet_balance >= order['due_amount']:
		                wallet_balance -= order['due_amount']
		                wallet_data['total_due_amount'] -= order['due_amount']
		                order['total_received_amount'] += order['due_amount']
		                wallet_data['total_received_amount'] += order['due_amount']
		                received_amount = order['due_amount']
		                total_received_now += order['due_amount']
		                net_bill_amount += order['bill_amount']
		                total_discount += order['total_discount']
		                order['due_amount'] = 0

		            elif wallet_balance < order['due_amount']:
		                order['due_amount'] -= wallet_balance
		                wallet_data['total_due_amount'] -= wallet_balance
		                order['total_received_amount'] += wallet_balance
		                wallet_data['total_received_amount'] += wallet_balance
		                received_amount = wallet_balance
		                total_received_now += wallet_balance
		                net_bill_amount += order['bill_amount']
		                total_discount += order['total_discount']
		                wallet_balance = 0

		        else:
		            continue

		        received_history = order['received_history']
		        payment_history = order['payment_history']
		        total_current_due = wallet_data['total_due_amount']
		        order_current_due = order['due_amount']

		        received_data = {
		            'received_amount': received_amount,
		            'received_method': 'conveyance wallet',
		            'received_date': datetime.now(timezone.utc).replace(tzinfo=None),
		            'received_entry_date': datetime.now(timezone.utc).replace(tzinfo=None),
		            'received_by': str(user['_id']),
		            'received_by_name': user['name']
		        }

		        received_history.append(received_data)
		        payment_history.append(received_data)

		        order_payload = {
		            'received_history': received_history,
		            'payment_history': payment_history,
		            'total_received_amount': order['total_received_amount'],
		            'due_amount': order['due_amount']
		        }

		        order_status = db.orders.find_one_and_update({'_id': ObjectId(str(order['_id']))}, {'$set': order_payload})
		        if order_status:
		            log.info(f"Order {str(order['_id'])} has been updated with info {order_payload}")
		        
		        wallet_deduction_history_data = {
		            'id': ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12)),
		            'previous_balance': previous_wallet_balance,
		            'total_previous_due': total_previous_due,
		            'order_previous_due': order_previous_due,
		            'order_id': str(order['_id']),
		            'deducted_amount': received_amount,
		            "deducted_method" : "conveyance wallet",
		            'total_current_due': total_current_due if total_current_due > 0 else 0,
		            'order_current_due': order_current_due,
		            'current_balance': wallet_balance,
		            'modified_on': datetime.now(timezone.utc).replace(tzinfo=None),
		            'modified_by': str(user['_id']),
		            'modified_by_name': str(user['name'])
		        }

		        wallet_deduction_history.append(wallet_deduction_history_data)

		    current_due = wallet_data['total_due_amount'] if wallet_data['total_due_amount'] > 0 else 0
		    invoice_no = int(time()) * 1000 * randint(2, 200)
		    today = datetime.today().date()
		    pos_created_by = str(user['name'])
		    filename = f"conveyance_wallet_invoice_{invoice_no}.pdf"
		    # filepath = os.path.join(
		    #     os.getcwd(), "pdf", "wallet_pdf", filename)
		    template, css = pdf_assets('wal2.html')

		    template_vars = {
		        'invoice_order_list': invoice_order_list,
		        'entity': entity,
		        'invoice_no': invoice_no,
		        'pos_created_by': pos_created_by,
		        'previous_due': previous_due,
		        'current_due': current_due,
		        'today': today,
		        'total_discount': total_discount,
		        'total_received_now': total_received_now,
		        'net_bill_amount': net_bill_amount,
		        'contact_no': contact_no
		    }

		    rendered_string = template.render(template_vars)
		    html = weasyprint.HTML(string=rendered_string)
		    log.info("Template Vars Passsed and html rendered")
		    # conveyance_pdf_filepath = f"pdf{filepath.split('/pdf')[1]}"
		    # file_upload_path_data = {
		    #     "wallet_report_url": conveyance_pdf_filepath
		    # }
		    # log.info(f"pdf path is {conveyance_pdf_filepath}")

		    pdf = html.write_pdf()
		    log.info("PDF wrote from html")

		    self.set_header('Content-Type', 'application/pdf; charset="utf-8"')
		    self.set_header('Content-Disposition', 'attachment; filename=' + filename)
		    self.write(pdf)
		    log.info("PDF returned")

		payload = {
		    "total_received_amount": wallet_data['total_received_amount'],
		    "wallet_add_history": wallet_add_history,
		    "wallet_deduction_history": wallet_deduction_history,
		    "total_due_amount": wallet_data['total_due_amount'] if wallet_data['total_due_amount'] > 0 else 0,
		    "wallet_balance": wallet_balance,
		    "last_received_date": last_received_date,
		    "modified_on": datetime.now(timezone.utc).replace(tzinfo=None),
		    "modified_by": str(user['_id']),
		    "modified_by_name": str(user['name'])
		}

		status = db.wallets.find_one_and_update({'_id': ObjectId(wallet_id)}, {'$set': payload})
		log.info("Update operation done")

		if status:
		    # payload['_id'] = wallet_id
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