import json
import xlsxwriter
from bson import json_util, ObjectId
import pymongo
from datetime import datetime, timedelta
from pytz import utc
from dbconnection import connect_db
from tornado.web import RequestHandler
from tornado.log import app_log as log
from io import BytesIO
db = connect_db()

class TestDbHandler(RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))
        print("******* Printing Requests ******")
        print(self.request)
        print(self.request.body)


        payload = data
        payload['created_on'] = datetime.now(utc)
        in_status = db.student.insert_one(payload)

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
        report = self.get_argument("report", False)
        collection = db.wallets  # Replace with your actual collection name

        # Define the _id for matching
        target_id = "657ecd45810fb8daa3d07b19"

        # Define the timestamp range
        start_time = 1695796755642  # Replace with your start timestamp
        end_time = 1698819645588  # Replace with your end timestamp

        if start_time:
            # if date_validation(self, start_time):  # for check ing mandatary fields
                start_time = datetime.fromtimestamp(int(start_time)/1000.0)
                # start_time_date = start_time.date()
                # start_time = datetime.combine(
                #     start_time_date, datetime.min.time())
                # log.info(f"Start time is {start_time}")
        if end_time:
              # for check ing mandatary fields
            end_time = datetime.fromtimestamp(int(end_time)/1000.0)
            # end_time_date = end_time.date()
            # end_time = datetime.combine(end_time_date, datetime.min.time())
            # end_time = end_time + \
            #     timedelta(hours=23, minutes=59, seconds=59)
            # log.info(f"End time is {end_time}")
        # print(start_time)
        # print(end_time)
        # Define the aggregation pipeline
        pipeline = [
            {"$match": {'_id': target_id}},
            {"$project": {'wallet_deduction_history': 1}},
            {"$unwind": "$wallet_deduction_history"},
            # {"$match": {"wallet_deduction_history.modified_on": {"$gte": start_time, "$lte": end_time}}},
            {"$sort": {"wallet_deduction_history.modified_on": 1}},
            {"$group": {"total": {"$sum":1}, "_id": "$_id", "wallet_deduction_history": {"$push": "$wallet_deduction_history"}}}
        ]

        # Execute the aggregation
        result = list(db.wallets.aggregate(pipeline))
        wallet_data = db.wallets.find_one({"_id": target_id}, {"entity_name": 1})
        print(report)
        if result and report == 'fmt':
            buff = BytesIO()
            workbook = xlsxwriter.Workbook(buff, {'in_memory': True})
            if True:
                worksheet = workbook.add_worksheet("Wallet History Report")
                print('worksheet initialised')
                bold = workbook.add_format({'bold': True})
                border_bold_grey = workbook.add_format({'border': True, 'bold': True, 'bg_color': '#d3d3d3'})
                # border_bold_grey = border_bold_grey.set_align('center')
                border_bold_grey = border_bold_grey.set_align('vcenter')
                border = workbook.add_format({'border': True})
                # border = border.set_align('center')
                border = border.set_align('vcenter')
                worksheet.write(0, 0, f'Wallet History Report', bold)
                row = 2
                worksheet.write(row, 0, f"Entity Name: {wallet_data['entity_name']}", border)
                row += 1
                worksheet.write(row, 0, f"Generated At: {datetime.utcnow()}", border)

                data = result[0]['wallet_deduction_history']
                fields = ['previous_balance', 'previous_due', 'order_previous_due', 'order_id', 'deducted_amount',
                 'total_current_due', 'order_current_due', 'current_balance', 'modified_on']
                row += 2
                col = 0
                st_row = row
                worksheet.set_column(0, 9, 20)
                for field in fields:
                    worksheet.write(row, col, field.replace("_", " ").title(), border_bold_grey)
                    col += 1
                row += 1
                for otpt in data:
                    worksheet.write(row, 0, otpt.get('previous_balance', 'NA'), border)
                    worksheet.write(row, 1, otpt.get('total_previous_due', 'NA'), border)
                    worksheet.write(row, 2, otpt.get('order_previous_due', 'NA'), border)
                    worksheet.write(row, 3, otpt.get('order_id', 'NA'), border)
                    worksheet.write(row, 4, otpt.get('deducted_amount', 'NA'), border)
                    worksheet.write(row, 5, otpt.get('total_current_due', 'NA'), border)
                    worksheet.write(row, 6, otpt.get('order_current_due', 'NA'), border)
                    worksheet.write(row, 7, otpt.get('current_balance', 'NA'), border)
                    worksheet.write(row, 8, otpt.get('modified_on', 'NA'), border)

                    row += 1
                # print(row)
                row += 2
                centered_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
                worksheet.set_column(st_row, len(data[0]) - 1, None, centered_format)
            buff.seek(0)
            workbook.close()

            print('workbook closed')

            try:
                self.set_status(200)
                self.set_header(
                    'Content-type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.set_header(
                    "Content-Disposition", 
                    "attachment; filename=wallet_{}.xlsx".format(datetime.now().strftime('%d-%m-%y_%I-%M-%S_%p')))
                return self.finish(buff.getvalue())
        
            except Exception as e:
                self.set_header('Content-Type', 'application/json')
                self.set_status(200)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': 'Unknown error occurred!',
                    'status_code': 200,
                }, default=json_util.default))
        
        elif result:
            # result = list(result)
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Okay',
                'message': 'Test Done!',
                'data': result,
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


