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
        price = float(self.get_argument('price'))
        
        res = db.product.find({"product_price": {"$gt": price}})
        res = list(res)

        if res:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test With Kwargs Done!',
                'data': res,
                'status_code': 200,
            }, default=json_util.default))


class GetProductBySizeAndColor(RequestHandler):
    def get(self):
        size = self.get_argument('size')
        color = self.get_argument('color')

        query = {'product_size': size, 'product_color': color}

        res = list(db.product.find(query))

        print(len(res))

        if res:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Your Desired Products Are Here!',
                'data': res,
                'status_code': 200,
            }, default=json_util.default))