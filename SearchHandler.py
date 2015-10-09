from Stream import StreamModel
import webapp2
import re
from ViewHandler import View

import os
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Search(webapp2.RequestHandler):
    def get(self):
        View.more = True
        template = JINJA_ENVIRONMENT.get_template('templates/search.html')
        self.response.write(template.render())

class SearchResult(webapp2.RequestHandler):
    def get(self):
        View.more = True
        template = JINJA_ENVIRONMENT.get_template('templates/searchresult.html')
        pattern = self.request.get("searchPattern")
        found_in_tag = False
        Name = []
        streams = StreamModel.query().fetch()
        for st in streams:
            Name.append(st.name)
        num = 0
        infos = []
        for name in Name:
            fi = re.findall(pattern, name)
            stream = StreamModel.query(StreamModel.name==name).fetch()[0]
            for tag in stream.tag:
                if len(re.findall(pattern,tag))>0:
                    found_in_tag = True
            if len(fi)>0 or found_in_tag==True:
                infos.append((stream.name, stream.coverpageURL, stream.url, num))
                if num==3:
                    num = 0
                else:
                    num += 1
        template_values = {
            'infos': infos
        }
        self.response.write(template.render(template_values))

class AutoApi(webapp2.ResponseHeaders):
    def post(self):
        streams = StreamModel.query().fetch()
        namelist = list()
        for stream in streams:
            namelist.append(stream.name)


app = webapp2.WSGIApplication([
    ('/search', Search),
    ('/searchresult', SearchResult),
    ('/autoapi', AutoApi),
], debug=True)