class WalletCollectionApi(RequestHandler):
    def get(self):
        pipeline = [
            {
              "$addFields": {
                   "wallet_history": {
                       "$concatArrays": ["$wallet_add_history", "$wallet_deduction_history"]
                    }
               }
             },
             {
                 "$unwind": "$wallet_history"
             },
             {
                  "$match": {
                        "wallet_history.modified_on": {
                            "$gte": "2023-12-10T00:00:00.000Z",
                            "$lte": "2024-01-11T06:56:06.902Z"
                    },
                   "wallet_history.modified_by": "641a9b1fea0c1cd5e5ed2a81",
               }
              },
              {
                   "$group": {
                       "_id": {
                           "date": {"$dateToString": { 'format': "%Y-%m-%d", 'date': {"$toDate": "$wallet_history.modified_on"} }},
                           "sub_org": "$sub_org.id",
                           "sub_org_name": "$sub_org.name",
                           "parent_sub_org": "$sub_org.parent_sub_org_data.name",
                           "user": "641a9b1fea0c1cd5e5ed2a81",
                           "method": {
                               "$ifNull": ["$wallet_history.added_method", "$wallet_history.deducted_method"]
                           }
                       },
                       "total_collected_amount": {"$sum": {"$sum": ["$wallet_history.added_amount", "$wallet_history.deducted_amount"]}},
                   },
               },
               {
                   "$project": {
                       "date": "$_id.date",
                       "method": "$_id.method",
                       "sub_org": "$_id.sub_org",
                       "sub_org_name": "$_id.sub_org_name",
                       "total_collected_amount": "$total_collected_amount",
                       "parent_sub_org": "$_id.parent_sub_org",
                       "user": "$_id.user",
                       "_id": 0
                   }
               },
               {
                   "$match": {
                       "method": {
                           "$nin": [None, "conveyance wallet", "refunded_from_order"]
                       },
                       "sub_org": {
                            "$nin": [None, "", {}]
                       }
                   }
               },
               {
                   "$group": {
                       "_id": {
                           "date": "$date",
                           "sub_org": "$sub_org",
                           "sub_org_name": "$sub_org_name",
                           "parent_sub_org": "$parent_sub_org",
                           "user": "$user"
                       },
                       "data": {
                           "$push": {
                               "method": "$method",
                               "total_collected_amount": "$total_collected_amount"
                           }
                       }
                   },
               },
               {
                   "$project": {
                       "date": "$_id.date",
                       "sub_org": "$_id.sub_org",
                       "sub_org_name": "$_id.sub_org_name",
                       "parent_sub_org": "$_id.parent_sub_org",
                       "data": "$data",
                       "user": "$_id.user",
                       "_id": 0
                   }
               },
               {
                    "$addFields": {
                        "total_amount_this_day": {
                            "$sum": "$data.total_collected_amount"
                        }
                    }
                },
               {
                   "$addFields": {
                       "user_number": 1
                   }
               },
               {
                    "$lookup": {
                        "from": "users",
                        "localField": "user",
                        "foreignField": "_id",
                        "as": "userDetails"
                    },
               },
               {
                "$set": {
                    "user_number": {
                        "$ifNull": [{ "$arrayElemAt": ["$userDetails.mobile", 0] },
                            { "$arrayElemAt": ["$userDetails.email", 0] }
                        ]
                    },
                    "user": {"$arrayElemAt": ["$userDetails.name", 0]},
                    }
               },
               {
                   "$project": {
                       "userDetails": 0
                   }
               },
               {
                   "$addFields": {
                       "parent_sub_org": ""
                   }
               },
               {
                    "$lookup": {
                        "from": "sub_orgs",
                        "localField": "sub_org",
                        "foreignField": "_id",
                        "as": "subOrg"
                    },
               },
               {
                    "$set": {
                        "parent_sub_org": {
                            "$ifNull": [
                                { "$arrayElemAt": ["$subOrg.parent_sub_org_data.name", 0] },
                                    "Parent Not Found"
                            ]
                        }
                    }
                },
                {
                    "$project": {
                        "subOrg": 0
                    }
                },
                {
                   "$sort": {"date": -1}
                }, 
        ]

        result = list(db.wallets.aggregate(pipeline))

        if result:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'success!',
                "total": len(result),
                'message': 'Aggregation Done!',
                'data': result,
                'status_code': 200,
            }, default=json_util.default))


