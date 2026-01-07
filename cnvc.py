import json
import os
import random
import weasyprint
import pytz
from xlsxwriter import Workbook
from render import pdf_assets
from datetime import datetime, timedelta, timezone
from io import BytesIO
from json.decoder import JSONDecodeError
from random import randint
from time import time
from num2words import num2words

# from base import OAuth2BaseHandler, BaseHandler
from tornado.web import RequestHandler
from bson import ObjectId, errors, json_util
from tornado.log import app_log as log
from product import db

from reportlab.lib import colors, pagesizes
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table)
from reportlab.graphics.shapes import Drawing, Rect, Line
# from utilities.blocks import user_tz_time, org_tz_time
def org_tz_time(self, utc_time, organization):
    org_data = db.organizations.find_one({'_id': ObjectId(organization)})
    timezone_name = org_data['timezone_name']
    tz = pytz.timezone(timezone_name)
    offset = utc_time.astimezone(tz).utcoffset()
    dst_offset = utc_time.astimezone(tz).dst()
    dst_aware_time_by_org_timezone = utc_time + offset + dst_offset
    return dst_aware_time_by_org_timezone

user = {
            "_id": "641a9b1fea0c1cd5e5ed2a81",
            "name": "Benoy Kumar Roy",
            "org_admin": True,
            "organization": ObjectId('5ef834ca70713e543a64195a')
        }
organization = '5ef834ca70713e543a64195a'

