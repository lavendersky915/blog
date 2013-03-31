#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import sys
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
import urllib
import urllib2
import pycurl
import StringIO
import yql
import array
#import cStringIO
from tornado.options import define, options
from HTMLParser import HTMLParser
from bs4 import BeautifulSoup

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="blog", help="blog database name")
define("mysql_user", default="root", help="blog database user")
define("mysql_password", default="19052260", help="blog database password")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/archive", ArchiveHandler),
            (r"/feed", FeedHandler),
            (r"/google", GoogleHandler),
            (r"/stpi", Lavender_STPI),
            (r"/test", TestHandler),
            (r"/entry/([^/]+)", EntryHandler),
            (r"/compose", ComposeHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),

            (r"/api_v1/get_blog_posts", ApiBlogPosts),
            (r"/sample_external_app", SampleApp)
        ]
        settings = dict(
            blog_title=u"Tornado Blog",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={"Entry": EntryModule},
            xsrf_cookies=False,
            cookie_secret="123456",
            login_url="/auth/login",
            autoescape=None,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        # Have one global connection to the blog DB across all handlers
        self.db = tornado.database.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)
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

class SampleApp(BaseHandler):
    def get(self):
        self.render('blog_sample.html')
class ApiBlogPosts(BaseHandler):
    def get(self):
        _entries = self.db.query("SELECT * FROM entries ORDER BY published "
                                "DESC LIMIT 10")
        #entries = json.dumps(entries)
        entries_api = []
        entries = {}
        for e in _entries:
            print "====="
            _e = e
            _e['updated'] = str(_e['updated'])
            _e['published'] = str(_e['published'])
            entries_api.append(_e)
            print "====="
        print entries_api
        self.set_header("Content-Type", "application/json")
        self.write({'data':entries_api})
    def post(self):
        # allows third part apps to create blog posts....
        self.set_header("Content-Type", "application/json")
        '''
            but for simplicity sake, when testing out, will need to login to google account first.....
        '''
        user = 1
        title = self.get_argument("title")
        text = self.get_argument("markdown")
        html = markdown.markdown(text)

        print "================================================================"
        print user
        print title
        print text
        print "================================================================"
        response = {'success':True}
        try:
            slug = unicodedata.normalize("NFKD", title).encode("ascii", "ignore")
            slug = re.sub(r"[^\w]+", " ", slug)
            slug = "-".join(slug.lower().strip().split())
            if not slug: slug = "entry"
            while True:
                e = self.db.get("SELECT * FROM entries WHERE slug = %s", slug)
                if not e: break
                slug += "-2"
            self.db.execute(
                "INSERT INTO entries (author_id,title,slug,markdown,html,"
                "published) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP())",
                user, title, slug, text, html)
            self.write({'data':response})
        except:
            response['success'] = False
            response['error_message'] = "You screwed up!"
            self.write({'data':response})
class HomeHandler(BaseHandler):
    def get(self):
        entries = self.db.query("SELECT * FROM entries ORDER BY published "
                                "DESC LIMIT 5")
        if not entries:
            self.redirect("/compose")
            return
        self.render("home.html", entries=entries)


class EntryHandler(BaseHandler):
    def get(self, slug):
        entry = self.db.get("SELECT * FROM entries WHERE slug = %s", slug)
        if not entry: raise tornado.web.HTTPError(404)
        self.render("entry.html", entry=entry)


class ArchiveHandler(BaseHandler):
    def get(self):
        entries = self.db.query("SELECT * FROM entries ORDER BY published "
                                "DESC")
        self.render("archive.html", entries=entries)


class FeedHandler(BaseHandler):
    def get(self):
        entries = self.db.query("SELECT * FROM entries ORDER BY published "
                                "DESC LIMIT 10")
        self.set_header("Content-Type", "application/atom+xml")
        self.render("feed.xml", entries=entries)
