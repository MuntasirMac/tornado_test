import tornado.web
import tornado.ioloop
from dbconnection import connect_db

from views import TestDbHandler


db = connect_db()

class basicRequestHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world!!!!!!")

class resourceRequestHandler(tornado.web.RequestHandler):
    def get(self, id):
        self.write("Querying soemthing with id " + id)

class queryStringRequestHandler(tornado.web.RequestHandler):
    def get(self):
        n = int(self.get_argument("n"))
        r = "odd" if n % 2 else "even"
        
        self.write("the number " + str(n) + " is " + r)

class staticRequestHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class callJSON(tornado.web.RequestHandler):
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
        (r"/", basicRequestHandler),
        (r"/html", staticRequestHandler),
        (r"/isEven", queryStringRequestHandler),
        (r"/resource/([0-9]+)", resourceRequestHandler),
        (r"/api", callJSON),
        (r"/test", TestDbHandler),
    ])

    app.listen(8881)
    print("I'm listening on port 8881")
    tornado.ioloop.IOLoop.current().start()
