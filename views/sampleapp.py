import tornado.auth
import tornado.database
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from views.basehandler import BaseHandler

class SampleApp(BaseHandler):
    def get(self):
        self.render('blog_sample.html')