class ConveyanceBillPDF(RequestHandler):
    """
        ConveyanceBillPDF currently takes four parameters
        :param from:
        :param to:
        :param bill_ids: bill ids of selected conveyance bills
        
        access with: /app/conveyance_bill_pdf
    """


    # REQUIRED_FIELD = ('from', "to", "bill_ids")
    REQUIRED_FIELD = ("bill_ids",)
    DAY_FORMAT = '%d %B, %Y'
    DEFAULT_DATETIME_FORMAT = '%A %d %B %Y %I:%M:%S %p'
    table_style = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                   ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
                   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                   ('LINEBELOW', (0, 0), (-1, 0), 1, colors.grey),
                   ('FONTNAME', (0, 0), (-1, 0), 'Vera'),
                   ('LINEBELOW', (0, -1), (-1, -1), 1, colors.grey),
                   ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey,
                                                         colors.white])]
    table_style2 = [('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                   ('LINEABOVE', (0, 0), (-1, 0), 1, colors.white),
                   ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                   ('FONTNAME', (0, 0), (-1, 0), 'Vera'),
                   ('LINEBELOW', (0, -1), (-1, -1), 1, colors.white)]

    def page_size(self, cn, doc):
        cn.saveState()
        cn.setFont('Vera', 9)
        conveyance_logo = os.path.join(
            os.getcwd(), 'static_www', 'logo.png')
        # cn.drawImage(conveyance_logo, 30, 50, 50, 30)
        cn.drawString(cm, 1 * cm, "Page %d %s" %
                      (doc.page, "Checbox"))
        cn.restoreState()

    def post(self):
        data = json.loads(self.request.body.decode("utf-8"))

        # if self.current_user is not None:
        #     # JUST in case
        #     user = db.users.find_one(
        #         {"_id": ObjectId(self.current_user["user_id"])},
        #         {"organization": 1, "sub_org": 1,
        #          "is_operator": 1, "is_driver": 1, "is_staff": 1,
        #          "is_super": 1, "org_admin": 1, "name": 1})
        # else:
        #     user = None
        # if user is None:
        #     return self.finish(json.dumps({
        #         'status': 'error',
        #         'message': 'You are not a valid user!',
        #         'status_code': 400,
        #     }, default=json_util.default))
        user = {
            "_id": "641a9b1fea0c1cd5e5ed2a81",
            "name": "Benoy Kumar Roy",
            "org_admin": True,
            "organization": ObjectId('5ef834ca70713e543a64195a')
        }
        organization = '5ef834ca70713e543a64195a'

        is_org_admin = user.get("org_admin", False)

        # frm = data['from']
        # _to = data["to"]
        bill_ids = data["bill_ids"]

        # try:
        #     frm = datetime.fromtimestamp(int(float(frm)))
        # except ValueError:
        #     self.set_status(404)
        #     return self.finish(json.dumps({
        #         'status': 'error',
        #         'message': 'Invalid date on from',
        #         'status_code': 404,
        #     }, default=json_util.default))

        # try:
        #     _to = datetime.fromtimestamp(int(float(_to)))
        # except ValueError:
        #     self.set_status(404)
        #     return self.finish(json.dumps({
        #         'status': 'error',
        #         'message': 'Invalid date on to',
        #         'status_code': 404,
        #     }, default=json_util.default))

        # if frm > _to:
        #     self.set_status(404)
        #     return self.finish(json.dumps({
        #         'status': 'error',
        #         'message': 'from date cannot be after _to date.',
        #         'status_code': 404,
        #     }, default=json_util.default))


        org_id = '5ef834ca70713e543a64195a'
        # try:
        #     ObjectId(org_id)
        # except errors.InvalidId:
        #     self.set_status(404)
        #     return self.finish(json.dumps({
        #         'status': 'error',
        #         'message': 'Invalid organization id',
        #         'status_code': 404,
        #     }, default=json_util.default))

        organization = db.organizations.find_one(
            {"_id": ObjectId(org_id)})
        if organization is None:
            self.set_status(404)
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'Invalid organization id',
                'status_code': 404,
            }, default=json_util.default))

        organization_address = "{}, {}, {}".format(organization.get("address",
                                                                    ""),
                                                   organization.get(
                                                       "city", ""),
                                                   organization.get("country",
                                                                    ""))

        buff = BytesIO()
        doc = SimpleDocTemplate(buff, pagesize=portrait(A4),
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)

        registerFont(TTFont('Vera', 'Vera.ttf'))
        registerFont(TTFont('Vera Bold', 'VeraBd.ttf'))
        registerFont(TTFont('Vera Italic', 'VeraIt.ttf'))
        registerFont(TTFont('Vera Bold-Italic', 'VeraBI.ttf'))

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Heading-1',
                                  fontName='Vera Bold',
                                  fontSize=16,
                                  leading=12))
        styles.add(ParagraphStyle(name='Heading-2',
                                  fontName='Vera Bold',
                                  fontSize=14,
                                  leading=12))
        styles.add(ParagraphStyle(name='Heading-3',
                                  fontName='Vera Bold',
                                  fontSize=12,
                                  leading=12))
        styles.add(ParagraphStyle(name='TextNormal',
                                  fontName='Vera',
                                  fontSize=9,
                                  leading=12))
        styles.add(ParagraphStyle(name='TableHeading-1',
                                  fontName='Vera Bold',
                                  fontSize=5,
                                  leading=10,
                                  alignment=TA_CENTER,))
        styles.add(ParagraphStyle(name='TableNormal',
                                  fontName='Vera',
                                  fontSize=4,
                                  leading=10,
                                  alignment=TA_CENTER,))
        styles.add(ParagraphStyle(name='Normal_CENTER',
                                  parent=styles['Normal'],
                                  fontName='Vera',
                                  wordWrap='LTR',
                                  alignment=TA_CENTER,
                                  fontSize=12,
                                  leading=13,
                                  borderPadding=0,
                                  leftIndent=0,
                                  rightIndent=0,
                                  spaceAfter=0,
                                  spaceBefore=0,
                                  splitLongWords=True,
                                  spaceShrinkage=0.05,
                                  ))
        styles.add(ParagraphStyle(name='Normal_RIGHT',
                                  parent=styles['Normal'],
                                  fontName='Vera',
                                  wordWrap='LTR',
                                  alignment=TA_RIGHT,
                                  fontSize=7,
                                  leading=13,
                                  borderPadding=0,
                                  leftIndent=0,
                                  rightIndent=0,
                                  spaceAfter=0,
                                  spaceBefore=0,
                                  splitLongWords=True,
                                  spaceShrinkage=0.05,
                                  ))

        styles.add(ParagraphStyle(name='Normal_LEFT',
                                  parent=styles['Normal'],
                                  fontName='Vera',
                                  wordWrap='LTR',
                                  alignment=TA_LEFT,
                                  fontSize=7,
                                  leading=13,
                                  borderPadding=0,
                                  leftIndent=0,
                                  rightIndent=0,
                                  spaceAfter=0,
                                  spaceBefore=0,
                                  splitLongWords=True,
                                  spaceShrinkage=0.05,
                                  ))

        self.set_status(200)

        # Calculate data for some heading fields

        new_bill_report_no = str(random.randint(10000000, 99999999))
        total_sum_of_bills = 0

        for bill_id in bill_ids:
            if is_org_admin:
                # Can Download All Bill n Requisition
                bill_parameter = {"$and": [
                    {"_id": ObjectId(bill_id)},
                    {"misc_bill_type.name": "Conveyance"}
                ]}

            else:
                # Can Download only users Nill n Requisition
                bill_parameter = {"$and": [
                    {"_id": ObjectId(bill_id)},
                    {"misc_bill_type.name": "Conveyance"},
                    {"created_by": str(user["_id"])}
                ]}

            bill_data = db.bills.find_one(bill_parameter)
            
            if bill_data:
                total_price = bill_data.get("total_price", "")
                total_sum_of_bills = total_sum_of_bills + total_price
            
        
        elements = list()

        elements.append(
            Paragraph("Powered by",
                      styles['Normal_RIGHT']))
        org_logo = os.path.join(
            os.getcwd(), 'static_www', 'logo.png')
        org_logo_img = Image(org_logo, 50, 30, hAlign='RIGHT')
        elements.append(org_logo_img)
        org_name = organization.get("name", "")
        elements.append(
            Paragraph(org_name, styles["Normal_LEFT"]))
        elements.append(
            Paragraph('Conveyance', styles["Normal_LEFT"]))

        
        elements.append(
            Paragraph("Generated by %s" % user.get("name"),
                        styles["Normal_LEFT"]))

        elements.append(
            Paragraph(
            "Generated on %s" % (
                org_tz_time(self, datetime.now(timezone.utc).replace(tzinfo=None), str(organization['_id'])).strftime(self.DEFAULT_DATETIME_FORMAT)), styles['Normal_LEFT']))

        elements.append(
            Paragraph(f"Number of Bills: {len(bill_ids)} "  ,
                        styles["Normal_LEFT"]))
 

        elements.append(
            Paragraph(f"Bill No: {new_bill_report_no}",
                        styles["Normal_LEFT"]))


        elements.append(
            Paragraph(f"Total Amount: {total_sum_of_bills}",
                        styles["Normal_LEFT"]))

        elements.append(
            Paragraph(f"In Words: {num2words(total_sum_of_bills).capitalize()} Tk. Only",
                        styles["Normal_LEFT"]))
        # elements.append(
        #     Paragraph(org_tz_time(self, datetime.now(timezone.utc).replace(tzinfo=None), str(organization['_id'])).strftime('%A %d %B %Y %I:%M %p'), styles["Normal_LEFT"]))

        # elements.append(
        #     Paragraph(organization_address, styles["Normal_RIGHT"]))

        elements.append(Spacer(8 * inch, 0.50 * inch))

        data = [
                    [
                        # Paragraph("Serial No.", styles["TableHeading-1"]),
                        Paragraph("Bill Date", styles["TableHeading-1"]),
                        Paragraph("Entry No", styles["TableHeading-1"]),
                        Paragraph("Bill Name", styles["TableHeading-1"]),
                        Paragraph("Bill For", styles["TableHeading-1"]),
                        Paragraph("Billing Purpose", styles["TableHeading-1"]),
                        Paragraph("Started Time", styles["TableHeading-1"]),
                        Paragraph("Started Location", styles["TableHeading-1"]),
                        Paragraph("Completed Time", styles["TableHeading-1"]),
                        Paragraph("Completed Location", styles["TableHeading-1"]),
                        Paragraph("Total Requested Amount", styles["TableHeading-1"]),
                        
                    ]
                ]

        data2 = [
                    [
                        Paragraph("", styles["TableHeading-1"]),
                        Paragraph("", styles["TableHeading-1"]),
                        Paragraph("", styles["TableHeading-1"]),
                        Paragraph("", styles["TableHeading-1"]),   
                    ]
                ]
        data2.extend([[
                    Paragraph('prepared by',
                              styles["TableNormal"]),
                    Paragraph('authorized by', styles["TableNormal"]),
                    Paragraph('approved by', styles["TableNormal"]),
                    Paragraph('received by', styles["TableNormal"]),
                ]])

        # new_bill_report_no = str(random.randint(10000000, 99999999))
        total_sum_of_bills = 0
        bill_report_numbers = []
        
        for bill_id in bill_ids:
            if is_org_admin:
                # Can Download All Bill n Requisition
                bill_parameter = {"$and": [
                    {"_id": ObjectId(bill_id)},
                    {"misc_bill_type.name": "Conveyance"}
                ]}

            else:
                # Can Download only users Nill n Requisition
                bill_parameter = {"$and": [
                    {"_id": ObjectId(bill_id)},
                    {"misc_bill_type.name": "Conveyance"},
                    {"created_by": str(user["_id"])}
                ]}

            bill_data = db.bills.find_one(bill_parameter)
            log.info(f"bill data is {bill_data}")
            if bill_data:
                if 'bill_report_no' in bill_data and bill_data['bill_report_no'] != '' and bill_data['bill_report_no']:
                    bill_report_numbers.append(bill_data['bill_report_no'])
                else:
                    log.info(f'bill report no is not exist')
                    bill_update = db.bills.find_one_and_update({'_id': ObjectId(bill_id)}, {'$set': {'bill_report_no': new_bill_report_no}})
            else:
                 return self.finish(json.dumps({
                    'status': 'error',
                    'message': f'Bill data is not found for {bill_id} parameters',
                    'status_code': 400,
                }, default=json_util.default))           
                # serial_no = serial_no + 1
            items = bill_data.get("items", [])
            bill_for = ''
            for item in items:
                if 'item' in item and 'name' in item['mtype'] and item['item'] != item['mtype']['name']  and item['item'] != '':
                    bill_for = item['item'] + ', ' + item['mtype']['name']
                elif 'item' in item and 'name' in item['mtype'] and item['item'] != item['mtype']['name']  and item['item'] == '':
                    bill_for = item['mtype']['name']
                elif 'item' in item and 'name' in item['mtype'] and item['item'] == item['mtype']['name'] and item['item'] != '':
                    bill_for = item['item']
                elif 'item' in item and 'name' in item['mtype'] and item['item'] == item['mtype']['name'] and item['item'] == '':
                    bill_for = item['mtype']['name']
            

            bill_name = bill_data.get("name", None)
            bill_no = bill_data.get("bill_no", None)
            created_by = bill_data.get("created_by", None)
            created_on = bill_data.get("created_on", None)
            if created_on is not None:
                created_on = created_on.strftime(self.DAY_FORMAT)
            supplier = bill_data.get("supplier", {})
            if supplier != {} and supplier !='' and supplier:
                supplier_name = supplier.get("name", "")
            else:
                supplier_name = ""
            # task_name = bill_data.get("task_name", "")
            task_id = bill_data.get("task_id", "")
            
            log.info(f'created_by is {created_by}')

            if created_by is not None:
                created_by = db.users.find_one(
                    {"_id": ObjectId(created_by)},
                    {"name": 1})
                if created_by == None:
                    log.info(f'User {created_by} may not exist')
                    return self.finish(json.dumps({
                        'status': 'error',
                        'message': f'User {created_by} may not exist',
                        'status_code': 400,
                    }, default=json_util.default))
                else:
                    created_by_name = created_by.get("name", "")
                
            
            started_on = 'NA'
            started_loc_name = 'NA'
            completed_on = 'NA'
            completed_loc_name = 'NA'
            try:
                task_data = db.tasks.find_one({'_id': ObjectId(task_id)})
                if task_data:
                    started_on = task_data['started_on']
                    started_loc_name = task_data['started_loc_name']
                    completed_on = task_data['completed_on']
                    completed_loc_name = task_data['completed_loc_name']
                else:
                    bill_name = "No Task Linked"
            except:
                task_data = {}
                bill_name = "No Task Linked"
                started_on = 'NA'
                started_loc_name = 'NA'
                completed_on = 'NA'
                completed_loc_name = 'NA'
            total_price = bill_data.get("total_price", "")
            total_sum_of_bills = total_sum_of_bills + total_price
            
                

            if len(items) == 0:
                data.extend([[
                    # Paragraph("", styles["TableNormal"]),
                    Paragraph(created_on, styles["TableNormal"]),
                    Paragraph(bill_no,
                            styles["TableNormal"]),
                    Paragraph(bill_name,
                            styles["TableNormal"]),
                    Paragraph(bill_for,
                            styles["TableNormal"]),
                    Paragraph(f"by {created_by_name}", styles["TableNormal"]),
                    Paragraph(str(started_on), styles["TableNormal"]),
                    Paragraph(str(started_loc_name), styles["TableNormal"]),
                    Paragraph(str(completed_on), styles["TableNormal"]),
                    Paragraph(str(completed_loc_name), styles["TableNormal"]),
                    Paragraph(str(total_price), styles["TableNormal"]),
                ]])
            else:
                # TODO: there was no item list on the db when testing.
                for item in items:
                    item_name = item.get("item", "")
                    item_price = item.get("price", "")
                    item_qty = item.get("qty", "")
                    item_unit = item.get("unit", "")

                    data.extend([[
                    # Paragraph(serial_no, styles["TableNormal"]),
                    Paragraph(created_on, styles["TableNormal"]),
                    Paragraph(bill_no,
                            styles["TableNormal"]),
                    Paragraph(bill_name,
                            styles["TableNormal"]),
                    Paragraph(bill_for,
                            styles["TableNormal"]),
                    Paragraph(f"by {created_by_name}", styles["TableNormal"]),
                    Paragraph(str(started_on), styles["TableNormal"]),
                    Paragraph(str(started_loc_name), styles["TableNormal"]),
                    Paragraph(str(completed_on), styles["TableNormal"]),
                    Paragraph(str(completed_loc_name), styles["TableNormal"]),
                    Paragraph(str(total_price), styles["TableNormal"]),
                    ]])     

        data.extend([[
                # Paragraph(serial_no, styles["TableNormal"]),
                Paragraph("", styles["TableNormal"]),
                Paragraph("", styles["TableNormal"]),
                Paragraph("", styles["TableNormal"]),
                Paragraph("", styles["TableNormal"]),
                Paragraph("", styles["TableNormal"]),
                Paragraph("", styles["TableNormal"]),
                Paragraph("", styles["TableNormal"]),
                Paragraph("", styles["TableNormal"]),
                Paragraph("", styles["TableNormal"]),
                Paragraph(f"Total Sum: {str(total_sum_of_bills)}", styles["TableNormal"]),
                ]])
    


        table = Table(data=data, style=self.table_style, repeatRows=1)


        table2 = Table(data=data2, style=self.table_style2)

        elements.append(table)
        d = Drawing(800, 100)
        # Line return (self.x1, self.y1, self.x2, self.y2)
        d.add(Line(10, 10, 110, 10))

        d.add(Line(120, 10, 220, 10))

        d.add(Line(230, 10, 330, 10))

        d.add(Line(340, 10, 440, 10))

        # d.add(Line(20, 10, 150, 10))

        # d.add(Line(190, 10, 320, 10))

        # d.add(Line(360, 10, 490, 10))

        # d.add(Line(530, 10, 660, 10))




        elements.append(d)
        # # self._canvas.drawString(x, y, text, mode=textRenderMode or None)
        # d.add(Line(20, -20, 140, -20))

        # d.add(Line(180, -20, 300, -20))

        # d.add(Line(340, -20, 460, -20))

        # d.add(Line(500, -20, 620, -20))


        elements.append(table2)
        elements.append(Spacer(1, 20))
        elements.append(
            Paragraph("Bill Images/Receipts", styles["Heading-3"]))
        elements.append(Spacer(1, 10))
        # Collect bill images
        bill_images = []
        for bill_id in bill_ids:
            if is_org_admin:
                bill_parameter = {"$and": [
                    {"_id": ObjectId(bill_id)},
                    {"misc_bill_type.name": "Conveyance"}
                ]}
            else:
                bill_parameter = {"$and": [
                    {"_id": ObjectId(bill_id)},
                    {"misc_bill_type.name": "Conveyance"},
                    {"created_by": str(user["_id"])}
                ]}

            bill_data = db.bills.find_one(bill_parameter)
            
            if bill_data:
                bill_no = bill_data.get("bill_no", "")
        
                # Check first image
                bill_image_path_1 = bill_data.get("bill_image_path_1", "")
                if bill_image_path_1 and os.path.exists(bill_image_path_1):
                    try:
                        bill_img_1 = Image(bill_image_path_1, width=180, height=120)
                        bill_images.append({
                            'image': bill_img_1,
                            'caption': f"Bill No: {bill_no} - Image 1"
                        })
                    except Exception as e:
                        log.error(f"Error loading image {bill_image_path_1}: {e}")
                
                # Check second image
                bill_image_path_2 = bill_data.get("bill_image_path_2", "")
                if bill_image_path_2 and os.path.exists(bill_image_path_2):
                    try:
                        bill_img_2 = Image(bill_image_path_2, width=180, height=120)
                        bill_images.append({
                            'image': bill_img_2,
                            'caption': f"Bill No: {bill_no} - Image 2"
                        })
                    except Exception as e:
                        log.error(f"Error loading image {bill_image_path_2}: {e}")

        # Add images to PDF
        if bill_images:
            # Create image table (2 images per row)
            image_table_data = []
            for i in range(0, len(bill_images), 2):
                image_row = []
                caption_row = []
                
                # First image
                img_data = bill_images[i]
                image_row.append(img_data['image'])
                caption_row.append(Paragraph(img_data['caption'], styles["Normal_CENTER"]))
                
                # Second image and caption (if exists)
                if i + 1 < len(bill_images):
                    img_data = bill_images[i + 1]
                    image_row.append(img_data['image'])
                    caption_row.append(Paragraph(img_data['caption'], styles["Normal_CENTER"]))
                else:
                    # Fill empty cells
                    image_row.append(Paragraph("", styles["TableNormal"]))
                    caption_row.append(Paragraph("", styles["TableNormal"]))
                
                image_table_data.append(image_row)
                image_table_data.append(caption_row)
            
            # Create image table
            image_table_style = [
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]
            
            image_table = Table(image_table_data, style=image_table_style)
            elements.append(image_table)
        else:
            elements.append(Paragraph("No bill images available", styles["TextNormal"]))



        if bill_report_numbers == []:
            doc.build(elements,
                    onFirstPage=self.page_size,
                    onLaterPages=self.page_size)
            pdf = buff.getvalue()  # do not remove this variable
            buff.close()
            
            random_num = time() * 1000 * randint(2, 200)
            filename = f"conveyance_bill_{random_num}.pdf"
            filepath = os.path.join(
                os.getcwd(), "pdf", "bill_pdf", filename)
            with open(filepath, "wb") as outfile:
                # Copy the BytesIO stream to the output file
                outfile.write(pdf)
            conveyance_pdf_filepath = f"pdf{filepath.split('/pdf')[1]}"
            file_upload_path_data = {
                "bill_report_url": conveyance_pdf_filepath
            }
            for bill_id in bill_ids:
                db.bills.find_one_and_update({'_id': ObjectId(bill_id)}, {'$set': file_upload_path_data})
            log.info(f"pdf path is {conveyance_pdf_filepath}")
            # self.set_header('Content-Type', 'application/json')
            # self.set_status(201)
            # return self.finish(json.dumps({
            #     'status': 'success',
            #     'message': 'PDF file saved successfully!',
            #     'status_code': 201,
            #     'data': file_upload_path_data,
            # }, default=json_util.default))

            self.set_header("Content-Type", 'application/pdf; charset="utf-8"')
            self.finish(pdf)

        else:
            if len(bill_report_numbers) == 1:
                log.info(f"Bill report no {bill_report_numbers[0]} already generated previously.")
                self.set_header('Content-Type', 'application/json')
                self.set_status(400)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': f"Bill report no {bill_data['bill_report_no']} already exist.",
                    'status_code': 400,
                }, default=json_util.default))
            else:
                bill_report_nos = ','.join(bill_report_numbers)
                log.info(f"Bill report no {bill_report_nos} already generated previously.")
                self.set_header('Content-Type', 'application/json')
                self.set_status(400)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': f"Bill report no {bill_report_nos} already exist.",
                    'status_code': 400,
                }, default=json_util.default))
            

