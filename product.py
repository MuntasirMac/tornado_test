import json
import pymongo
from bson import json_util, ObjectId
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

# worked with mock data

class GetProductByPrice(RequestHandler):
    def get(self):
        price = self.get_argument('price')
        query = {"product_price": {"$gt": price}}
        res = list(db.product.find(query))

        print(res)

        if res:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test With Kwargs Done!',
                'data': res,
                'status_code': 200,
            }, default=json_util.default))