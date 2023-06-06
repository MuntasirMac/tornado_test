from tornado.web import RequestHandler

class TestDbHandler(RequestHandler):
    def post(self):
        data = self.request.data

        pass