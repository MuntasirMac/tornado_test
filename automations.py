import json, random, string
from random import randint
import os, json, re, openai
from datetime import datetime, timedelta, timezone
from time import time
from decouple import config
from bson import json_util, ObjectId
from product import db
import pandas as pd
from openai import OpenAI
from tornado.web import RequestHandler
from tornado.log import app_log as log
from tornado.ioloop import IOLoop
from concurrent.futures import ThreadPoolExecutor


file_path = '/home/muntasir/samples/Client List of Nerolac Nepal.csv'
openai.api_key = config('openai_api_key')
client = OpenAI(api_key=openai.api_key)
executor = ThreadPoolExecutor(max_workers=4)

def read_file(file_path, sheet=None):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        if sheet:
            return pd.read_excel(file_path, sheet_name=sheet)
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format")

async def insert_product_togpt(file_content):
    messages = [
        {
            "role": "system",
            "content": "You are a data processing assistant."
        }
    ]
    message_content = [
        {
            "role": "user",
            "content": f"""You are an intelligent assistant \
            where you will read the content here, \
            \
            {file_content}
            \
            extract the information of the table into JSON response \
            based on the following Pydantic defined structure \
            class ProductModel(BaseModel):
                product_name: str = Field(..., description="The name of the product")
                category: str = Field(..., description="The category the product belongs to")
                purchase_price: Union[float, int] = Field(..., description="The purchase price of the product")
                selling_price: Union[float, int] = Field(..., description="The cost of the product")
                unit: str
                sku: str
                number_of_stocks: int = Field(..., alias="Number of Stocks", description="The number of available stocks")
                discount: Union[float, int] = Field(..., description="The discount on the product as a percentage")
            Extract the category if exists, else determine the category analysing the product name and the unit by pcs/pack.
            If no discount exists, keep it 0
            According to the products, filling all the fields, return a total list.
            """
        }
    ]
    messages += message_content
    messages.append({"role": "user", "content": "Provide me the full list of products as JSON."})

    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4o mini",
        # stream=True
    )
    # print(dict(chat_completion))
    full_response = chat_completion.choices[0].message.content
    
    full_response = re.sub(r'//.*?\n', '', full_response).strip()
    rbracket = full_response.rfind(']') + 1
    lbracket = full_response.find('[')
    full_response = full_response[:rbracket].strip()
    full_response = full_response[lbracket:].strip()
    print('\nPrinting full response: ', full_response[-3:])
    # fix_incomplete_json(full_response)
    # print(full_response)
    try:
        content = json.loads(full_response)
        print('\nPrinting Content:\n')
        print((content))
        print(len(content), type(content[0]))
        return content
    except:
        return []

async def insert_content_togpt(content, messages):
    messages.append(
        {
            "role": "user",
            "content": str(content)
        },
    )
    # print(messages)
    chat_completion = await IOLoop.current().run_in_executor(executor, lambda: client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        stream=True
    ))
    full_response = await IOLoop.current().run_in_executor(
        executor, lambda: accumulate_stream(chat_completion)
    )

    return full_response

def accumulate_stream(chat_completion):
    # full_response = chat_completion.choices[0].message.content
    full_response = ""
    
    for stream_part in chat_completion:
        full_response += stream_part.choices[0].delta.content or ""
        print(stream_part.choices[0].delta.content or "", end="")
    full_response = re.sub(r'//.*?\n', '', full_response).strip()
    rbracket = full_response.rfind(']') + 1
    lbracket = full_response.find('[')
    full_response = full_response[:rbracket].strip()
    full_response = full_response[lbracket:].strip()
    # print("Full Response is", full_response)
    content = json.loads(full_response)
    print('\nPrinting Content:\n')
    print(type(content), type(content[0]), len(content))

    return content

def chunk_data(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

class PlaceAutomationApi(RequestHandler):
    """
    API to read file and return a json output to insert in the db
    """
    async def get(self):
        data = json.loads(self.request.body.decode("utf-8"))
        message = data['message'] if 'message' in data else None

        messages = [
            {
                "role": "system",
                "content": """You are an intelligent assistant \
                where you will read the content of a tabular file, \
                extract the information of the table into JSON response \
                based on the following Pydantic defined structure \
                class Location(BaseModel):
                    type: str
                    coordinates: List[float]

                class Contact(BaseModel):
                    "name" : str = Field(""),
                    "mobile" : str = Field(""),
                    "email" : str = Field("")

                class EntityModel(BaseModel):
                    name: str = Field(..., alias="name", description="The name of the place")
                    entity_type: str = Field(..., alias="entity_type", description="The category the place belongs to")
                    loc: Location or ""
                    contact: Contact or ""
                    address: str = Field(..., alias="address", description="The address of the place")
                    city: str = Field(..., alias="city", description="city")
                    country: str = Field(..., alias="country", description="The country of the place")
                    is_inventory: bool = Field(default=false)
                    post_code: Optional[str] = ""

                Read all the rows, no rows should be excluded.
                All of them should be returned regardless of the size.
                Extract the place names, addresses, city and country from the file reading all the entries,
                address can be long including city name with it
                cities are mainly districts and not any upazila or sub district(In cases of Bangladesh), extract them carefully.
                Set the location as type: "Point".
                Determine proper location coordinates and set coordinates: [lat, long] from vymaps.com up to 8 digits after decimal point.
                And finally, determine the proper post codes.
                Don't process them by batch, process them all at once.
                """
            }
        ]

        if message:
            messages.append(
                {
                    "role": "user",
                    "content": message
                }
            )
        messages.append(
                {
                    "role": "user",
                    "content": "Give me a full list of places as json by reading all the entries"
                }
            )

        file_content = read_file(file_path)
        file_content = file_content.fillna("")
        # print("File Content is: ", type(file_content))
        chunk_list = list(chunk_data(file_content, 40))
        output = []
        for ch in chunk_list:
            print(ch)
            output_content = await insert_content_togpt(ch.to_string(index=False), messages.copy())
            if output_content:
                output += output_content

        if output:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Ok',
                # 'message': 'Output Given!',
                'total': len(output),
                'data': output,
                'status_code': 200,
            }, default=json_util.default))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'failed',
                'message': 'Output Not Found!',
                'status_code': 200,
            }, default=json_util.default))