class ConveyanceBillReportPdf(RequestHandler):

    REQUIRED_FIELD = ("bill_ids",)
    DAY_FORMAT = '%d %B, %Y'
    DEFAULT_DATETIME_FORMAT = '%A %d %B %Y %I:%M:%S %p'

        
    def get(self): 

        """
            ConveyanceBillReportPdf currently takes four parameters
            :param bill_ids: bill ids of selected conveyance bills
            
            access with: /app/conveyance_bill_pdf
        """
        
        try:
            bill_ids_param = self.get_argument('bill_ids', None)
            if not bill_ids_param:
                raise ValueError("Expecting value for bill_ids")

            bill_ids = bill_ids_param.strip('[]').split(',')
            bill_ids = [ObjectId(bill_id.strip()) for bill_id in bill_ids]
            
        except JSONDecodeError as _:
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'Expecting value - {}'.format(_),
                'status_code': 400,
            }, default=json_util.default))
       
        # current_user = "641a9b1fea0c1cd5e5ed2a81"
        user = {
            "_id": "641a9b1fea0c1cd5e5ed2a81",
            "name": "Benoy Kumar Roy",
            "org_admin": True,
            "organization": ObjectId('5ef834ca70713e543a64195a')
        }
        organization = '5ef834ca70713e543a64195a'

        is_org_admin = user.get("org_admin", False)
        org_id = user.get("organization", "")
        try:
            ObjectId(org_id)
        except errors.InvalidId:
            self.set_status(404)
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'Invalid organization id',
                'status_code': 404,
            }, default=json_util.default))

        organization = db.organizations.find_one(
            {"_id": ObjectId(org_id)})
        if organization is None:
            self.set_status(404)
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'Invalid organization id',
                'status_code': 404,
            }, default=json_util.default))
        org_country = organization['country']
        if org_country == 'Bangladesh  +880' or org_country == 'Bangladesh':
            currency = 'BDT'
            extension = "+880"
        if org_country == 'India  +91' or org_country == 'India':
            currency = 'INR'
            extension = "+91"
        if org_country == 'Angola  +244' or org_country == 'Angola':
            currency = 'AOA'
            extension = "+244"
        if org_country == 'Australia  +61' or org_country == 'Australia':
            currency == 'AUD'
            extension = "+61"

        organization_address = "{}, {}, {}".format(organization.get("address",
                                                                    ""),
                                                   organization.get(
                                                       "city", ""),
                                                   organization.get("country",
                                                                    ""))
        

        new_bill_report_no = str(random.randint(10000000, 99999999))
        total_sum_of_bills = 0
        total_bill_data = []
        bill_report_numbers = []

        for bill_id in bill_ids:
            # pipeline = [
            #     {
            #         '$addFields': {
            #             'task_id': { '$toObjectId': '$task_id' }  # Convert task_id from string to ObjectId
            #         }
            #     },
            #     {
            #         '$lookup': {
            #             'from': 'tasks',
            #             'localField': 'task_id',
            #             'foreignField': '_id',
            #             'as': 'task_info'
            #         }
            #     },
            #     {
            #         '$unwind': '$task_info'
            #     }
            # ]
            # pipeline = [
            #     {
            #         '$match': {
            #             'task_id': {'$type': 'string', '$regex': '^[a-fA-F0-9]{24}$'}
            #         }
            #     },
            #     {
            #         '$addFields': {
            #             'task_id': {
            #                 '$convert': {
            #                     'input': '$task_id',
            #                     'to': 'objectId',
            #                     'onError': None,
            #                     'onNull': None
            #                 }
            #             }
            #         }
            #     },
            #     {
            #         '$lookup': {
            #             'from': 'tasks',
            #             'localField': 'task_id',
            #             'foreignField': '_id',
            #             'as': 'task_info'
            #         }
            #     },
            #     {
            #         '$unwind': '$task_info'
            #     }
            # ]

            pipeline = [
                {
                    # Include all documents, even if 'task_id' is missing or invalid
                    '$addFields': {
                        'task_id': {
                            '$cond': {
                                'if': {'$regexMatch': {'input': '$task_id', 'regex': '^[a-fA-F0-9]{24}$'}},
                                'then': {'$convert': {'input': '$task_id', 'to': 'objectId', 'onError': None, 'onNull': None}},
                                'else': None
                            }
                        }
                    }
                },
                {
                    '$lookup': {
                        'from': 'tasks',
                        'localField': 'task_id',
                        'foreignField': '_id',
                        'as': 'task_info'
                    }
                },
                {
                    '$unwind': {
                        'path': '$task_info',
                        'preserveNullAndEmptyArrays': True  # Allow bills with no task_info to still be included
                    }
                }
            ]

    
            # result = list(db.bills.aggregate(pipeline))
            if is_org_admin:
                match = {
                    '$match': {
                        '_id': ObjectId(bill_id),
                        # 'misc_bill_type.name': 'Conveyance'
                    }
                }
                pipeline.insert(0, match)

            else:
                match = {
                    '$match': {
                        '_id': ObjectId(bill_id),
                        # 'misc_bill_type.name': 'Conveyance',
                        'created_by': str(user["_id"])
                    }
                }
                pipeline.insert(0, match)

            bill_data = list(db.bills.aggregate(pipeline))
            
            if bill_data:
                if 'bill_report_no' in bill_data[0] and bill_data[0]['bill_report_no']:
                    print("HAS bill report no", bill_data[0]['bill_report_no'])
                    bill_report_numbers.append(bill_data[0]['bill_report_no'])
                else:
                    log.info(f'bill report no is not exist')
                    db.bills.find_one_and_update({'_id': ObjectId(bill_id)}, {'$set': {'bill_report_no': new_bill_report_no}})
                total_price = bill_data[0].get("total_price", "")
                total_sum_of_bills = total_sum_of_bills + total_price
                for b_data in bill_data:
                    if 'created_for' not in b_data:
                        user_info = db.users.find_one({"_id": ObjectId(b_data['generated_for'])}, {'name': 1, 'mobile': 1})
                        b_data['bill_for'] = user_info['name']
                        b_data['bill_for_mobile'] = user_info['mobile']
                    total_bill_data.append(b_data)
            else:
                 return self.finish(json.dumps({
                    'status': 'error',
                    'message': f'Bill data is not found for {bill_id} parameters',
                    'status_code': 400,
                }, default=json_util.default))


        if bill_report_numbers == []:
            base_dir = os.path.join(os.getcwd(), 'pdf', 'bill_pdf')
            os.makedirs(base_dir, exist_ok=True)

            # Define the filename and full filepath
            random_num = time() * 1000 * randint(2, 200)
            filename = f"conveyance_bill_{random_num}.pdf"
            # filepath = os.path.join(
            #     os.getcwd(), "pdf", "bill_pdf", filename)
            filepath = os.path.join(base_dir, filename)
            
            template, css = pdf_assets('conveyance_bill.html')
            org_mobile = extension+""+ organization.get('telephone', 'NA')
            now = datetime.now()
            now = now.strftime("%A, %d %B %Y %I:%M %p")

            template_vars = {"bills": total_bill_data, 
                            "total_price": total_sum_of_bills, 
                            "currency": currency,
                            "org_name": organization.get('name', 'NA'),
                            "org_address": organization.get('address', 'NA'),
                            "org_mobile": org_mobile,
                            "now": now
                            }
            
            if isinstance(total_bill_data[0]['misc_bill_type'], dict):
                template_vars['bill_type'] = total_bill_data[0]['misc_bill_type']['name']
            else:
                template_vars['bill_type'] = total_bill_data[0]['misc_bill_type']

            rendered_string = template.render(template_vars)
            html = weasyprint.HTML(string=rendered_string)
            conveyance_pdf_filepath = f"pdf{filepath.split('/pdf')[1]}"
            file_upload_path_data = {
                "bill_report_url": conveyance_pdf_filepath
            }
            for bill_id in bill_ids:
                db.bills.find_one_and_update({'_id': ObjectId(bill_id)}, {'$set': file_upload_path_data})
            
            log.info(f"pdf path is {conveyance_pdf_filepath}")
            # pdf = html.write_pdf(target=filepath)
            html.write_pdf(target=filepath)
            with open(filepath, 'rb') as f:
                pdf_data = f.read()
            self.set_header('Content-Type', 'application/pdf; charset="utf-8"')
            self.set_header('Content-Disposition', 'attachment; filename=' + filename)
            self.write(pdf_data)
        else:
            if len(bill_report_numbers) == 1:
                log.info(f"Bill report no {bill_report_numbers[0]} already generated previously.")
                self.set_header('Content-Type', 'application/json')
                self.set_status(400)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': f"Bill report no {bill_data[0]['bill_report_no']} already exist.",
                    'status_code': 400,
                }, default=json_util.default))
            else:
                bill_report_nos = ','.join(bill_report_numbers)
                log.info(f"Bill report no {bill_report_nos} already generated previously.")
                self.set_header('Content-Type', 'application/json')
                self.set_status(400)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': f"Bill report no {bill_report_nos} already exist.",
                    'status_code': 400,
                }, default=json_util.default))
            

