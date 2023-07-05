import tornado.web
import tornado.ioloop

class uploadImgHandler(tornado.web.RequestHandler):
    def post(self):
        files = self.request.files["fileImage"]
        for f in files:
            fh = open(f"upload/{f.filename}", "wb")
            fh.write(f.body)
            fh.close()
        self.write(f"http://localhost:8881/img/{f.filename}")
    def get(self):
        self.render("index.html")