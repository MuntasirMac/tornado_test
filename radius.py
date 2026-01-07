import json
from bson import ObjectId, json_util
from tornado.web import RequestHandler
# from utilities import get_current_user_data
from product import db
from datetime import datetime, timezone
from tornado.log import app_log as log

# user = {
#     "_id": "641a9b1fea0c1cd5e5ed2a81",
#     "name": "Benoy Kumar Roy"
# }
# user = {
#     "_id": "6746a20e400e87cf4ddd5f94",
#     "name": "Admin"
# }
# user = {
#     "_id": "686e5cea801f1c2c3bcf5259",
#     "name": "Easir Arafat Khan"
# }
user = {
    "_id": "674eb8a77ea69af0554ab5a6",
    "name": "Depot Admin 2"
}
# user = {
#             "_id": {
#                 "$oid": "674eb8a77ea69af0554ab5a6"
#             },
#             "name": "Depot Admin 2",
#             "email": "depo2@test.com",
#             "mobile": "",
#             # "email_verified": true,
#             # "mobile_verified": false,
#             "password": {
#                 "$binary": "JDJiJDEyJGtheFlxWEtHQ0xDeS4wc3gyNnZKMHUuNTAyMGNiVURNWVpoUWd3Ry9wSUtzaDFwSG54Si5X",
#                 "$type": "00"
#             },
#             # "profile_img": null,
#             "designation": "RSM",
#             "address": "dhaka",
#             "city": "Dhaka",
#             "country": "Bangladesh",
#             "tz": "Asia/Dhaka",
#             "apps": [
#                 {
#                     "finder_user_id": "",
#                     "finder_org_id": "",
#                     "app_token": "",
#                     "name": ""
#                 }
#             ],
#             "o_player_id": "e39dad7e-8317-4062-b347-9c5da23a756e",
#             # "security_id": null,
#             "organization": {
#                 "$oid": "674eafcdea682e275149c904"
#             },
#             "organizations": [
#                 {
#                     "_id": {
#                         "$oid": "674eafcdea682e275149c904"
#                     },
#                     "name": " Crop Care Solution",
#                     "org_admin": True
#                 }
#             ],
#             "sub_org": {
#                 "id": "674ebc7cea682e275149dd80",
#                 "name": "Depo2",
#                 "sub_org_type_data": {
#                     "name": "Depot",
#                     "seq_no": 1,
#                     "id": "674eb181ea682e275149cbc8"
#                 },
#                 "parent_sub_org_data": {}
#             },
#             "org_admin": True,
#             "is_operator": True,
#             "contact_no": "",
#             "emr_contact_name": "",
#             "lic_no": "",
#             "pin": "017621",
#             "ref_id": "36ZTT3",
#             "exp_date": "",
#             "blood_grp": "",
#             "created_on": {
#                 "$date": 1733212327376
#             },
#             "created_by": "6746a20e400e87cf4ddd5f94",
#             "modified_on": {
#                 "$date": 1758713219511
#             },
#             "modified_by": "6746a20e400e87cf4ddd5f94",
#             # "is_super": false,
#             # "is_staff": false,
#             "is_active": True,
#             "status_updated_on": {
#                 "$date": 1733212327376
#             },
#             "has_perms": [],
#             # "is_inventory": false,
#             "role_id": "676aaae12e16a2c114e33988",
#             "role_name": "RSM",
#             "roles": [
#                 {
#                     "_id": {
#                         "$oid": "676aaae12e16a2c114e33988"
#                     },
#                     "name": "RSM",
#                     "organization": {
#                         "$oid": "674eafcdea682e275149c904"
#                     },
#                     "assigned_date": {
#                         "$date": 1758713219511
#                     },
#                     "active": True
#                 }
#             ],
#             "role_history": [
#                 {
#                     "_id": {
#                         "$oid": "674eafcdea682e275149c906"
#                     },
#                     "name": "org_admin",
#                     "organization": {
#                         "$oid": "674eafcdea682e275149c904"
#                     },
#                     "assigned_date": {
#                         "$date": 1733212327376
#                     },
#                     "active": True
#                 }
#             ],
#             "bank_account_name": "",
#             "bank_account_number": "",
#             "bank_name": "",
#             "department": "",
#             "employee_id": "",
#             "gender": "",
#             # "joining_date": null,
#             "reporting_office": {},
#             "organization_status": "active"
#         }
# organization = '5ef834ca70713e543a64195a'
# organization = '674eafcdea682e275149c904'
# organization = '686e6078801f1c2c3bcf6094'
organization = '674eafcdea682e275149c904'

