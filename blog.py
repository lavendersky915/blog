#-*- coding: utf-8 -*-
#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import markdown
import os.path
import tornado.auth
import tornado.database
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.escape
import tornado.httpclient
import unicodedata
import re, urlparse
import urllib,simplejson
import sys

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="blog", help="blog database name")
define("mysql_user", default="root", help="blog database user")
define("mysql_password", default="24479994", help="blog database password")

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
        parts= urlparse.urlparse(iri)
        return urlparse.urlunparse(
            part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
            for parti, part in enumerate(parts)
        )
def unique_result(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/environment/", EnvironmentHandler),
            (r"/userperspective/", UserperspectiveHandler),
            (r"/embodiment/", EmbodimentHandler),
            (r"/desire/", DesireHandler),
            (r"/depth/", DepthHandler),
        ]
        settings = dict(
            blog_title=u"Tornado Blog",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/auth/login",
            autoescape=None,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        self.db = tornado.database.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)



class BaseHandler(tornado.web.RequestHandler):
    
    a = "123"

class HomeHandler(BaseHandler):
    def get(self):
        self.render("home.html")


class EnvironmentHandler(BaseHandler):
    def get(self):
        environments = []
        c=self.get_argument("c")
        n=self.get_argument("n")
        iri = "http://conceptnet5.media.mit.edu/data/5.1/search?rel=/r/AtLocation&start=/c/zh_TW/"+c+"&limit="+n
        url=iriToUri(iri)
        text = urllib.urlopen(url)
        result = simplejson.load(text)
        result = result["edges"]
        for each in result:
            environments.append(each["endLemmas"])
        environments = unique_result(environments)
        result = tornado.escape.json_encode(environments)
        self.set_header('Content-Type', 'text/javascript')
        self.write(result)

class UserperspectiveHandler(BaseHandler):
    def get(self):
        users = []
        c=self.get_argument("c")
        n=self.get_argument("n")
        iri = "http://conceptnet5.media.mit.edu/data/5.1/search?rel=/r/Desires&end=/c/zh_TW/"+c+"&limit="+n
        url=iriToUri(iri)
        text = urllib.urlopen(url)
        result = simplejson.load(text)
        result = result["edges"]
        for each in result:
            users.append(each["startLemmas"])
        users = unique_result(users)
        result = tornado.escape.json_encode(users)
        self.set_header('Content-Type', 'text/javascript')
        self.write(result)

class EmbodimentHandler(BaseHandler):
    def get(self):
        embodiments = []
        c=self.get_argument("c")
        n=self.get_argument("n")
        iri = "http://conceptnet5.media.mit.edu/data/5.1/search?rel=/r/UsedFor&start=/c/zh_TW/"+c+"&limit="+n
        url=iriToUri(iri)
        text = urllib.urlopen(url)
        result = simplejson.load(text)
        result = result["edges"]
        for each in result:
            iri2 = "http://conceptnet5.media.mit.edu/data/5.1/search?rel=/r/UsedFor&end=/c/zh_TW/"+each["endLemmas"]+"&limit="+n
            url2=iriToUri(iri2)
            text2 = urllib.urlopen(url2)
            result2 = simplejson.load(text2)
            result2 = result2["edges"]
            for each2 in result2:
                embodiments.append(each2["startLemmas"])
        embodiments = unique_result(embodiments)
        result = tornado.escape.json_encode(embodiments)
        self.set_header('Content-Type', 'text/javascript')
        self.write(result)

class DesireHandler(BaseHandler):
    def get(self):
        desires = []
        c=self.get_argument("c")
        n=self.get_argument("n")
        iri = "http://conceptnet5.media.mit.edu/data/5.1/search?rel=/r/Desires&start=/c/zh_TW/"+c+"&limit="+n
        url=iriToUri(iri)
        text = urllib.urlopen(url)
        result = simplejson.load(text)
        result = result["edges"]
        for each in result:
            desires.append(each["endLemmas"])
        desires = unique_result(desires)
        result = tornado.escape.json_encode(desires)
        self.set_header('Content-Type', 'text/javascript')
        self.write(result)

class DepthHandler(BaseHandler):
    def get(self):
        c=self.get_argument("c")
        #economic = [u"經濟",u"便宜",u"耐用"]
        #functional = [u"方便",u"實用",u"便利"]
        #intrinsic = [u"愛",u"情感",u"心靈"]
        #societal = [u"環保",u"社會",u"政府"]
        economic = [u"便宜"]
        functional = [u"實用"]
        intrinsic = [u"情感"]
        societal = [u"社會"]
        e_total = 0
        f_total = 0
        i_total = 0
        s_total = 0
        for each in economic:
            iri="http://conceptnet5.media.mit.edu/data/5.1/assoc/c/zh_TW/"+c+"?filter=/c/zh_TW/"+each+"&limit=1"
            url=iriToUri(iri)
            text = urllib.urlopen(url)
            result = simplejson.load(text)
            if(result["similar"]):
                score = result["similar"][0][1]
            else:
                score = 0
            e_total = e_total+score

        for each in functional:
            iri="http://conceptnet5.media.mit.edu/data/5.1/assoc/c/zh_TW/"+c+"?filter=/c/zh_TW/"+each+"&limit=1"
            url=iriToUri(iri)
            text = urllib.urlopen(url)
            result = simplejson.load(text)
            if(result["similar"]):
                score = result["similar"][0][1]
            else:
                score = 0
            f_total = f_total+score

        for each in intrinsic:
            iri="http://conceptnet5.media.mit.edu/data/5.1/assoc/c/zh_TW/"+c+"?filter=/c/zh_TW/"+each+"&limit=1"
            url=iriToUri(iri)
            text = urllib.urlopen(url)
            result = simplejson.load(text)
            if(result["similar"]):
                score = result["similar"][0][1]
            else:
                score = 0
            i_total = i_total+score

        for each in societal:
            iri="http://conceptnet5.media.mit.edu/data/5.1/assoc/c/zh_TW/"+c+"?filter=/c/zh_TW/"+each+"&limit=1"
            url=iriToUri(iri)
            text = urllib.urlopen(url)
            result = simplejson.load(text)
            if(result["similar"]):
                score = result["similar"][0][1]
            else:
                score = 0
            s_total = s_total+score
        
        result_list = [e_total,f_total,i_total,s_total]
        result = tornado.escape.json_encode(result_list)
        self.set_header('Content-Type', 'text/javascript')
        self.write(result)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
