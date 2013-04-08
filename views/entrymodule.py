import markdown
import os.path
import re
import tornado.auth
import tornado.database
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import json

from tornado.options import define, options
from views.basehandler import BaseHandler

class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)