def query_with_data_level_permission_for_leave_list(self, user, sub_org):
    role_data = db.roles.find_one({'_id': ObjectId(user['role_id'])})
    data_level_permissions = role_data['permissions']['data_level']
    if data_level_permissions['access_all_data'] is False and data_level_permissions["access_suborg_data"] is False and data_level_permissions["access_own_data"] is True:
        print("access only own data")
        try:
            query = {'organization': user['organization'], '$or': [{'created_by': str(user['_id'])}, {'assigned_to': str(user['_id'])}]}
        except Exception:
            return _error_response(self, "error in user query.")
    elif (user['role_name'] == 'org_admin' or data_level_permissions['access_all_data'] is True) and ObjectId.is_valid(sub_org) is True:
        print("access only sub org data for org_admin")
        sub_query_sub_org_ancestors_query = {'sub_org_ancestors': {'$elemMatch': {'sub_org_id': sub_org}}}
        
        try:
            if sub_query_sub_org_ancestors_query != {}:
                query = {'organization': user['organization'], '$or': [{'sub_org_ancestors': {'$elemMatch': {'sub_org_id': sub_org}}}, {'sub_org.id': sub_org}]}
        except Exception:
            return _error_response(self, "error in organization of the user.")
    

    elif (user['role_name'] == 'org_admin' or data_level_permissions['access_all_data'] is True) and ObjectId.is_valid(sub_org) is False:    
        print("access all data as org admin")
        try:
            query = {'organization': user['organization']}
        except Exception:
            return _error_response(self, "error in organization of the user.")
    elif data_level_permissions['access_suborg_data'] is True and ObjectId.is_valid(sub_org) is True:
        print("access only sub org data")
        sub_query_sub_org_ancestors_query = {'sub_org_ancestors': {'$elemMatch': {'sub_org_id': sub_org}}}
        
        try:
            if sub_query_sub_org_ancestors_query != {}:
                query = {'organization': user['organization'], '$or': [{'sub_org_ancestors': {'$elemMatch': {'sub_org_id': sub_org}}}, {'sub_org.id': sub_org}]}
        except Exception:
            return _error_response(self, "error in organization of the user.")
    
    elif data_level_permissions['access_suborg_data'] is True and ObjectId.is_valid(sub_org) is False:
        print("no sub org")
        try:    
            query = {'organization': user['organization']}
        except Exception:
            return _error_response(self, "error in organization of the user.")
    log.info(f'query is {query}')
    return query

