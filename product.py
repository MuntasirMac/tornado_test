import json
from bson import json_util, ObjectId
import pymongo
from dbconnection import connect_db
from tornado.web import RequestHandler

db = connect_db()

class ProductListHandler(RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        print("******* Printing Requests ******")

        in_status = db.product.insert_many(data)

        payload = data
        print(in_status)

        if in_status:
            
            self.set_header('Content-Type', 'application/json')
            self.set_status(201)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test Done!',
                'data': payload,
                'status_code': 201,
            }, default=json_util.default))