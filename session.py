import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.escape
import uuid
from ipwhois import IPWhois

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        session_id = self.get_secure_cookie('session_id')
        return active_sessions.get(session_id)

class ActiveSessionsHandler(BaseHandler):
    # @tornado.web.authenticated
    def get(self):
        # Only allow admins to view active sessions
        # if not self.current_user.get('is_admin', False):
        #     self.set_status(403)  # Forbidden
        #     self.finish("Permission denied.")
        #     return
        print(self.request.cookies)
        user_agent = self.request.headers.get('user_agent', 'unknown')
        ip_address = self.request.remote_ip

        device_info = {
            'user_agent': user_agent,
            'ip_address': ip_address
        }
        ipwhois = IPWhois(ip_address)
        result = ipwhois.lookup_rdap()
        print(result)

        # active_sessions_list = list(active_sessions.values())
        self.write({"device_info": device_info})

class LoginHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self):
        user_id = self.get_argument('user_id')
        password = self.get_argument('password')

        # Perform authentication (this is a simplified example)
        if user_id in user_database and password == 'password123':
            session_id = str(uuid.uuid4())
            self.set_secure_cookie('session_id', session_id)
            active_sessions[session_id] = user_database[user_id]
            self.write({"status": "success"})
        else:
            self.set_status(401)  # Unauthorized
            self.finish("Invalid credentials.")

class LogoutHandler(BaseHandler):
    def post(self):
        session_id = self.get_secure_cookie('session_id')
        if session_id in active_sessions:
            del active_sessions[session_id]
        self.clear_cookie('session_id')
        self.write({"status": "success"})

def make_app():
    return tornado.web.Application([
        (r'/active_sessions', ActiveSessionsHandler),
        (r'/login', LoginHandler),
        (r'/logout', LogoutHandler),
    ], cookie_secret='your_cookie_secret', debug=True)

if __name__ == '__main__':
    app = make_app()

    # Initialize active sessions dictionary
    active_sessions = {}

    app.listen(8881)
    print('session started')
    tornado.ioloop.IOLoop.current().start()
