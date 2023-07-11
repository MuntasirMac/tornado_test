import tornado.web
import tornado.ioloop
from PIL import Image
from io import BytesIO

class uploadImgHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

    def post(self):
        file = self.request.files["fileImage"][0]
        # print(files['body'])
        image = Image.open(BytesIO(file['body']))
        th_image = image

        size = (100, 100)
        th_image.thumbnail(size)
        thumb = th_image
        # print(thumb.info)
        th = open("/home/muntasir/thumbtornado.png",'wb')
        bs = BytesIO()
        thumb.save(bs, format='JPEG')
        b_str = bs.getvalue()
        bs.close()
        th.write(b_str)
        # for f in files:
        #     fh = open(f"/{f.filename}", "wb")
        #     fh.write(f.body)
        #     fh.close()
        # self.write(f"http://localhost:8881/img/{f.filename}")
        # self.write('posted!')