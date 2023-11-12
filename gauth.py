import requests
import json
from bson import json_util, ObjectId
from tornado.web import RequestHandler


REDIRECT_URI = 'web.conveyance.app/'
CLIENT_ID = '882109075726-mp2k8s5hdej8614o6dh9sd2pmbo818hv.apps.googleusercontent.com'
CLIENT_SECRET = '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'

class GAuth(RequestHandler):
	def post(self):
		data = json.loads(self.request.body.decode("utf-8"))
		code = data['auth_code'] if 'auth_code' in data else ''
		token_uri = 'https://oauth2.googleapis.com/token'
		headers = {
			'Content-Type':'application/x-www-form-urlencoded'
			}
		body = {
				'code': code,
			    'client_id': CLIENT_ID,
			    'client_secret': CLIENT_SECRET,
			    'redirect_uri': REDIRECT_URI,
			    'grant_type': 'authorization_code'
			}
		redirect_uri = 'https://' + REDIRECT_URI
		# print(type(body))
		token_uri += '?'
		for key, value in body.items():
			token_uri += f"{key}={value}&"
		token_uri = token_uri[:-1]
		# print(token_uri)

		uri = f'https://oauth2.googleapis.com/token?code={code}&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&redirect_uri={redirect_uri}&grant_type=authorization_code'
		print(uri)
		token_response = requests.post(uri)
		print(token_response.status_code)
		# print(token_response.json())
		tokens = token_response.json()
		access_token = tokens.get('access_token')
		pro_uri = f'https://www.googleapis.com/oauth2/v3/userinfo?access_token={access_token}'
		# pro_params = {
		# 	'access_token':access_token
		# }

		res = requests.get(pro_uri).json()

		self.set_header('Content-Type', 'application/x-www-form-urlencoded')
		self.set_status(200)
		return self.finish(json.dumps({
		    'status': 'OK',
		    'data': tokens,
		    'user_info': res,
		    'status_code': 200,
		}, default=json_util.default))