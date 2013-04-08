import tornado.auth
import tornado.database
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from views.basehandler import BaseHandler


class AuthLoginHandler(BaseHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect()
    
    def _on_auth(self, user):
        print "========================="
        print user
        print "========================="
        if not user:
            raise tornado.web.HTTPError(500, "Google auth failed")

        author = self.db.get("SELECT * FROM authors WHERE email = %s",user["email"])
        print author
        if not author:
            # Auto-create first author
            any_author = self.db.get("SELECT * FROM authors LIMIT 1")
            
            print "================================ any_author"
            print any_author
            
            if not any_author:
                author_id = self.db.execute(
                    "INSERT INTO authors (email,name) VALUES (%s,%s)",
                    user["email"], user["name"])
            else:
                self.redirect("/")
                return
        else:
            author_id = author["id"]
            print "============== author_id "
            print author_id
            
        self.set_secure_cookie("user", str(author_id))
        self.redirect(self.get_argument("next", "/"))

class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))