class PurchaseBillReportPdf(RequestHandler):

    REQUIRED_FIELD = ("bill_ids",)
    DAY_FORMAT = '%d %B, %Y'
    DEFAULT_DATETIME_FORMAT = '%A %d %B %Y %I:%M:%S %p'

        
    def get(self): 

        """
            PurchaseBillReportPdf currently takes one parameters
            :param bill_ids: bill ids of selected conveyance bills
            
            access with: /app/purchase_bill_pdf
        """
        bill_type = self.get_argument('bill_type', None)
        try:
            bill_ids_param = self.get_argument('bill_ids', None)
            if not bill_ids_param:
                raise ValueError("Expecting value for bill_ids")

            bill_ids = bill_ids_param.strip('[]').split(',')
            bill_ids = [ObjectId(bill_id.strip()) for bill_id in bill_ids]
            
        except JSONDecodeError as _:
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'Expecting value - {}'.format(_),
                'status_code': 400,
            }, default=json_util.default))
       
        # current_user = "641a9b1fea0c1cd5e5ed2a81"
        user = {
            "_id": "641a9b1fea0c1cd5e5ed2a81",
            "name": "Benoy Kumar Roy",
            "org_admin": True,
            "organization": ObjectId('5ef834ca70713e543a64195a')
        }
        organization = '5ef834ca70713e543a64195a'
        # else:
        #     user = None
        if user is None:
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'You are not a valid user!',
                'status_code': 400,
            }, default=json_util.default))

        is_org_admin = user.get("org_admin", False)
        org_id = user.get("organization", "")
        try:
            ObjectId(org_id)
        except errors.InvalidId:
            self.set_status(404)
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'Invalid organization id',
                'status_code': 404,
            }, default=json_util.default))

        organization = db.organizations.find_one(
            {"_id": ObjectId(org_id)})
        if organization is None:
            self.set_status(404)
            return self.finish(json.dumps({
                'status': 'error',
                'message': 'Invalid organization id',
                'status_code': 404,
            }, default=json_util.default))
        org_country = organization['country']
        if org_country == 'Bangladesh  +880' or org_country == 'Bangladesh':
            currency = 'BDT'
            extension = "+880"
        if org_country == 'India  +91' or org_country == 'India':
            currency = 'INR'
            extension = "+91"
        if org_country == 'Angola  +244' or org_country == 'Angola':
            currency = 'AOA'
            extension = "+244"
        if org_country == 'Australia  +61' or org_country == 'Australia':
            currency == 'AUD'
            extension = "+61"

        organization_address = "{}, {}, {}".format(organization.get("address",
                                                                    ""),
                                                   organization.get(
                                                       "city", ""),
                                                   organization.get("country",
                                                                    ""))
        

        new_bill_report_no = str(random.randint(10000000, 99999999))
        total_sum_of_bills = 0
        total_bill_data = []
        bill_report_numbers = []
        
        for bill_id in bill_ids:
            bill_data = db.bills.find_one({"_id": ObjectId(bill_id)})
            # pipeline = [
            #     {
            #         "$match": {"_id": ObjectId(bill_id)}
            #     },
            #     {
            #         "$addFields": {
            #             "user_id": {"$toObjectId": "$generated_for"}
            #         }
            #     },
            #     {
            #         "$lookup": {
            #             "from": "users",
            #             "localField": "generated_for",
            #             "foreignField": "_id",
            #             "as": "user_info"
            #         }
            #     },
            #     {
            #         "$unwind":  "$user_info"
            #     }
            # ]
            # bill_data = list(db.bills.aggregate(pipeline))
            # print("Bill DATA", bill_data)

            if 'created_for' not in bill_data:
                user_info = db.users.find_one({"_id": ObjectId(bill_data['generated_for'])}, {'name': 1, 'mobile': 1})
                bill_data['bill_for'] = user_info['name']
                bill_data['bill_for_mobile'] = user_info['mobile']
            
            if bill_data:
                total_bill_data.append(bill_data)

                if 'bill_report_no' in bill_data and bill_data['bill_report_no']:
                    bill_report_numbers.append(bill_data['bill_report_no'])
                else:
                    log.info(f'bill report no is not exist')
                    db.bills.find_one_and_update({'_id': ObjectId(bill_id)}, {'$set': {'bill_report_no': new_bill_report_no}})
            else:
                    return self.finish(json.dumps({
                    'status': 'error',
                    'message': f'Bill data is not found for {bill_id} parameters',
                    'status_code': 400,
                }, default=json_util.default))

        if bill_report_numbers == []:
            random_num = time() * 1000 * randint(2, 200)
            filename = f"purchase_bill_{random_num}.pdf"
            filepath = os.path.join(
                os.getcwd(), "pdf", "bill_pdf", filename)
            template, css = pdf_assets('bills.html')
            org_mobile = extension+""+ organization.get('telephone', 'NA')
            now = datetime.now()
            now = now.strftime("%A, %d %B %Y %I:%M %p")
            
            template_vars = {"bills": total_bill_data, 
                            "currency": currency,
                            "org_name": organization.get('name', 'NA'),
                            "org_address": organization.get('address', 'NA'),
                            "org_mobile": org_mobile,
                            "now": now
                            }
            print(f"Total Bill Data Image Path 1: {total_bill_data[0].get('bill_image_path_1')}")
            print(f"Total Bill Data Image Path 2: {total_bill_data[0].get('bill_image_path_2')}")
            
            if isinstance(total_bill_data[0]['misc_bill_type'], dict):
                template_vars['bill_type'] = total_bill_data[0]['misc_bill_type']['name']
            else:
                template_vars['bill_type'] = total_bill_data[0]['misc_bill_type']

            rendered_string = template.render(template_vars)
            html = weasyprint.HTML(string=rendered_string)
            purchase_pdf_filepath = f"pdf{filepath.split('/pdf')[1]}"
            file_upload_path_data = {
                "bill_report_url": purchase_pdf_filepath
            }
            for bill_id in bill_ids:
                db.bills.find_one_and_update({'_id': ObjectId(bill_id)}, {'$set': file_upload_path_data})
            log.info(f"pdf path is {purchase_pdf_filepath}")
            # pdf = html.write_pdf(target=filepath)
            html.write_pdf(target=filepath)
            with open(filepath, 'rb') as f:
                pdf_data = f.read()
            self.set_header('Content-Type', 'application/pdf; charset="utf-8"')
            self.set_header('Content-Disposition', 'attachment; filename=' + filename)
            self.write(pdf_data)
        else:
            if len(bill_report_numbers) == 1:
                log.info(f"Bill report no {bill_report_numbers[0]} already generated previously.")
                self.set_header('Content-Type', 'application/json')
                self.set_status(400)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': f"Bill report no {bill_data['bill_report_no']} already exist.",
                    'status_code': 400,
                }, default=json_util.default))
            else:
                bill_report_nos = ','.join(bill_report_numbers)
                log.info(f"Bill report no {bill_report_nos} already generated previously.")
                self.set_header('Content-Type', 'application/json')
                self.set_status(400)
                return self.finish(json.dumps({
                    'status': 'error',
                    'message': f"Bill report no {bill_report_nos} already exist.",
                    'status_code': 400,
                }, default=json_util.default))