class GoogleHandler(BaseHandler):
    def get(self):
        content = ""
        assarray = []
        page = 1
        linkall =""
        keyword = self.get_argument("keyword", default=None, strip=False)
        while page < 10:
            index = str(page)
            url = "https://www.googleapis.com/customsearch/v1?q="+keyword+"&start="+index+"&key=AIzaSyCyj6LcvbjCciGMmt9Vq2UXUfShev_IpWM&cx=005971756043172606388:5upt-glxmyc"
            result = urllib.urlopen(url).read()
            count = result.count('kind') - 1
            obj_result = tornado.escape.json_decode(result)
            for x in xrange(0,count):
                html = obj_result['items'][x]['link']
                link = str(html)
                linkall = linkall + link + "<br>"
                crl = pycurl.Curl()
                crl.setopt(pycurl.VERBOSE,1)
                crl.setopt(pycurl.FOLLOWLOCATION, 1)
                crl.setopt(pycurl.MAXREDIRS, 5)
                crl.fp = StringIO.StringIO()
                crl.setopt(pycurl.URL, link)
                crl.setopt(crl.WRITEFUNCTION, crl.fp.write)
                crl.perform()
                soup = BeautifulSoup(crl.fp.getvalue())
                ans = soup.find("div", { "class" : "about_content" })
                content = strip_tags(ans.prettify())
                if 'Assignee' in content:
                    array = content.split('Assignee')                
                    arr = array[1].split('Primary')
                    ass = arr[0].split(':')
                    assarray.append(ass[1])
                    leng = len(assarray)
                pass
            pass
            page = page + 10
        pass

        data = tornado.escape.json_encode(leng)
        #self.render("google.html", entries="test")
        self.write(assarray[0])

class Lavender_STPI(BaseHandler):
    def get(self):
         #宣告區
        pages = 1
        test = ""
        litigation=0
        two =""
        length =""
        p = []
        d = []
        decom = []
        w = unicode('告', 'utf-8')

        keyword = self.get_argument("keyword", default=None, strip=False)
        while pages < 20:
            startindex = str(pages)
            url = "https://www.googleapis.com/customsearch/v1?q="+keyword+"&start="+startindex+"&key=AIzaSyCSGM0fArmZcWnu2GD2ZHG_tGX3mQl9rCI&cx=005971756043172606388:edll3ji0ejq"
            result = urllib.urlopen(url).read()
            count = result.count('kind') - 1
            obj_result = tornado.escape.json_decode(result)


            #找出訴訟並紀錄
            for x in xrange(0,count):
                
                if  w in obj_result['items'][x]['title']:
                    litigation = litigation+1
                    test = obj_result['items'][x]['link']
                    links = str(test)
                    if links is not None:
                        crl = pycurl.Curl()
                        crl.setopt(pycurl.VERBOSE,1)
                        crl.setopt(pycurl.FOLLOWLOCATION, 1)
                        crl.setopt(pycurl.MAXREDIRS, 5)
                        crl.fp = StringIO.StringIO()
                        crl.setopt(pycurl.URL, links)
                        crl.setopt(crl.WRITEFUNCTION, crl.fp.write)
                        crl.perform()
                        a = crl.fp.getvalue()

                        #找出訴訟名稱裡的原套被告
                        litiname = a.split('訴訟名稱')
                        liticom = litiname[1].split('提告日期')
                        
                    pass
                pass
            pass
            pages = pages + 10
        pass
        data = tornado.escape.json_encode(obj_result)
        self.write(a)
    

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

class TestHandler(BaseHandler):
    def get(self):
        keyword = self.get_argument("keyword", default=None, strip=False)
        p = 0
        while p<10:
            p=p+1
            pass
        t = str(p)

        self.write(t)
       
class ComposeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        id = self.get_argument("id", None)
        entry = None
        if id:
            entry = self.db.get("SELECT * FROM entries WHERE id = %s", int(id))
        self.render("compose.html", entry=entry)

    @tornado.web.authenticated
    def post(self):
        id = self.get_argument("id", None)
        title = self.get_argument("title")
        text = self.get_argument("markdown")
        html = markdown.markdown(text)
        if id:
            entry = self.db.get("SELECT * FROM entries WHERE id = %s", int(id))
            if not entry: raise tornado.web.HTTPError(404)
            slug = entry.slug
            self.db.execute(
                "UPDATE entries SET title = %s, markdown = %s, html = %s "
                "WHERE id = %s", title, text, html, int(id))
        else:
            slug = unicodedata.normalize("NFKD", title).encode(
                "ascii", "ignore")
            slug = re.sub(r"[^\w]+", " ", slug)
            slug = "-".join(slug.lower().strip().split())
            if not slug: slug = "entry"
            while True:
                e = self.db.get("SELECT * FROM entries WHERE slug = %s", slug)
                if not e: break
                slug += "-2"
            self.db.execute(
                "INSERT INTO entries (author_id,title,slug,markdown,html,"
                "published) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP())",
                self.current_user.id, title, slug, text, html)
        self.redirect("/entry/" + slug)
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


class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    #http_server.listen(options.port)
    http_server.listen(int(sys.argv[1]))
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