class BulkPlaceInsertApi(RequestHandler):
    """
    API to insert into places from llm output
    """
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))

        input_data = list(data['input_data']) if 'input_data' in data else None
        total = len(input_data)
        succeeded = 0
        failed = 0

        if not input_data:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'failed',
                'message': 'Data Not Found!',
                'status_code': 200,
            }, default=json_util.default))

        for instance in input_data:
            payload = {
                "name": instance['name'],
                "entity_type": instance['entity_type'],
                "loc": instance['loc'],
                "address": instance['address'],
                "city": instance['city'],
                "country": instance['country'],
                "post_code": ""
            }

            
            entry = db.entities.insert_one(payload).inserted_id
            print(f"Place {instance['name']} inserted with id: {entry}")
            
            if entry:
                succeeded += 1
            else:
                failed += 1

        self.set_status(202)
        self.set_header('Content-Type', 'application/json')
        return self.finish(json.dumps({
            "status": 202,
            "success": succeeded,
            "failed": failed,
            "total": total,
            "message": f"Total places added {total}, successfully added {succeeded}, failed to add {failed}",
        }, default=json_util.default))
            

class ProductLLMApi(RequestHandler):
    """
    The API to read file and return a json output to insert in the db
    """
    async def post(self):
        """
        The post method
        :param self:
        :param file_path: file path to read file.
        :param category_file_path: category file path to read category file.
        :param unit: unit of the product
        :param message: message to prompt GPT from user.
        """
        try:
            data = json.loads(self.request.body.decode("utf-8"))
        except json.decoder.JSONDecodeError as _:
            self.set_header('Content-Type', 'application/json')
            self.set_status(400)
            self.finish(json.dumps({
                'status': 'error',
                'message': 'Expecting value - {}'.format(_),
                'status_code': 400,
            }, default=json_util.default))
            return
        log.info('crossed 1')

        # user = get_current_user_data(self, self.current_user["user_id"])
        
        message = data['message'] if 'message' in data else None
        file_path = data['file_path'] if 'file_path' in data else None
        category_file_path = data['category_file_path'] if 'category_file_path' in data else None
        unit = data['unit'] if 'unit' in data else None
        sheet_name = data['sheet_name'] if 'sheet_name' in data else None

        file_content = read_file(file_path)
        if sheet_name:
            file_content = read_file(file_path, sheet_name)
        category_file = read_file(category_file_path) if category_file_path else None
        # file_content = file_content.to_string(index=False)
        messages = [
            {
                "role": "system",
                "content": "You are a data processing assistant."
            }
        ]
        message_content = [
            {
                "role": "user",
                "content": f"""You are an intelligent assistant \
                where you will read the content here, \
                \
                {file_content}
                \
                extract the information of the table into JSON response \
                based on the following Pydantic defined structure \
                class ProductModel(BaseModel):
                    product_name: str = Field(..., description="The name of the product")
                    category: str = Field(..., description="The category the product belongs to")
                    purchase_price: Union[float, int] = Field(..., description="The purchase price of the product")
                    selling_price: Union[float, int] = Field(..., description="The cost of the product")
                    unit: str
                    sku: str
                    number_of_stocks: int = Field(..., description="The number of available stocks")
                    discount: Union[float, int] = Field(..., description="The discount on the product as a percentage")
                Extract the category if exists, else determine the category analysing the product name and the unit by pcs/pack.
                If no discount exists, keep it 0
                According to the products, filling all the fields, return a total list.
            """
            }
        ]
        messages += message_content
        if message:
            messages.append({"role": "user", "content": message})
        messages.append({"role": "user", "content": "Provide me the full list of products as JSON."})
        print(len(file_content))
        page_size = 60
        total_pages = len(file_content) // page_size + (1 if len(file_content) % page_size > 0 else 0)
        print("total pages: ", total_pages)
        inserted_content = []
        for page in range(total_pages):
            start = page * page_size
            end = start + page_size
            data_chunk = file_content[start:end]
            output_content = await insert_product_togpt(data_chunk.to_string(index=False))
            inserted_content += output_content
        # output_content = clean_response(inserted_content)

        if inserted_content:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Ok',
                'total': len(inserted_content),
                'message': 'Output Given!',
                'data': inserted_content,
                'status_code': 200,
            }, default=json_util.default))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'failed',
                'message': 'Output Not Found!',
                'status_code': 200,
            }, default=json_util.default))


