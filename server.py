import tornado.web
import tornado.ioloop
from dbconnection import connect_db

from views import (TestDbHandler, 
                    TestGetHandler, 
                    GetArgHandler, 
                    GetStudentByKwargs, 
                    DeleteById
                    )
from product import ProductListHandler

db = connect_db()


# The next 5 request handler classes are for test
class BasicRequestHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!!!!!!")

class ResourceRequestHandler(tornado.web.RequestHandler):
    def get(self, id):
        self.write("Querying soemthing with id " + id)

class QueryStringRequestHandler(tornado.web.RequestHandler):
    def get(self):
        n = int(self.get_argument("n"))
        r = "odd" if n % 2 else "even"
        
        self.write("the number " + str(n) + " is " + r)

class StaticRequestHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class CallJSON(tornado.web.RequestHandler):
	def get(self):
		response = {
			"agent" : "Killjoy",
			"role" : "Sentinel",
			"origin" : "Germany",
			"abilities" : {
				"basic" : ["Alarmbot", "Nanoswarm"],
				"signature" : "Turret",
				"ultimate" : "Lockdown"
			}
		}

		self.write(response)

if __name__ == "__main__":
    app = tornado.web.Application([
        (r"/", BasicRequestHandler),
        (r"/html", StaticRequestHandler),
        (r"/isEven", QueryStringRequestHandler),
        (r"/resource/([0-9]+)", ResourceRequestHandler),
        (r"/api", CallJSON),
        (r"/test", TestDbHandler),
        (r"/gettest/", TestGetHandler),
        (r"/getarg/([^/]+)", GetArgHandler),
        (r"/delete/([^/]+)", DeleteById),
        (r"/getkwarg/", GetStudentByKwargs),
        (r"/insert-multiple-product/", ProductListHandler)
    ])

    app.listen(8881)
    print("I'm listening on port 8881")
    tornado.ioloop.IOLoop.current().start()
