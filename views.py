import json
from bson import json_util
import pymongo
from dbconnection import connect_db
from tornado.web import RequestHandler

db = connect_db()

class TestDbHandler(RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        print("******* Printing Requests ******")
        print(data)
        print(data['name'])
        print(data['roll'])
        print(db)

        in_status = db.user_info.insert_one(data)

        payload = data

        if in_status:
            payload['_id'] = in_status
        
        self.set_header('Content-Type', 'application/json')
        self.set_status(201)
        return self.finish(json.dumps({
            'status': 'Okay',
            'message': 'Test Done!',
            'data': payload,
            'status_code': 201,
        }, default=json_util.default))