class BulkProductInsertApi(RequestHandler):
    """
    API to insert into places from llm output
    """
    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))

        input_data = list(data['input_data']) if 'input_data' in data else None
        total = len(input_data)
        succeeded = 0
        failed = 0

        if not input_data:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'failed',
                'message': 'Data Not Found!',
                'status_code': 200,
            }, default=json_util.default))

        for instance in input_data:
            payload = {
                "name": instance['product_name'],
                'product_img': "",
                'product_img_thumb': "",
                'description': "",
                'sku': "",
                'unit_purchase_price': instance['purchase_price'],
                'unit_selling_price': instance['selling_price'],
                'mrp': instance['selling_price'],
                'unit': instance['unit'],
                'tags': [],
                'stock_quantity': instance['number_of_stocks'],
                'ordered_quantity': 0,
                'available_stock': instance['number_of_stocks'],
                'stock_value': round((instance['purchase_price'] * instance['number_of_stocks']), 2),
                'last_closing_qty': 0,
                'last_closing_val': 0,
                'last_closing_time': '',
                'is_parent_product': False,
                'parent_product_id': '',
                'inventory_id': '',
                'entity_id': '',
                'category_id': '',
                'category_name': instance['category'],
                'organization': '',
                'product_status': 'active',
                'created_on': datetime.now(timezone.utc).replace(tzinfo=None),
                'created_by': "641a9b1fea0c1cd5e5ed2a81",
                'modified_on': datetime.now(timezone.utc).replace(tzinfo=None),
                'modified_by': "641a9b1fea0c1cd5e5ed2a81",
                'deleted': False,
            }

            
            entry = db.product.insert_one(payload).inserted_id
            print(f"Place {instance['product_name']} inserted with id: {entry}")
            
            if entry:
                succeeded += 1
            else:
                failed += 1

        self.set_status(202)
        self.set_header('Content-Type', 'application/json')
        return self.finish(json.dumps({
            "status": 202,
            "success": succeeded,
            "failed": failed,
            "total": total,
            "message": f"Total places added {total}, successfully added {succeeded}, failed to add {failed}",
        }, default=json_util.default))

class UserLLMAPI(RequestHandler):
    """
    This API reads the file containing user information and returns a json response
    according to the user model provided in the message passed by llm.
    accessed through
    /app/user-llm
    """
    async def post(self):
        """
        The post method
        :param self:
        :param file_path: file path to read file. 
        :param message: message to prompt GPT from user.
        """
        data = json.loads(self.request.body.decode('utf-8'))
        log.info('crossed 1')

        # user = get_current_user_data(self, self.current_user["user_id"])
        
        message = data['message'] if 'message' in data else None
        file_path = data['file_path'] if 'file_path' in data else None

        if not file_path:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps({
                'status': 'error',
                'message': 'file path is required',
                'status_code': 200,
            }, default=json_util.default))
            return

        log.info(f"file path is: {file_path}")

        file_content = read_file(file_path)
        log.info(f"read file content is: {file_content}")


        messages = [
            {
                "role": "system",
                "content": """You are an intelligent assistant \
                where you will read the content of a tabular file, \
                extract the information of the table into JSON response \
                based on the following Pydantic defined structure \
                class User(BaseModel):
                    name: str = Field(..., alias="name", description="The name of the user")
                    designation: str = Field(..., alias="designation", description="The designation of the user")
                    address: str = Field(..., alias="address", description="The address of the user")
                    country: str = Field(..., alias="country", description="The country of the user")
                    city: str = Field(..., alias="city", description="The city of the user")
                    email: Optional[str] = Field('', alias="email", description="The email of the user")
                    mobile: Optional[str] = Field('', alias="mobile", description="The mobile of the user")
                Remember that, each name should be unique. Take all the names, full address and extract city and determine country from address.
                Cities are mainly districts and not any upazila or sub district(In cases of Bangladesh), extract them carefully.
                Make sure it contains every unique name from the file. Fill other fields according to the row.
                According to the names, filling all the fields, return a total list.
                """
            }
        ]

        if message:
            messages.append(
                {
                    "role": "user",
                    "content": message
                }
            )
        messages.append(
            {
                "role": "user",
                "content": "Provide me the full list of users as JSON."
            }
        )

        inserted_content = await insert_content_togpt(file_content.to_string(index=False), messages)
        log.info(f"inserted content is: {inserted_content}")
        # output_content = clean_response(inserted_content)

        if inserted_content:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Ok',
                'total': len(inserted_content),
                'message': 'Output Given!',
                'data': inserted_content,
                'status_code': 200,
            }, default=json_util.default))
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'failed',
                'message': 'Output Not Found!',
                'status_code': 200,
            }, default=json_util.default))