def date_validation(self, datefield: str):
    """
    validates and transform dd-mm-yyyy format date into pythonic datetime format.
    :param date_field: dd-mm-yyyy format date
    :return: datetime
    """
    if datefield is None or len(str(datefield)) == 0:
        self.set_header('Content-Type', 'application/json')
        self.set_status(400)
        return self.finish(json.dumps({
            'status': 'error',
            'message': 'DateField cannot be None',
            'status_code': 400,
        }, default=json_util.default))
    try:
        _ = datetime.fromtimestamp(int(datefield)/1000.0)
        return True
    except ValueError:
        self.set_header('Content-Type', 'application/json')
        self.set_status(400)
        return self.finish(json.dumps({
            'status': 'error',
            'message': 'A Value Error in DateField',
            'status_code': 400,
        }, default=json_util.default))
    except SyntaxError:
        self.set_header('Content-Type', 'application/json')
        self.set_status(400)
        return self.finish(json.dumps({
            'status': 'error',
            'message': 'An Syntax Error in DateField',
            'status_code': 400,
        }, default=json_util.default))


class WalletDueCollectionListApi(RequestHandler):
    """
    The Total Collection By User API for Getting Total Amounts
    Collected(modified) by User within a time range
        access thru
        /app/due-collection-list
        :param OAuth2BaseHandler: 
    """
    def get(self):
        """
        The GET method for list view
            :param self: will have request.body in post
            :param page:
            :param limit:
            :param collector_id: user that modified/collected
            :param sub_org_id: to filter by sub_org
            :param start_time: timestamp, within a timeframe in general timestamp divisible by 1000
            :param end_time: timestamp, within a timeframe in general timestamp divisible by 1000 
        """

        # log.info('Current User')
        # log.info(self.current_user)
        # log.info('crossed 1')
        # user = db.users.find_one({"_id": ObjectId(self.current_user["user_id"])})
        # log.info(f"username is {user['name']}")
        # if user:
        #     if 'is_operator' in user:
        #         is_operator = user['is_operator']
        #     else:
        #         is_operator = False
        #     is_driver = is_operator
        #     user_id = user['_id'] if '_id' in user else None
        # else:
        #     user = db.drivers.find_one({"_id": ObjectId(self.current_user["user_id"])})
        #     if user:
        #         is_driver = True
        #         user_id = user['_id'] if '_id' in user else None

        # if user is not None:
        #     user_id = str(user['_id']) if '_id' in user else None

        #     if user_id is None:
        #         # error
        #         self.set_header('Content-Type', 'application/json')
        #         self.set_status(400)
        #         return self.finish(json.dumps({
        #             'status': 'error',
        #             'message': 'Sorry. you are not a valid user!',
        #             'status_code': 400,
        #         }, default=json_util.default))
        # else:
        #     self.set_header('Content-Type', 'application/json')
        #     self.set_status(400)
        #     return self.finish(json.dumps({
        #         'status': 'error',
        #         'message': 'You are not a valid user!',
        #         'status_code': 400,
        #     }, default=json_util.default))
        # organization = str(user['organization'])
        organization = "5ef834ca70713e543a64195a"
        user = "641a9b1fea0c1cd5e5ed2a81"

        try:
            page = int(self.get_argument('page', "0"))
            if page < 0:
                # This will send a blank search
                page = 0
        except ValueError:
            self.set_header('Content-Type', 'application/json')
            self.set_status(400)
            return self.finish(json.dumps({
                'status': 'error',
                'message': "argument <page> value has to be int.",
                'status_code': 400,
            }, default=json_util.default))

        try:
            limit = int(self.get_argument('limit', '10'))
            if limit < 0:
                limit = 0
        except ValueError:
            self.set_header('Content-Type', 'application/json')
            self.set_status(400)
            return self.finish(json.dumps({
                'status': 'error',
                'message': "argument <limit> value has to be int.",
                'status_code': 400,
            }, default=json_util.default))
        
        start_time = self.get_argument('start_time', None)
        end_time = self.get_argument('end_time', None)
        sub_org_id = self.get_argument('sub_org_id', None)
        collector_id = self.get_argument('collector_id', None)

        if start_time:
            if date_validation(self, start_time):  # for check ing mandatary fields
                start_time = datetime.fromtimestamp(int(start_time)/1000.0)
                log.info(f"Start time is {start_time}")
            else:
                return
        if end_time:
            if date_validation(self, end_time):  # for check ing mandatary fields
                end_time = datetime.fromtimestamp(int(end_time)/1000.0)
                log.info(f"End time is {end_time}")
            else:
                return
        
        skip = limit * page

        subq = {}
        query = {}
        pipeline = []
        if sub_org_id != None:
            query = {
                "$match": {
                    "sub_org.id": sub_org_id,
                    "organization": ObjectId(organization)
                }
            }
        else:
            query = {"$match" : {"organization": ObjectId(organization)}}
        pipeline.append(query)

        print(f"Initial query is {pipeline}")

        if user and skip >= 0:

            if start_time and end_time:
                subq['wallet_history.modified_on'] = {"$gte": start_time, "$lte": end_time}
                
            elif start_time and end_time == None:
                subq['wallet_history.modified_on'] = {"$gte": start_time}
                
            elif end_time and start_time == None:
               subq['wallet_history.modified_on'] = {"$lte": end_time}

            if collector_id:
                subq['wallet_history.modified_by'] = collector_id

        subq['wallet_history.method'] = {"$nin": ["refunded_from_order", "conveyance wallet", None, ""]}

        print(f"sub query is {subq}")
        
        pipeline += [
            {
                "$addFields": {
                    "wallet_history": {
                        "$concatArrays": ["$wallet_add_history", "$wallet_deduction_history"]
                    }
                }
            },
            {
                "$unwind": "$wallet_history"
            },
            {
                "$addFields": {
                    "wallet_history.collected_amount": {
                        "$ifNull": ["$wallet_history.added_amount", "$wallet_history.deducted_amount"]
                    },
                    "wallet_history.entity_name": "$entity_name",
                    "wallet_history.entity_id": "$entity_id",
                    "wallet_history.sub_org_id": "$sub_org.id",
                    "wallet_history.sub_org": "$sub_org.name",
                    "wallet_history.parent_sub_org": {
                        "$ifNull": ["$sub_org.parent_sub_org_data.name", "Parent Not Found"]
                    },
                    "wallet_history.method": {
                        "$ifNull": ["$wallet_history.added_method", "$wallet_history.deducted_method"]
                    },
                    "wallet_history.trx_type": {
                        "$cond": {
                            "if": { "$ifNull": ["$wallet_history.added_amount", False] },
                            "then": "addition",
                            "else": {
                                "$cond": {
                                    "if": { "$ifNull": ["$wallet_history.deducted_amount", False] },
                                    "then": "deduction",
                                    "else": None
                                }
                            }
                        }
                    },
                    "wallet_history.organization": "$organization",
                },
            },
            {
                "$project": {
                    "wallet_history": 1,
                    "_id": 0,
                }
            },
            {
                "$project": {
                    "wallet_history.added_method": 0,
                    "wallet_history.deducted_method": 0,
                }
            },
            {
                "$match": subq
            },
            {
                "$sort": {
                    "wallet_history.modified_on": -1
                }
            },
            {
                "$group": {
                    "_id": 0,
                    "total": {"$sum":1},
                    "data": {
                        "$push": "$wallet_history"
                    },
                }
            },
            {
                "$project": {
                    "_id": 0
                }
            },
            {
                "$unwind": "$data"
            },
            {"$skip": skip},
            {"$limit": limit},
            {
                "$group": {
                    "_id": "$total",
                    "data": {"$push": "$data"}
                }
            },
            {
                "$project": {
                    "total": "$_id",
                    "data": "$data",
                    "_id": 0
                }
            }
        ]

        print(f"Final query is {pipeline}")

        data_list = list(db.wallets.aggregate(pipeline))
        print(data_list)

        if data_list != []:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps({
                # 'message': {
                'total': data_list[0]['total'],
                'page': page + 1,
                'limit': limit,
                'data': data_list[0]['data'],
                # },
                'status_code': 200,
            }, default=json_util.default))
            return
        
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'Not Found!',
                'status_code': 200,
            }, default=json_util.default))