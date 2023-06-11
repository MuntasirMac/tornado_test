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

class TestGetHandler(RequestHandler):
    def get(self):
        payload = list(db.student.find())
        
        if payload:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test Done!',
                'data': payload,
                'status_code': 200,
            }, default=json_util.default))


class GetArgHandler(RequestHandler):
    def get(self, id):
        print(id)
        res = db.student.find_one({"_id": ObjectId(id)})
        print(res)

        if res:
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test Done!',
                'data': res,
                'status_code': 200,
            }, default=json_util.default))

        pass