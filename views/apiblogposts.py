import tornado.auth
import tornado.database
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from views.basehandler import BaseHandler

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