class RadiusSettingApi(RequestHandler):
    """
    The Radius Setting API for GET and PUT
        access thru
        /app/radius-setting/([\w\d]+)
        :param OAuth2BaseHandler: 
    """
    def get(self, org_setting_id):
        """
        The GET method
            :param self: 
            :param org_setting_id: 
        """
        print('Radius Setting API GET called')
        # user = get_current_user_data(self, self.current_user['user_id'])
        # organization = str(user['organization'])

        radius_settings = db.org_settings.find_one(
            {'_id': ObjectId(org_setting_id), 'organization': ObjectId(organization)},
            {'radius_settings': 1, '_id': 0}
        )

        radius_settings = radius_settings.get('radius_settings', {})
        if radius_settings:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps({
                'data': radius_settings,
                'status_code': 200,
            }, default=json_util.default))
            return
        
        else:
            self.set_status(200)
            self.finish(json.dumps({
                'message': 'Radius settings not found',
                'status_code': 200,
            }, default=json_util.default))
            return

    def put(self, org_setting_id):
        """
        The PUT method
            :param self: 
            :param is_enabled: bool
            :param radius_in_meters: int
            :param org_setting_id: str
            :return: JSON response with status and message
        """
        print('Radius Setting API PUT called')
        data = json.loads(self.request.body.decode("utf-8"))
        print('crossed 1')
        # user = get_current_user_data(self, self.current_user['user_id'])
        # organization = str(user['organization'])

        org_setting_data = db.org_settings.find_one(
            {'_id': ObjectId(org_setting_id), 'organization': ObjectId(organization)}
        )

        if not org_setting_data:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps({
                'status': 'error',
                'message': 'Organization settings not found',
                'status_code': 200,
            }, default=json_util.default))
            return
        print('crossed 2')

        existing_radius_settings = org_setting_data.get('radius_settings', {})
        if not existing_radius_settings:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps({
                'status': 'error',
                'message': 'Radius settings not found in organization settings',
                'status_code': 200,
            }, default=json_util.default))
            return

        is_enabled = data.get('is_enabled', existing_radius_settings.get('is_enabled', False))
        radius_in_meters = data.get('radius_in_meters', existing_radius_settings.get('radius_in_meters', 0))

        if not isinstance(is_enabled, bool)\
           or not isinstance(radius_in_meters, int)\
           or radius_in_meters < 0:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps({
                'status': 'error',
                'message': 'Invalid input data: is_enabled must be boolean, radius_in_meters must be non-negative integer',
                'status_code': 200,
            }, default=json_util.default))
            return
        
        print('crossed 3')
        # If radius is enabled, ensure radius_in_meters is greater than 0
        if is_enabled and radius_in_meters <= 0:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps({
                'status': 'error',
                'message': 'If radius settings is enabled, radius_in_meters must be greater than 0',
                'status_code': 200,
            }, default=json_util.default))
            return

        # Prepare the payload for updating radius settings
        print('crossed 4')

        radius_settings = {
            'is_enabled': is_enabled,
            'radius_in_meters': radius_in_meters
        }

        payload = {
            'radius_settings': radius_settings,
            'modified_on': datetime.now(timezone.utc).replace(tzinfo=None),
            'modified_by': str(user['_id'])
        }

        status = db.org_settings.find_one_and_update(
            {'_id': ObjectId(org_setting_id), 'organization': ObjectId(organization)},
            {'$set': payload}
        )

        if status:
            if is_enabled:
                print("Inside status")
                entities = db.entities.find(
                    {'organization': ObjectId(organization)}
                )
                count = 0

                for entity in entities:
                    should_update = False
                    
                    if 'expected_radius' not in entity and 'enable_radius' not in entity:
                        should_update = True
                    elif not entity.get('enable_radius', False) and not entity.get('expected_radius', 0):
                        should_update = True
                        
                    if should_update:
                        db.entities.update_one(
                            {'_id': entity['_id']},
                            {'$set': {'expected_radius': radius_in_meters, 'enable_radius': True}}
                        )
                        print(f"Updated entity: {entity['name']} with expected_radius: {radius_in_meters} and enable_radius: True")
                        count += 1

                print(f"\n\nTotal {count} entities updated")

            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps({
                'status': 'success',
                'message': 'Radius settings updated successfully',
                'status_code': 200,
            }, default=json_util.default))
            return
        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(200)
            self.finish(json.dumps({
                'status': 'error',
                'message': 'Unknown error occurred while updating radius settings',
                'status_code': 200,
            }, default=json_util.default))
            return

