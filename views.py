import json
from tornado.web import RequestHandler

class TestDbHandler(RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        print("******* Printing Requests ******")
        print(type(data))
        print(data['name'])
        print(data['role'])

        payload = data
        
        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(json.dumps({
            'status': 'Okay',
            'message': 'Test Done!',
            'data': data,
            'status_code': 200,
        }))
        return 