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


file_path = '/home/muntasir/samples/conveyance.xlsx'
openai.api_key = config('openai_api_key')
client = OpenAI(api_key=openai.api_key)

def read_file(file_path, sheet=None):
	if file_path.endswith('.csv'):
	    return pd.read_csv(file_path)
	elif file_path.endswith('.xlsx'):
		if sheet:
			return pd.read_excel(file_path, sheet_name=sheet)
		return pd.read_excel(file_path)
	else:
	    raise ValueError("Unsupported file format")

def insert_content_togpt(content, messages):

    messages.append(
        {
            "role": "user",
            "content": str(content)
        },
    )
    messages.append({"role": "user", "content": "Provide me the full list of places as JSON."})

    # print(messages)
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        stream=True
    )
    # print(dict(chat_completion))
    full_response = ""  # storing the json response here
    
    for chunk in chat_completion:
        full_response += chunk.choices[0].delta.content or ""
        # pprint(chunk.choices[0].delta.content or "")
        # print(chunk.choices[0].delta.content or "", end="")
    full_response = re.sub(r'//.*?\n', '', full_response).strip()
    rbracket = full_response.rfind(']') + 1
    lbracket = full_response.find('[')
    full_response = full_response[:rbracket].strip()
    full_response = full_response[lbracket:].strip()
    print('\nPrinting full response: ', full_response[-3:])
    # fix_incomplete_json(full_response)
    print((full_response))
    content = json.loads(full_response)
    print('\nPrinting Content:\n')
    print(type(content), type(content[0]))

    return content

class PlaceAutomationApi(RequestHandler):
	"""
	API to read file and return a json output to insert in the db
	"""
	def get(self):
		data = json.loads(self.request.body.decode("utf-8"))
		message = data['message'] if 'message' in data else None

		messages = [
		    {
		        "role": "system",
		        "content": """You are an intelligent and very helpful assistant \
		        where you will read the content of a tabular file, \
		        extract the information of the table into JSON response \
		        based on the following Pydantic defined structure \
		        class Location(BaseModel):
		            type: str
		            coordinates: List[float]

		        class EntityModel(BaseModel):
		            name: str = Field(..., alias="Place Name", description="The name of the place")
		            entity_type: str = Field(..., alias="Type", description="The category the place belongs to")
		            loc: Location
		            address: str = Field(..., alias="Address", description="The address of the place")
		            city: str = Field(..., alias="city", description="city")
		            country: str = Field(..., alias="country", description="The country of the place")
		            post_code: Optional[str] = ""

		        Extract the place names, addresses, city and country from the file,
		        address can be long including city name with it
		        cities are mainly districts and not any upazila or sub district(In cases of Bangladesh), extract them carefully.
		        Set the entity_type as 'Depo'. Set the location as type: "Point".
		        Determine proper location coordinates and set coordinates: [lat, long] from vymaps.com up to full digits fractal point.
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

		file_content = read_file(file_path)
		output_content = insert_content_togpt(file_content.to_string(index=False), messages)

		if output_content:
			self.set_header('Content-Type', 'application/json')
			self.set_status(200)
			return self.finish(json.dumps({
			    'status': 'Ok',
			    'message': 'Output Given!',
			    'data': output_content,
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
    def post(self):
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
        messages = [
            {
                "role": "system",
                "content": f"""You are an intelligent and very helpful assistant \
                where you will read the content of a tabular file, \
                extract the information of the table into JSON response \
                based on the following Pydantic defined structure \
                class ProductModel(BaseModel):
                    product_name: str = Field(..., alias="Product Name", description="The name of the product")
                    category: str = Field(..., alias="Category", description="The category the product belongs to")
                    purchase_price: Union[float, int] = Field(..., alias="Purchase Price (AUD)", description="The purchase price of the product in AUD")
                    selling_price: Union[float, int] = Field(..., alias="Cost (AUD)", description="The cost of the product in AUD")
                    unit: str
                    number_of_stocks: int = Field(..., alias="Number of Stocks", description="The number of available stocks")
                    discount: Union[float, int] = Field(..., alias="Discount (%)", description="The discount on the product as a percentage")
                Determine the category analysing the product name or from the category_file {category_file} and the unit by {unit}.
                According to the products, filling all the fields, return a total list.
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
                    "content": "Provide me the full list of products as JSON."
                }
            )

        inserted_content = insert_content_togpt(file_content.to_string(index=False), messages)
        # output_content = clean_response(inserted_content)

        if inserted_content:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            return self.finish(json.dumps({
                'status': 'Ok',
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