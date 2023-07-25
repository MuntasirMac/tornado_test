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
        payload = db.order.find().sort('created_at',-1)
        # payload = list(payload)
        # for i in payload:
        # #     print("net_price ", i['net_price'])
        # #     i['net_price'] += 1000
        #     print(i['net_price'])
        #     status = db.order.find_one_and_update({'_id': i['_id']}, {"$set": {'net_price': i['net_price']}})
        
        if payload:
            payload = list(payload)
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
        print(self.path_args)
        print(self.path_kwargs)
        res = db.student.find_one({"_id": ObjectId(id)})
        print(res)

        if res:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test With Args Done!',
                'data': res,
                'status_code': 200,
            }, default=json_util.default))


class GetStudentByKwargs(RequestHandler):
    def get(self):
        holding = self.get_argument('holding')
        city = self.get_argument('city')
        query = {"address.holding": holding, "address.city": city}
        res = db.student.find_one(query)
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


class UpdateStudent(RequestHandler):
    def put(self, id):
        data = json.loads(self.request.body.decode("utf-8"))
        dept = data['dept']

        payload = {
            "dept": dept
        }

        res = db.student.find_one_and_update({'_id':ObjectId(id)}, {'$set': payload})

        if res:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test With Kwargs Done!',
                'data': res,
                'status_code': 200,
            }, default=json_util.default))


class DeleteById(RequestHandler):
    def delete(self, id):
        print(self.path_args)
        query = db.student.delete_one({"_id": ObjectId(id)})
        print(query)

        if query:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Deleted',
                'message': 'Test With Kwargs Done!',
                'data': 'No Content',
                'status_code': 200,
            }, default=json_util.default))
