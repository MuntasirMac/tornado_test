import json
from datetime import datetime
from bson import json_util, ObjectId
from product import db
from tinyec import registry
from tornado.web import RequestHandler
from cryptography.fernet import Fernet


now = datetime.now()

class CreateEncryptionApi(RequestHandler):
	def post(self):
		data = json.loads(self.request.body.decode("utf-8"))

		api_key = data.get('api_key', None)
		api_secret = data.get('api_secret', None)

		key = Fernet.generate_key()
		fernet = Fernet(key)
		print(key)

		if api_key:
			encrypted_api_key = fernet.encrypt(api_key.encode('utf-8'))
		if api_secret:
			encrypted_api_secret = fernet.encrypt(api_secret.encode('utf-8'))

		encrypted_payload = {
			'encrypted_api_key': (encrypted_api_key),
			'encrypted_api_secret': (encrypted_api_secret),
			'encrypted_key': key
		}

		decrypted_api_key = fernet.decrypt(encrypted_api_key).decode('utf-8')
		decrypted_api_secret = fernet.decrypt(encrypted_api_secret).decode('utf-8')
		
		print("encrypted msg:", (encrypted_api_key))
			
		status = db.encryptions.insert_one(encrypted_payload)

		if status:
			data['_id'] = status
			data["created_on"]: now
			self.set_header('Content-Type', 'application/json')
			self.set_status(201)
			return self.finish(json.dumps({
			    'status': 'created',
			    'message': 'Encryption Created!',
			    'data': encrypted_payload,
			    'status_code': 201,
			}, default=json_util.default))


class GetEncryptedKeys(RequestHandler):
	def get(self, id):

		instance = db.encryptions.find_one({'_id': ObjectId(id)})

		if instance:
			encrypted_api_key = instance.get('encrypted_api_key')
			encrypted_key = instance.get('encrypted_key')
			encrypted_api_secret = instance.get('encrypted_api_secret')

			fernet = Fernet(encrypted_key)

			# print(encrypted_api_key)
			# print(encrypted_api_secret)
			# print(encrypted_key)

			decrypted_api_key = fernet.decrypt(encrypted_api_key).decode('utf-8')
			decrypted_api_secret = fernet.decrypt(encrypted_api_secret).decode('utf-8')

			# print(type(decrypted_api_key))
			# print(decrypted_api_secret)

			instance['encrypted_api_key'] = (decrypted_api_key),
			instance['encrypted_api_secret'] = decrypted_api_secret

			self.set_header('Content-Type', 'application/json')
			self.set_status(200)
			return self.finish(json.dumps({
			    'status': 'OK',
			    'message': 'Here are your credentials!',
			    'data': instance,
			    'status_code': 200,
			}, default=json_util.default))
