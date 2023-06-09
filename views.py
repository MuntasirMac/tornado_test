import json
from bson import json_util, ObjectId
import pymongo
from dbconnection import connect_db
from tornado.web import RequestHandler

db = connect_db()

class TestDbHandler(RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        print("******* Printing Requests ******")

        in_status = db.student.insert_one(data)

        payload = data

        if in_status:
            payload['_id'] = in_status.inserted_id
            print(payload['_id'])
            self.set_header('Content-Type', 'application/json')
            self.set_status(201)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test Done!',
                'data': payload,
                'status_code': 201,
            }, default=json_util.default))


    def get(self, _id):
        # _id = self.get_argument('id')
        payload = db.student.find_one({"_id":ObjectID(_id)})
        print(self.path_kwargs)
        print(self.request)

        if payload:
            self.set_header('Content-Type', 'application/json')
            self.set_status(201)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test Done!',
                'data': payload,
                'status_code': 201,
            }, default=json_util.default))