class ExtendedOrderSummary(RequestHandler):
    """
    Extended Order summary with order's detailed summary

    using get to collection data via query param.

    access through
    /extended_order_summary or 
    reports/extended_order_summary(to get nginx settings facilities)


    """
    PARAMS = ("from", "to")
    DEFAULT_DATETIME_FORMAT = '%A %d %B %Y %I:%M:%S %p'
    DAY_FORMAT = '%d %b, %y'

    def get(self):
        """
            GET request for getting extended order summary report
            :param from: datetime in seconds from epoch
            :param to: datetime in seconds from epoch

        """
        # test_id = "600f94a68edd46e6c55006c0" # TR
        # test_id = "63c28511b3183fac600d92f7" # Eusuv Agni International
        # test_id = "63edebff321640561e6982ac" # Reza
        # test_id = "63f5ae8fc710ee1a0b8f8575" # org admin
        # test_id = "63f5ae8fc710ee1a0b8f8575" # own data
        # test_id = "63f59574580b1087498f8662" # sub org data
        # user = db.users.find_one(
        #     {"_id": ObjectId(self.current_user["user_id"])},
        #     {"organization": 1, "sub_org": 1,
        #      "is_operator": 1, "is_driver": 1, "is_staff": 1,
        #      "is_super": 1, "org_admin": 1, "name": 1, "user_tz_time": 1, "role_id": 1, "role_name": 1})

        # if user is None:
        #     return self.finish(json.dumps({
        #         'status': 'error',
        #         'message': 'You are not a valid user!',
        #         'status_code': 400,
        #     }, default=json_util.default))

        organization = str(user['organization'])
        sub_org = str(user['sub_org']) if 'sub_org' in user else None
        # log.info('crossed 3')
        # org_admin_user = db.users.find_one({"_id": ObjectId(self.current_user["user_id"]), 'organizations': {
        #                                         '$elemMatch': {'org_admin': True, '_id': ObjectId(organization)}}})
        start_time = self.get_argument('start_date', None)
        end_time = self.get_argument('end_date', None)
        sub_org = self.get_argument('sub_org', None)
        sub_org_name = self.get_argument('sub_org_name', None)
        sub_org_type_name = self.get_argument('sub_org_type_name', None)
        sort_by = self.get_argument('sort_by', 'started_on')
        sort_type = self.get_argument('sort_type', 'dsc')
        summary_type = self.get_argument('summary_type', "order")

        order_number = self.get_argument('order_number', None)
        name = self.get_argument('name', None)
        details = self.get_argument('details', None)
        drop_contact_no = self.get_argument('drop_contact_no', None)
        drop_contact_name = self.get_argument('drop_contact_name', None)
        start_loc_name = self.get_argument('start_loc_name', None)
        end_loc_name = self.get_argument('end_loc_name', None)
        search_date_time_type = self.get_argument('search_date_time_type', None)
        timezone_choice = self.get_argument('timezone_choice', None)
        timezone_name = self.get_argument('timezone_name', None)
        # delivery = self.get_argument('delivery', None)
        delivered = self.get_argument('delivered', None)
        cancelled = self.get_argument('cancelled', None)
        rescheduled = self.get_argument('rescheduled', None)
        
        created_by_name = self.get_argument('created_by_name', None)
        modified_by_name = self.get_argument('modified_by_name', None)
        # sub_org = self.get_argument('sub_org', None)


        deleted = self.get_argument('d', False)
        

        if start_time:
            if date_validation(self, start_time):  # for check ing mandatary fields
                start_time = datetime.fromtimestamp(int(start_time)/1000.0)
                if timezone_choice == "user_timezone":
                    timezone_from = user_tz_time(self, start_time, timezone_name)
                else:
                    timezone_from = org_tz_time(self, start_time, organization)
        
            else:
                return
        if end_time:
            if date_validation(self, end_time):  # for check ing mandatary fields
                end_time = datetime.fromtimestamp(int(end_time)/1000.0)
                if timezone_choice == "user_timezone":
                    timezone_to = user_tz_time(self, end_time, timezone_name)
                else:
                    timezone_to = org_tz_time(self, end_time, organization)

            else:
                return
        organization = db.organizations.find_one(
            {"_id": ObjectId(user['organization'])})
        org_country = organization['country']
        if org_country == 'Bangladesh  +880' or org_country == 'Bangladesh':
            currency = 'BDT'
        if org_country == 'India  +91' or org_country == 'India':
            currency = 'INR'
        if org_country == 'Angola  +244' or org_country == 'Angola':
            currency = 'AOA'
        if org_country == 'Australia  +61' or org_country == 'Australia':
            currency == 'AUD'


        query = {"organization": ObjectId('5ef834ca70713e543a64195a')}

        log.info(f'query_with_data_level_permission_for_order_list is {query}')
        if user:
            log.info('found user')    
            subquery = []
            subq = {}
            if start_time and end_time:
                subq = {}
                subq['created_on'] = {
                    "$gte": start_time, "$lte": end_time}
                subquery.append(subq)
            if sub_org_name:
                subq = {}
                subq['sub_org.name'] = {'$regex': f".*{sub_org_name}.*", '$options': 'i'}
                subquery.append(subq)
            
            if sub_org_type_name:
                subq = {}
                subq['sub_org.sub_org_type_data.name'] = {'$regex': f".*{sub_org_type_name}.*", '$options': 'i'}
                subquery.append(subq)
            log.info('found user_id and skip>0')

            if delivered:
                if delivered.startswith('t') == True or delivered.startswith('T') == True:
                    subq = {}
                    delivered = True
                    subq['delivered'] = delivered
                    subquery.append(subq)
                elif delivered.startswith('f') == True or delivered.startswith('F') == True:
                    subq = {}
                    delivered = False
                    subq['delivered'] = delivered
                    subquery.append(subq)
            
            if cancelled:
                if cancelled.startswith('t') == True or cancelled.startswith('T') == True:
                    subq = {}
                    cancelled = True
                    subq['cancelled'] = cancelled
                    subquery.append(subq)
                elif cancelled.startswith('f') == True or cancelled.startswith('F') == True:
                    subq = {}
                    cancelled = False
                    subq['cancelled'] = cancelled
                    subquery.append(subq)
            
            if rescheduled:
                if rescheduled.startswith('t') == True or rescheduled.startswith('T') == True:
                    subq = {}
                    rescheduled = True
                    subq['rescheduled'] = rescheduled
                    subquery.append(subq)
                elif rescheduled.startswith('f') == True or rescheduled.startswith('F') == True:
                    subq = {}
                    rescheduled = False
                    subq['rescheduled'] = rescheduled
                    subquery.append(subq)
            
            if deleted:
                subq = {}
                subq['deleted'] = True
                subquery.append(subq)
            else:
                subq = {}
                subq['deleted'] = False
                subquery.append(subq)
            

            if start_time and end_time and search_date_time_type == 'delivery_date_time':
                subq = {}
                subq['delivery_date_time'] = {
                    "$gte": start_time, "$lte": end_time}
                subquery.append(subq)
            if start_time and end_time and search_date_time_type == 'placed_on':
                subq = {}
                subq['placed_on'] = {
                    "$gte": start_time, "$lte": end_time}
                subquery.append(subq)
            if start_time and end_time and search_date_time_type == 'created_on':
                subq = {}
                subq['created_on'] = {
                    "$gte": start_time, "$lte": end_time}
                subquery.append(subq)
            if start_time and end_time and search_date_time_type == 'modified_on':
                subq = {}
                subq['modified_on'] = {
                    "$gte": start_time, "$lte": end_time}
                subquery.append(subq)
            
            if name:
                subq = {}
                subq['name'] = {'$regex': f".*{name}.*", '$options': 'i'}
                subquery.append(subq)
            
            if order_number:
                subq = {}
                subq['order_number'] = {'$regex': f".*{order_number}.*", '$options': 'i'}
                subquery.append(subq)
            
            if details:
                subq = {}
                subq['details'] = {'$regex': f".*{details}.*", '$options': 'i'}
                subquery.append(subq)
   
            if drop_contact_no:
                subq = {}
                subq['drop_contact_no'] = {'$regex': f".*{drop_contact_no}.*", '$options': 'i'}
                subquery.append(subq)
            
            if drop_contact_name:
                subq = {}
                subq['drop_contact_name'] = {'$regex': f".*{drop_contact_name}.*", '$options': 'i'}
                subquery.append(subq)
            
            if start_loc_name:
                subq = {}
                subq['start_entity.address'] = {'$regex': f".*{start_loc_name}.*", '$options': 'i'}
                subquery.append(subq)
            
            if end_loc_name:
                subq = {}
                subq['end_loc_name'] = {'$regex': f".*{end_loc_name}.*", '$options': 'i'}
                subquery.append(subq)
            
            if created_by_name:
                subq = {}
                subq['created_by_name'] = {'$regex': f".*{created_by_name}.*", '$options': 'i'}
                subquery.append(subq)
            
            if modified_by_name:
                subq = {}
                subq['modified_by_name'] = {'$regex': f".*{modified_by_name}.*", '$options': 'i'}
                subquery.append(subq)
            
            log.info('Sub Queries')
            log.info(len(subquery))
            if len(subquery) > 0:
                query['$and'] = subquery
            count_obj = {}
            log.info(f"sub query: {subquery}")
            log.info(f"query: {query}")

            # if sub_org_ids == []:
            orders = list(db.orders.find(query))
            count = len(orders)

            # aggregate query pipline
            pipeline = [
                {"$match": query}, 
                {
                    "$group": {
                                "_id": None,
                                "partial_total_due" : { "$sum": "$due_amount" }, 
                                "partial_total_bill": {"$sum": "$bill_amount"},
                                "partial_total_received_amount": {"$sum": "$total_received_amount"},
                                "partial_total_delivered_order": {"$sum": {"$cond": [{ "$eq": ["$delivered", True] }, 1, 0]}}, 
                                "count": { "$sum": 1 }
                            },        
                },
                ]
            aggregate_data = list(db.orders.aggregate(pipeline))
            # NOTE: need to convert the following for loop in a generic pattern
            for p_data in aggregate_data:
                    count_obj['total_bill'] = p_data['partial_total_bill']
                    count_obj['total_due'] = p_data['partial_total_due']
                    count_obj['total_received_amount'] = p_data['partial_total_received_amount']
                    count_obj['total_delivered_amount'] = p_data['partial_total_delivered_order']
                    count_obj['total_order'] = p_data['count']
            log.info(f"orders: {orders}")
            # print("TOTALs", count_obj)
            for order in orders:
                order['total_items'] = len(order['items'])
            # else:
            #     orders = []
            #     count = 0
            #     for sub_org_id in sub_org_ids:
            #         query['sub_org.id'] = sub_org_id
            #         partial_count = db.orders.find(query).count()
            #         count = count + partial_count
            #         # aggregate query pipeline
            #         pipeline = [
            #         {"$match": query}, 
            #         {
            #             "$group": { 
            #                 "_id": None,
            #                 "partial_total_due" : { "$sum": "$due_amount" }, 
            #                 "partial_total_bill": {"$sum": "$bill_amount"},
            #                 "partial_total_received_amount": {"$sum": "$total_received_amount"},
            #                 "partial_total_delivered_order": {"$sum": {"$cond": [{ "$eq": ["$delivered", True] }, 1, 0]}}, 
            #                 "count": { "$sum": 1 }
            #                 }, 
            #                 }, 
                        
            #         ]
            #         # NOTE: Later need to improve following query
            #         partial_data = db.orders.find(query)
            #         partial_data_list = list(partial_data)
            #         orders = orders + partial_data_list  
            #         aggregate_data = list(db.orders.aggregate(pipeline))
            #         # NOTE: need to convert the following for loop in a generic pattern
            #         for p_data in aggregate_data:
            #             count_obj['total_bill'] = p_data['partial_total_bill']
            #             count_obj['total_due'] = p_data['partial_total_due']
            #             count_obj['total_received_amount'] = p_data['partial_total_received_amount']
            #             count_obj['total_delivered_amount'] = p_data['partial_total_delivered_order']
            #             count_obj['total_order'] = p_data['count']
            #         # print("TOTALs for not org admin", count_obj)
            #         for order in orders:
            #             order['total_items'] = len(order['items'])
            # print("ORDERSS >>>> 10", orders[:2])
            # today = datetime.now(timezone.utc).replace(tzinfo=None)
            today = datetime.now(timezone.utc).replace(tzinfo=None)
            today = org_tz_time(self, today, str(user['organization']))

            buff = BytesIO()
            workbook = Workbook(buff, {'in_memory': True})
            worksheet = workbook.add_worksheet("Order Detail Summary")

            bold = workbook.add_format({'bold': True})
            border_bold_grey = workbook.add_format(
                {'border': True, 'bold': True, 'bg_color': '#dcdcdc'})
            border = workbook.add_format({'border': True})
            cell_format = workbook.add_format({'align': 'center'})

            # worksheet.set_column('A:J', 20)
            worksheet.set_column(0, 3, 20)
            current_user_name = user.get("name", "")

            worksheet.write(0, 0, 'Detailed Order Report', bold)
            if start_time and end_time:
                worksheet.write(1, 0, 'Duration: {} to {}'.format(timezone_from.strftime(self.DEFAULT_DATETIME_FORMAT), 
                                                              timezone_to.strftime(self.DEFAULT_DATETIME_FORMAT)), bold)
            # worksheet.write(1, 0, 'Date Start: {}'.format(start_time), bold)  # TODO: timezone issue
            # worksheet.write(2, 0, 'Date End: {}'.format(end_time), bold)  # TODO: timezone issue

            worksheet.write(2, 0, "Generated by %s" % current_user_name, border)
            worksheet.write(3, 0, "Generated on %s" %
                            today.strftime(self.DEFAULT_DATETIME_FORMAT), border)


            # worksheet.write(6, 0, "Total Orders %s" % len(order_payload), border)
                          
            # worksheet.write(6, 0, "Total Orders %s" % len(order_payload), border)
            if count_obj:
                worksheet.write(4, 0, "Total Orders %s" % count_obj['total_order'], border)
                worksheet.write(5, 0, "Total Billed Amount %s" % count_obj['total_bill'], border)
                worksheet.write(6, 0, "Total Received Amount %s" % count_obj['total_received_amount'], border)
                worksheet.write(7, 0, "Total Due Amount %s" % count_obj['total_due'], border)
            else:
                worksheet.write(4, 0, "Total Orders %s" % 0, border)
                worksheet.write(5, 0, "Total Billed Amount %s" % 0, border)
                worksheet.write(6, 0, "Total Received Amount %s" % 0, border)
                worksheet.write(7, 0, "Total Due Amount %s" % 0, border)
            row = 10
            for order_info in orders:
                order_number = order_info.get("order_number", "NA")
                name = order_info.get("name", "NA")
                client_name = order_info.get("end_entity", "NA").get("name", "NA")
                details = order_info.get("details", "NA")
                created_on = order_info.get("created_on", "NA")
                modified_on = order_info.get("modified_on", "NA")
                inventory_name = order_info.get('inventory_entity_name', "NA")
                created_by_name = order_info.get('created_by_name', "NA")
                total_price = order_info.get('total_price', 0)
                total_discount = order_info.get('total_discount', 0)
                other_charges = order_info.get('other_charges', 0)
                billed_amount = order_info.get('bill_amount', 0)
                received_amount = order_info.get('total_received_amount', 0)
                due_amount = order_info.get('due_amount', 0)

                if created_on is not None:
                    created_on = created_on.strftime(self.DEFAULT_DATETIME_FORMAT)

                if modified_on is not None:
                    modified_on = modified_on.strftime(
                        self.DEFAULT_DATETIME_FORMAT)
                item_list = order_info.get("items", [])

                worksheet.write(row, 0, "Order number: ", border)
                worksheet.write(row, 1, order_number, border)
                row += 1
                worksheet.write(row, 0, "Client name: ", border)
                worksheet.write(row, 1, client_name, border)
                row += 1
                worksheet.write(row, 0, "Order details: ", border)
                worksheet.write(row, 1, details, border)
                row += 1
                if 'sub_org' in order_info and order_info['sub_org']:
                    worksheet.write(row, 0, "Sub Org Name: ", border)
                    worksheet.write(row, 1, order_info['sub_org']['name'], border)
                else:
                    worksheet.write(row, 0, "Sub Org Name: ", border)
                    worksheet.write(row, 1, "NA", border)
                row += 1
                if 'sub_org' in order_info and order_info['sub_org'] and 'parent_sub_org_data' in order_info['sub_org'] and order_info['sub_org']['parent_sub_org_data'] and 'name' in order_info['sub_org']['parent_sub_org_data'] and order_info['sub_org']['parent_sub_org_data']['name']:
                    worksheet.write(row, 0, "Parent Sub Org Name: ", border)
                    worksheet.write(row, 1, order_info['sub_org']['parent_sub_org_data']['name'], border)
                else:
                     worksheet.write(row, 0, "Parent Sub Org Name: ", border)
                     worksheet.write(row, 1, "NA", border)
                row += 1
                worksheet.write(row, 0, "Inventory Name: ", border)
                worksheet.write(row, 1, inventory_name, border)
                row += 1
                worksheet.write(row, 0, "Created By: ", border)
                worksheet.write(row, 1, created_by_name, border)
                row += 1
                worksheet.write(
                    row, 0, "Created 0", border)
                worksheet.write(row, 1, created_on, border)
                row += 1
                worksheet.write(row, 0, "Modified 0", border)
                worksheet.write(row, 1, modified_on, border)
                row += 1
                worksheet.write(row, 0, "Total Ite0", border)
                worksheet.write(row, 1, len(item_list), border)
                row += 1

                worksheet.write(row, 0, "Sl No.", border_bold_grey)
                worksheet.write(row, 1, "SKU.", border_bold_grey)
                worksheet.write(row, 2, "Product Name", border_bold_grey)
                worksheet.write(row, 3, "Product Unit", border_bold_grey)
                worksheet.write(row, 4, "Unit Price", border_bold_grey)
                worksheet.write(row, 5, "Quantity", border_bold_grey)
                worksheet.write(row, 6, "Discount", border_bold_grey)
                worksheet.write(row, 7, "Total Price", border_bold_grey)

                index = 1
                row += 1
                for item in item_list:
                    worksheet.write(row, 0, index, border)
                    worksheet.write(row, 1, item["sku"], border)
                    worksheet.write(row, 2, item["item"], border)
                    worksheet.write(row, 3, item["unit"], border)
                    if 'unit_price' in item:
                        worksheet.write(row, 4, item["unit_price"], border)
                    else:
                        worksheet.write(row, 4, item["unit_selling_price"], border)
                    worksheet.write(row, 5, item["qty"], border)
                    worksheet.write(row, 6, item["per_item_discount"], border)
                    worksheet.write(row, 7, item["price"], border)

                    index += 1
                    row += 1
                # 3 blank rows for space
                row += 1
                worksheet.write(row, 6, "Total Price: ", border)
                worksheet.write(row, 7, total_price, border)
                row += 1
                worksheet.write(row, 6, "Total Discount: ", border)
                worksheet.write(row, 7, total_discount, border)
                row += 1
                worksheet.write(row, 6, "Other Charges: ", border)
                worksheet.write(row, 7, other_charges, border)
                row += 1
                worksheet.write(row, 6, "Billed Amount: ", border)
                worksheet.write(row, 7, billed_amount, border)
                row += 1
                worksheet.write(row, 6, "Received Amount: ", border)
                worksheet.write(row, 7, received_amount, border)
                row += 1
                worksheet.write(row, 6, "Due Amount: ", border)
                worksheet.write(row, 7, due_amount, border)
                row += 4

            worksheet1 = workbook.add_worksheet("Order Tabuler Summary")

            bold = workbook.add_format({'bold': True})
            border_bold_grey = workbook.add_format(
                {'border': True, 'bold': True, 'bg_color': '#dcdcdc'})
            border = workbook.add_format({'border': True})
            cell_format = workbook.add_format({'align': 'center'})

            # worksheet.set_column('A:J', 20)
            worksheet1.set_column(0, 3, 20)
            current_user_name = user.get("name", "")

            worksheet1.write(0, 0, 'Ordered Product Report', bold)
            if start_time and end_time:
                worksheet1.write(1, 0, 'Duration: {} to {}'.format(timezone_from.strftime(self.DEFAULT_DATETIME_FORMAT), 
                                                            timezone_to.strftime(self.DEFAULT_DATETIME_FORMAT)), bold)
                
            worksheet1.write(2, 0, "Generated by %s" % current_user_name, border)
            worksheet1.write(3, 0, "Generated on %s" %
                            today.strftime(self.DEFAULT_DATETIME_FORMAT), border)
            
            if count_obj:
                worksheet1.write(4, 0, "Total Orders %s" % count_obj['total_order'], border)
                worksheet1.write(5, 0, "Total Billed Amount %s" % count_obj['total_bill'], border)
                worksheet1.write(6, 0, "Total Received Amount %s" % count_obj['total_received_amount'], border)
                worksheet1.write(7, 0, "Total Due Amount %s" % count_obj['total_due'], border)
            else:
                worksheet1.write(4, 0, "Total Orders %s" % 0, border)
                worksheet1.write(5, 0, "Total Billed Amount %s" % 0, border)
                worksheet1.write(6, 0, "Total Received Amount %s" % 0, border)
                worksheet1.write(7, 0, "Total Due Amount %s" % 0, border)
            row1 = 10

            worksheet1.write(row1, 0, "Sl No.", border_bold_grey)
            worksheet1.write(row1, 1, "Created On", border_bold_grey)
            worksheet1.write(row1, 2, "Order Number", border_bold_grey)
            worksheet1.write(row1, 3, "Order Name", border_bold_grey)
            worksheet1.write(row1, 4, "Sub Org Name", border_bold_grey)
            worksheet1.write(row1, 5, "Parent Sub Org Name", border_bold_grey)
            worksheet1.write(row1, 6, "Inventory Name", border_bold_grey)
            worksheet1.write(row1, 7, "Delivery Location", border_bold_grey)
            worksheet1.write(row1, 8, "Delivery Person", border_bold_grey)
            worksheet1.write(row1, 9, "Delivery Person's Name", border_bold_grey)
            worksheet1.write(row1, 10, "Product Name", border_bold_grey)
            worksheet1.write(row1, 11, "Product Unit", border_bold_grey)
            worksheet1.write(row1, 12, "Unit Price", border_bold_grey)
            worksheet1.write(row1, 13, "Quantity", border_bold_grey)
            worksheet1.write(row1, 14, "Per Item Discount", border_bold_grey)
            worksheet1.write(row1, 15, "Total Item Discount", border_bold_grey)
            worksheet1.write(row1, 16, "Discounted Total Price", border_bold_grey)
            worksheet1.write(row1, 17, "Bill Amount", border_bold_grey)

            index1 = 1
            row1 += 1
            items = []
            for order_info in orders:
                order_number = order_info.get("order_number", "NA")
                name = order_info.get("name", "NA")
                details = order_info.get("details", "NA")
                created_on = order_info.get("created_on", "NA")
                modified_on = order_info.get("modified_on", "NA")
                inventory_name = order_info.get('inventory_entity_name', "NA")
                created_by_name = order_info.get('created_by_name', "NA")
                total_price = order_info.get('total_price', "NA")
                total_discount = order_info.get('total_discount', "NA")
                other_charges = order_info.get('other_charges', "NA")
                billed_amount = order_info.get('bill_amount', "NA")
                received_amount = order_info.get('total_received_amount', "NA")
                due_amount = order_info.get('due_amount', "NA")
                delivery_location = order_info.get('end_loc_name', "NA")
                delivery_person = order_info.get('drop_contact_name', "NA")
                delivery_person_number = order_info.get('drop_contact_no', "NA")

                if created_on is not None:
                    created_on = created_on.strftime(self.DEFAULT_DATETIME_FORMAT)

                if modified_on is not None:
                    modified_on = modified_on.strftime(
                        self.DEFAULT_DATETIME_FORMAT)
                item_list = order_info.get("items", [])

                for item in item_list:
                    item['created_on'] = created_on
                    item['order_number'] = order_number
                    item['order_name'] = name
                    if 'sub_org' in order_info and order_info['sub_org']:
                        item['sub_org'] = order_info['sub_org']['name']
                    else:
                        item['sub_org'] = "NA"
                    if 'sub_org' in order_info and order_info['sub_org'] and 'parent_sub_org_data' in order_info['sub_org'] and order_info['sub_org']['parent_sub_org_data'] and 'name' in order_info['sub_org']['parent_sub_org_data'] and order_info['sub_org']['parent_sub_org_data']['name']:
                        item['parent_sub_org'] = order_info['sub_org']['parent_sub_org_data']['name']
                    else:
                        item['parent_sub_org'] = "NA"
                    item['inventory_name'] = inventory_name
                    item['delivery_location'] = delivery_location
                    item['delivery_person'] = delivery_person
                    item['delivery_person_number'] = delivery_person_number
                    item['bill_amount'] = billed_amount
                    
                    items.append(item)
            for item in items:
                worksheet1.write(row1, 0, index1, border)
                worksheet1.write(row1, 1, created_on, border)
                worksheet1.write(row1, 2, item["order_number"], border)
                worksheet1.write(row1, 3, item['order_name'], border)
                worksheet1.write(row1, 4, item['sub_org'], border)
                worksheet1.write(row1, 5, item['parent_sub_org'], border) 
                worksheet1.write(row1, 6, item['inventory_name'], border)
                worksheet1.write(row1, 7, item['delivery_location'], border)
                worksheet1.write(row1, 8, item['delivery_person'], border)
                worksheet1.write(row1, 9, item['delivery_person_number'], border)
                worksheet1.write(row1, 10, item["item"], border)
                worksheet1.write(row1, 11, item["unit"], border)
                if 'unit_price' in item:
                    worksheet1.write(row1, 12, item["unit_price"], border)
                else:
                    worksheet1.write(row1, 12, item["unit_selling_price"], border)
                worksheet1.write(row1, 13, item["qty"], border)
                worksheet1.write(row1, 14, item["per_item_discount"], border)
                worksheet1.write(row1, 15, item["item_discount"], border)
                worksheet1.write(row1, 16, item["item_discounted_price"], border)
                worksheet1.write(row1, 17, item["bill_amount"], border)

                row1 += 1
                index1 += 1

            workbook.close()
            self.set_status(200)
            self.set_header(
                'Content-type',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            if timezone_choice == "user_timezone":
                self.set_header("Content-Disposition", "attachment; filename=detail_order_summary_report_{}.xlsx".format((user_tz_time(self, datetime.now(timezone.utc).replace(tzinfo=None), timezone_name)).strftime('%d-%m-%y_%I-%M-%S_%p')))
            else:
                self.set_header("Content-Disposition", "attachment; filename=detail_order_summary_report_{}.xlsx".format((org_tz_time(self, datetime.now(timezone.utc).replace(tzinfo=None), str(user['organization']))).strftime('%d-%m-%y_%I-%M-%S_%p')))
            return self.finish(buff.getvalue())

        else:
            self.set_header('Content-Type', 'application/json')
            self.set_status(400)
            return self.finish(json.dumps({
                'status': 'error',
                'message': f"User should be org admin.",
                'status_code': 400,
            }, default=json_util.default))