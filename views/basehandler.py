import tornado.auth
import tornado.database
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        
        print "====== the user id is .... "
        print user_id
        if not user_id: 
            return None
        
        return self.db.get("SELECT * FROM authors WHERE id = %s", int(user_id))