class  AttendanceLeaveListApi(RequestHandler):
    """
    The Leave List API for List View via GET and adding new attendances leave via POST
        access thru
        /app/attendance-leave-list
        :param OAuth2BaseHandler: 
    """
    def post(self):
        """
        The POST method
            :param self:
            :param leave_start_date: timestamp for date to check the date for roaster plan and bring it for attendance
            :param leave_end_date: timestamp for date to check the date for roaster plan and bring it for attendance
            :param joining_date: timestamp for date to check the date for roaster plan and bring it for attendance
            
            :param leave_type: come from LeaveTypeChoicesApi
            :param leave_request_attachment: attachment file for leave come from FileUploadApi for app and WebFileUploadApi for web
            :param remarks:
            :param created_for: {           
                'id': <user_id>
                'name': name of user 
            }: created_for should be empty for user. But for org_admin will choose user for making attendance leave for user. 

        """   
        try:
            data = self.request.body
            log.info(f"post attendance data is: {data}")
        except json.decoder.JSONDecodeError as _:
            self.set_header('Content-Type', 'application/json')
            self.set_status(400)
            self.finish(json.dumps({
                'status': 'error',
                'message': 'Expecting value - {}'.format(_),
                'status_code': 400,
            }, default=json_util.default))
            return
        log.info(f'data is {data}')
        log.info('crossed 1')
        # request_user = "64c0c51ec6895a51735752f9"
        user = get_current_user_data(self, self.current_user['user_id'])
        user_id = str(user['_id'])
        
        organization = str(user['organization'])
        # sub_org = str(user['sub_org']) if 'sub_org' in user else None
        sub_org = data['sub_org'] if 'sub_org' in data else ''
        org_admin_user = db.users.find_one({"_id": ObjectId(self.current_user['user_id']), 'organizations': {'$elemMatch': {'org_admin': True, '_id': ObjectId(organization)}}})
        
        log.info('crossed 3')
        if 'checkin_image_path' in data and data['checkin_image_path'] != '':
            resp = check_permission(self, organization, service='Attendance with Selfie', allow_add=True, allow_view=True)
            log.info('resp {}'.format(resp))    
            if not resp['status']:
                self.set_header('Content-Type', 'application/json')
                self.set_status(200)
                return self.finish(json.dumps(resp, default=json_util.default))
        else:
            resp = check_permission(self, organization, service='Attendance', allow_add=True, allow_view=True)
            log.info('resp {}'.format(resp))    
            if not resp['status']:
                self.set_header('Content-Type', 'application/json')
                self.set_status(200)
        if not all(key in data for key in ('leave_start_date', 'leave_end_date', 'joining_date', 'leave_type')):
            self.set_header('Content-Type', 'application/json')
            self.set_status(400)
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'all key is not provided',
                'status_code': 400,
            }, default=json_util.default))

        # if data['entity_confirm'] == {} and data['asset_confirm'] == {}:
        #     self.set_header('Content-Type', 'application/json')
        #     self.set_status(400)
        #     return self.finish(json.dumps({
        #         'status': 'error',
        #         'message': 'You need to select either entity data or asset data for attendance',
        #         'status_code': 400,
        #     }, default=json_util.default))

        log.info('crossed 5')
        try:
            if date_validation(self, data['leave_start_date']):  # for check ing mandatary fields
                leave_start_datetime = datetime.fromtimestamp(int(data['leave_start_date'])/1000.0)
                str_leave_start_date = leave_start_datetime.strftime("%d %B %Y")
                only_leave_start_date = datetime.strptime(str_leave_start_date, '%d %B %Y')
        
        except Exception:
                self.set_header('Content-Type', 'application/json')
                self.set_status(200)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': 'Please enter the leave start date',
                    'status_code': 200,
                }, default=json_util.default))


        try:
            if date_validation(self, data['leave_end_date']):  # for check ing mandatary fields
                leave_end_datetime = datetime.fromtimestamp(int(data['leave_end_date'])/1000.0)
                str_leave_end_date = leave_end_datetime.strftime("%d %B %Y")
                only_leave_end_date = datetime.strptime(str_leave_end_date, '%d %B %Y')
        
        except Exception:
                self.set_header('Content-Type', 'application/json')
                self.set_status(200)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': 'Please enter the leave end date',
                    'status_code': 200,
                }, default=json_util.default))

        try:
            if date_validation(self, data['joining_date']):  # for check ing mandatary fields
                joining_datetime = datetime.fromtimestamp(int(data['joining_date'])/1000.0)
                str_joining_date = joining_datetime.strftime("%d %B %Y")
                only_joining_date = datetime.strptime(str_joining_date, '%d %B %Y')
        
        except Exception:
                self.set_header('Content-Type', 'application/json')
                self.set_status(200)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': 'Please enter the joining date',
                    'status_code': 200,
                }, default=json_util.default))

        leave_type = data['leave_type'] if 'leave_type' in data else None
        leave_request_attachment = data['leave_request_attachment'] if 'leave_request_attachment' in data else None
        remarks = data['remarks'] if 'remarks' in data else None
        created_for_id = str(data['created_for']['id']) if 'id' in data['created_for'] else None
        
        if ObjectId.is_valid(created_for_id):
            created_for_user_data = db.users.find_one({'_id': ObjectId(created_for_id)})
            if created_for_user_data:
                created_for_name = created_for_user_data.get('name', '')
                created_for_role_id = created_for_user_data.get('role_id', '')
                created_for_designation = created_for_user_data.get('designation', '')
                created_for_employee_id = created_for_user_data.get('employee_id', '')
                created_for_mobile = created_for_user_data.get('mobile', '')
                created_for_email = created_for_user_data.get('email', '')



        casual_leave_days = 0
        medical_leave_days = 0
        earn_leave_days = 0
        leave_days_count = (leave_end_datetime - leave_start_datetime).days + 1
        query_user = created_for_id if (org_admin_user and created_for_id) else user_id

        if leave_type['type'] == 'CL':
            casual_leave_days = leave_days_count
        elif leave_type['type'] == 'ML':
            medical_leave_days = leave_days_count
        elif leave_type['type'] == 'EL':
            earn_leave_days = leave_days_count

        leave_policy_data = db.user_leave_policies.find_one({'user_id': str(query_user), 'organization': ObjectId(organization), 'leaves.type': leave_type['type']})
        if leave_policy_data:
            leaves = leave_policy_data.get('leaves', [])
            leave_to_modify, index = find_leave_to_modify(leaves, leave_type)
            remaining_leaves = leave_to_modify.get('remaining', 0)

            if leave_days_count > remaining_leaves:
                self.set_header('Content-Type', 'application/json')
                self.set_status(200)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': f'Insufficient numbers of {leave_type["name"]}s. You have {remaining_leaves} remaining leaves.',
                    'status_code': 200
                }, default=json_util.default))
            
            applied = leave_to_modify.get('applied', 0) + leave_days_count
            leaves[index]['applied'] = applied
            db.user_leave_policies.update_one({'user_id': str(query_user), 'organization': ObjectId(organization)}, {'$set': {'leaves': leaves}})

        if only_leave_start_date <= only_leave_end_date and only_leave_end_date < only_joining_date:        
            payload = {
                'leave_start': str_leave_start_date,
                'leave_start_date': only_leave_start_date,
                'leave_end': str_leave_end_date,
                'leave_end_date': only_leave_end_date,
                'joining': str_joining_date,
                'leave_joining_date': only_joining_date,
                'leave_type': leave_type,
                'leave_request_attachment': leave_request_attachment,
                'remarks': remarks,
                'casual_leave_days': casual_leave_days,
                'medical_leave_days': medical_leave_days,
                'earn_leave_days': earn_leave_days,
                'organization': ObjectId(organization) if organization else None,

                'approved': 'pending',
                'approver': '',
                'approver_name': '',
                'approved_on': '',
                'recommended': 'pending',
                'recommender': '',
                'recommender_name': '',
                'recommended_on': '',
                'authorized': 'pending',
                'authorizer': '',
                'authorizer_name': '',
                'authorized_on': '',
                'created_on': datetime.now(timezone.utc).replace(tzinfo=None),
                'created_for': {},
                'created_by': str(user['_id']),
                'created_by_name': str(user['name']),
                'created_by_role_id': str(user['role_id']),
                'modified_on': datetime.now(timezone.utc).replace(tzinfo=None),
                'modified_by': str(user['_id']),
                'modified_by_name': str(user['name']),
                'deleted': False
            }
            sub_org_ancestors = []
            assigned_user_sub_org = {}
            sub_org_descendants = []

            try:
                if sub_org != {} and sub_org != '' and sub_org != []:        
                    sub_org_data = db.sub_orgs.find_one({'_id': ObjectId(sub_org)})
                    if sub_org_data:
                        sub_org_id = str(sub_org_data['_id'])
                        sub_org_name = sub_org_data['name']
                        if sub_org_data['sub_org_type_data']:
                            sub_org_type_data = sub_org_data['sub_org_type_data']
                        else:
                            sub_org_type_data = {}
                        if sub_org_data['parent_sub_org_data']:
                            parent_sub_org_data = sub_org_data['parent_sub_org_data']
                        else:
                            parent_sub_org_data = {}
                        assigned_user_sub_org['id'] = sub_org_id
                        assigned_user_sub_org['name'] = sub_org_name
                        assigned_user_sub_org['sub_org_type_data'] = sub_org_type_data
                        assigned_user_sub_org['parent_sub_org'] = parent_sub_org_data

                        sub_org_type_seq_no = sub_org_type_data['seq_no']
                        sub_org_ancestors = sub_org_ancestors_bfs(self, sub_org_id, sub_org_name, sub_org_type_seq_no)
                        sub_org_descendants = sub_org_descendants_bfs(self, sub_org_id, sub_org_name, sub_org_type_seq_no)

                payload['sub_org_ancestors'] = sub_org_ancestors
                payload['sub_org'] = assigned_user_sub_org
                payload['sub_org_descendants'] = sub_org_descendants
            except Exception:
                log.info('error in ObjectId for sub_org')
                try:
                    payload['sub_org'] = sub_org
                except Exception:
                    log.info('error in ObjectId for sub_org')
                
            if org_admin_user:
                payload['created_for'] = {
                    'id': created_for_id,
                    'name': created_for_name,
                    'mobile': created_for_mobile,
                    'email': created_for_email,
                    'role_id': created_for_role_id,
                    'designation': created_for_designation,
                    'employee_id': created_for_employee_id
                }
            else:
                payload['created_for'] = {
                    'id': user_id,
                    'name': user['name'],
                    'mobile': user['mobile'],
                    'email': user['email'],
                    'role_id': user['role_id'],
                    'designation': user['designation'],
                    'employee_id': user['employee_id']
                }
            procedure_data = db.procedures.find_one({'procedure_for_id':payload['created_for']['role_id'], 'organization': ObjectId(organization)}, {'_id': 1})
            if procedure_data:
                payload['procedure_id'] = str(procedure_data['_id'])
            else:
                payload['procedure_id'] = ''

            status = db.attendance_leaves.insert_one(payload).inserted_id

            if status:
                payload['_id'] = status
                self.set_header('Content-Type', 'application/json')
                self.set_status(201)
                return self.finish(json.dumps({
                    'status': 'success',
                    'message': 'Data successfully inserted!',
                    'status_code': 201,
                    'data': payload,
                }, default=json_util.default))
            else:
                self.set_header('Content-Type', 'application/json')
                self.set_status(400)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': 'Unknown error occurred!',
                    'status_code': 400,
                }, default=json_util.default))
        else:
            if only_leave_start_date > only_leave_end_date:        
                self.set_header('Content-Type', 'application/json')
                self.set_status(200)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': 'leave end date should be greater than leave start date!',
                    'status_code': 200,
                }, default=json_util.default))
            elif only_leave_end_date >= only_joining_date:        
                self.set_header('Content-Type', 'application/json')
                self.set_status(200)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': 'joining date should be greater than leave end date!',
                    'status_code': 200,
                }, default=json_util.default))



    def get(self):
        """
        The get request for attendance leave list
            :param self: will have request.body in post
            :param self.current_user: the current user
            :param start_time: timestamp, within a timeframe in general timestamp divisible by 1000
            :param end_time: timestamp, within a timeframe in general timestamp divisible by 1000
            :param created_for_name: to search by created_for name
            :param tab_name: to filter by tab name
            :param approved: to search by approved status
            :param recommended: to search by recommended status
            :param authorized: to search by authorized status
            :param need_approval_leave_by_me_action: to search by need_approval_leave_by_me_action
            :param page:
            :param limit: 
            :param sort_by: defaults to created_on
            :param sort_type:
            :param d: for deleted either True or False 
        """
        log.info('Current User')
        log.info(self.current_user)
        log.info('crossed 1')
        # user = get_current_user_data(self, self.current_user['user_id'])
        user_id = str(user['_id'])
        
        # organization = str(user['organization'])
        sub_org = str(user['sub_org']) if 'sub_org' in user else None

        # org_admin_user = db.users.find_one({"_id": ObjectId(self.current_user["user_id"]), 'organizations': {'$elemMatch': {'org_admin': True, '_id': ObjectId(organization)}}})

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

        if start_time:
            if date_validation(self, start_time):  # for check ing mandatary fields
                start_time = datetime.fromtimestamp(int(start_time)/1000.0)

        if end_time:
            if date_validation(self, end_time):  # for check ing mandatary fields
                end_time = datetime.fromtimestamp(int(end_time)/1000.0)

        sort_by = self.get_argument('sort_by', 'created_on')
        sort_type = self.get_argument('sort_type', 'dsc')
        sub_org = self.get_argument('sub_org', None)
        created_for_name = self.get_argument('created_for_name', None)
        approved = self.get_argument('approved', None)
        recommended = self.get_argument('recommended', None)
        authorized = self.get_argument('authorized', None)
        tab_name = self.get_argument('tab_name', None)
        need_approval_leave_by_me_action = self.get_argument('need_approval_leave_by_me_action', '')

        skip = limit * page

        deleted = bool(self.get_argument('d', False))
        log.info(f'deleted is {deleted}')
        # try:
        #     if org_admin_user:
        #         query = {'organization': ObjectId(organization)}
        #     elif org_admin_user == None:
        #         query = {'created_by': user_id}
        #     elif user['is_staff'] == True or user['is_super'] == True:
        #         query = {}
        # except Exception as e:
        #     log.info('error in query {}'.format(e))
        log.info('organization is {}'.format(organization))
        query = {}
        # sub_org_ids = []

        # query, sub_org_ids = query_with_data_level_permission_for_attendance_list(self, user, sub_org)
        procedure_datas = list(db.procedures.find({'organization': ObjectId(organization), 'name': 'attendance leave'}))
        # print("Procedure Data", procedure_datas)
        # query = query_with_data_level_permission_for_leave_list(self, user, sub_org)
        # query = query_with_data_level_permission_for_leave_list(self, user, sub_org='674ebd56ea682e275149deed')
        query = {'organization': ObjectId(organization)}
        print("QUERY in API", query)
        if user_id and skip >= 0:
            log.info('found user_id and skip>0')
            # ('name', 'details', 'start_time', 'end_time', 'start_loc', 'end_loc', 'contact_no', 'contact_name', 'price', 'completed', 'accepted')
            subquery = []
            subq = {}

            if deleted:
                subq['deleted'] = True
                subquery.append(subq)
            else:
                subq['deleted'] = False
                subquery.append(subq)

            if start_time and end_time:
                subq = {}
                subq['leave_start_date'] = {'$gte': start_time, "$lte": end_time}
                subq['leave_end_date'] = {'$gte': start_time, '$lte': end_time}
                subquery.append(subq)

            if tab_name == 'default':
                pass

            elif tab_name == 'my_leaves':
                subquery.append({"created_for.id": user_id})

            elif tab_name in ['need_approval_leave_by_me', 'approved_leaves_by_me']:
                stage_filters = []

                for procedure_data in procedure_datas:
                    procedure_id = str(procedure_data["_id"])
                    recommenders = procedure_data.get("recommenders", [])
                    approvers = procedure_data.get("approvers", [])
                    authorizers = procedure_data.get("authorizers", [])

                    if tab_name == 'need_approval_leave_by_me':
                        if need_approval_leave_by_me_action:
                            stage_map = {
                                "recommended": ("recommended", recommenders, "recommender_id"),
                                "approved": ("approved", approvers, "approver_id"),
                                "authorized": ("authorized", authorizers, "authorizer_id"),
                            }

                            field, stage_list, key = stage_map.get(need_approval_leave_by_me_action, (None, [], None))

                            if field and any(s.get(key) == user_id for s in stage_list):
                                stage_filters.append({
                                    "procedure_id": procedure_id,
                                    field: {"$eq": "pending"}
                                })

                        else:
                            if any(r.get("recommender_id") == user_id for r in recommenders):
                                stage_filters.append({
                                    "procedure_id": procedure_id,
                                    "recommended": {"$eq": "pending"}
                                })
                            if any(a.get("approver_id") == user_id for a in approvers):
                                stage_filters.append({
                                    "procedure_id": procedure_id,
                                    "approved": {"$eq": "pending"}
                                })
                            if any(a.get("authorizer_id") == user_id for a in authorizers):
                                stage_filters.append({
                                    "procedure_id": procedure_id,
                                    "authorized": {"$eq": "pending"}
                                })

                    elif tab_name == 'approved_leaves_by_me':
                        if any(r.get("recommender_id") == user_id for r in recommenders):
                            stage_filters.append({
                                "procedure_id": procedure_id,
                                "recommended": {"$in": ["approved", "rejected"]}
                            })
                        if any(a.get("approver_id") == user_id for a in approvers):
                            stage_filters.append({
                                "procedure_id": procedure_id,
                                "approved": {"$in": ["approved", "rejected"]}
                            })
                        if any(a.get("authorizer_id") == user_id for a in authorizers):
                            stage_filters.append({
                                "procedure_id": procedure_id,
                                "authorized": {"$in": ["approved", "rejected"]}
                            })

                print(f"stage_filters is {stage_filters}")
                if tab_name == 'need_approval_leave_by_me' and need_approval_leave_by_me_action and not stage_filters:
                    subquery.append({"_id": None})
                elif stage_filters:
                    subquery.append({"$or": stage_filters})
            
            if created_for_name:
                subq = {}
                subq['created_for.name'] = {'$regex': created_for_name, '$options': 'i'}
                subquery.append(subq)
            
            if approved:
                subq = {}
                subq['approved'] = {"$regex": approved, '$options': 'i'}
                subquery.append(subq)

            if recommended:
                subq = {}
                subq['recommended'] = {"$regex": recommended, '$options': 'i'}
                subquery.append(subq)

            if authorized:
                subq = {}
                subq['authorized'] = {"$regex": authorized, '$options': 'i'}
                subquery.append(subq)
            
            try:
                if len(subquery) > 0:
                    query['$and'] = subquery

            except Exception as e:
                log.info('error in orgnization {}'.format(e))
                
            print('query built was ')
            print(query)
            # query
            
            # if sub_org_ids == []:
            #     print("if no sub org")
            #     print("query is", query)
            #     count = db.attendance_leaves.find(query).count()
            #     data_list = db.attendance_leaves.find(query).skip(skip).limit(
            #         limit).sort('{}'.format(sort_by), 1 if sort_type == 'asc' else -1)
            # else:
            #     print("if sub org")
            #     print("query is", query)
            #     sub_org_sub_query = {'sub_org.id': {'$in': []}}
            #     for sub_org_id in sub_org_ids:
            #         sub_org_sub_query['sub_org.id']['$in'].append(sub_org_id)
            #     query['$and'].append(sub_org_sub_query)
            #     log.info("FINAL QUERY IS: ", query)
            #     count = db.attendance_leaves.find(query).count()
            #     data_list = db.attendance_leaves.find(query).skip(skip).limit(
            #         limit).sort('{}'.format(sort_by), 1 if sort_type == 'asc' else -1)
            count = db.attendance_leaves.count_documents(query)
            data_list = db.attendance_leaves.find(query).skip(skip).limit(
                limit).sort('{}'.format(sort_by), 1 if sort_type == 'asc' else -1)
        data = list(data_list)

        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(json.dumps({
            # 'message': {
            'total': count,
            'page': page + 1,
            'limit': limit,
            'data': data,
            # },
            'status_code': 200,
        }, default=json_util.default))
        return
