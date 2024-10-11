import json
from io import BytesIO
from time import time
from datetime import datetime
from dbconnection import connect_db
from bson import ObjectId, json_util
import re

db = connect_db()
print((db.list_collection_names()))

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
            "sub_org.id": "63955bbf639cd5b535bebadf",
            "wallet_history.modified_on": {
                "$gte": "2023-12-10T00:00:00.000Z",
                "$lte": "2024-01-11T06:56:06.902Z"
            },
        }
    },
    {
        "$group": {
            "_id": {
                "date": {"$dateToString": { "format": "%Y-%m-%d", "date": {"$toDate": "$wallet_history.modified_on"} }},
                "user": "$wallet_history.modified_by",
                "method": {
                    "$ifNull": ["$wallet_history.added_method", "$wallet_history.deducted_method"]
                }
            },
            "total_collected_amount": {"$sum": {"$sum": ["$wallet_history.added_amount", "$wallet_history.deducted_amount"]}},
        },
    },
    {
        "$match": {
            "_id.method": {
                "$nin": [None, "conveyance wallet", "refunded_from_order", ""]
            },
            "_id.user": {
                "$nin": [None, ""]
            }
        }
    },
    {
        "$group": {
            "_id": "$_id.date",
            "data": {
                "$push": {
                    "user": "$_id.user",
                    "method": "$_id.method",
                    "total_collected_amount": "$total_collected_amount"
                },
            }
        }
    },
    {
        "$project": {
            "date": "$_id",
            "data": "$data",
            "_id": 0
        },
    },
    {
        "$unwind": "$data"
    },
    {
        "$group": {
            "_id": {
                "date": "$date",
                "user": "$data.user"
            },
            "user_data": {
                "$push": {
                    "method": "$data.method",
                    "total_collected_amount": "$data.total_collected_amount",
                }
            },
            "total_amount_by_user": { "$sum": "$data.total_collected_amount" }
        }
    },
    {
        "$group": {
            "_id": "$_id.date",
            "data": {
                "$push": {
                    "user": "$_id.user",
                    "totals": "$user_data",
                    "total_amount_by_user": "$total_amount_by_user",
                }
            },
        }
    },
    {
        "$project": {
            "date": "$_id",
            "data": 1,
            "total_amount_by_user": 1,
            "_id": 0,
        }
    },
    {
        "$addFields": {
            "total_amount_this_day": {
                "$sum": "$data.total_amount_by_user"
            }
        }
    },
    {
        "$sort": {"date": -1}
    },
    {
        "$addFields": {
            "data": {
                "$map": {
                    "input": "$data",
                    "in": {
                        "user": "$$this.user",
                        "totals": "$$this.totals",
                        "total_amount_by_user": "$$this.total_amount_by_user",
                        "user_number": None # or any default value you prefer
                    }
                }
            }
        }
    },
    {
        "$unwind": "$data"  # Unwind the "data" array to make each element a separate document
    },
    {"$addFields": {"user_id": {"$toObjectId": "$data.user"}}},
    {
        "$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "_id",
            "as": "userDetails"
        }
    },
    {
        "$set": {
            "data.user": { "$arrayElemAt": ["$userDetails.name", 0] },
            "data.user_number": {
                    "$ifNull":[
                        {"$arrayElemAt": ["$userDetails.mobile", 0]},
                        {"$arrayElemAt": ["$userDetails.email", 0]}
                    ]
            }
        }
    },
    {
        "$group": {
            "_id": "$date",  # Assuming you have an "_id" field in your original data
            "date": { "$first": "$date" },
            "data": { "$push": "$data" },  # Reassemble the "data" array
            "total_amount_this_day": { "$first": "$total_amount_this_day" },
        }
    },
    {
        "$project": {"_id": 0}
    },
    {
        "$sort": {"date": -1}
    }
]
# pipeline.append({"$count": "total_count"})
# counter = list(db.wallets.aggregate(pipeline))[0]['total_count']
# print(counter)
# print((pipeline))

# print("Removing counter from pipeline\n")
# pipeline.pop()
# print(pipeline)

pipeline = [
    {
                "$match": {
                    "sub_org.id": "633ea4dd3bf4e3aa0f697063"
                }
            },
            {
                "$addFields": {
                    "wallet_history": {
                        "$concatArrays": ["$wallet_add_history", "$wallet_deduction_history"]
                    },
                }
            },
            {
                "$unwind": "$wallet_history"
            },
            {
                "$addFields": {
                    "wallet_history.sub_org_id": "$sub_org.id",
                    "wallet_history.sub_org_name": "$sub_org.name",
                    "wallet_history.method": {
                        "$ifNull": ["$wallet_history.added_method", "$wallet_history.deducted_method"]
                    },
                }
            },
            {
                "$match": {
                    "wallet_history": {
                        "$nin": [None, []]
                    },
                    "wallet_history.method": {
                        "$nin": ["refunded_from_order", "conveyance wallet", None, ""]
                    }
                }
            },
            {
                "$project": {
                    "wallet_history": 1,
                    "_id": 0
                }
            },
            {
                "$group": {
                    "_id": {
                        "sub_org": "$wallet_history.sub_org_id",
                        "sub_org_name": "$wallet_history.sub_org_name"
                    },
                    "cumulative_amount": {
                        "$sum": {
                            "$ifNull": ["$wallet_history.added_amount", "$wallet_history.deducted_amount"]
                        }
                    }
                }
            },
            {
                "$project": {
                    "sub_org": "$_id.sub_org",
                    "sub_org_name": "$_id.sub_org_name",
                    "cumulative_amount": "$cumulative_amount",
                    "_id": 0
                }
            }
]

pipeline = [
    {
        "$match": {
            "modified_by": "641a9b1fea0c1cd5e5ed2a81"
        }
    },
    {
        "$group": {
            "_id": None,
            "total_handovered_amount": {
                "$sum": "$handovered_amount"
            }
        }
    }
]

data = list(db.acc_services.aggregate(pipeline))
total_handovered_amount = data[0]['total_handovered_amount'] if data != [] and 'total_handovered_amount' in data[0] else 0
print((data), total_handovered_amount)
# print(data[0]['cumulative_amount'])