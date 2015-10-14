from Stream import StreamModel
import webapp2
import re
from ViewHandler import View

import os
import jinja2
import json

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

class AutoAPI(webapp2.RequestHandler):
     def get(self):
        # patten = self.request.get('term')
        # print patten
        streams = StreamModel.query().fetch()
        namelist = list()
        for stream in streams:
            # if patten in stream.name:
            namelist.append(stream.name)
            for tag in stream.tag:
                # if (patten in tag) and (tag != ""):
                    namelist.append(tag)

        namelist.sort()
        list_json = {"namelist": namelist}

        self.response.headers['Content-Type'] = 'application/json'
        list_json = json.dumps(list_json)
        self.response.write(list_json)


app = webapp2.WSGIApplication([
    ('/search', Search),
    ('/searchresult', SearchResult),
    ('/autoapi.*', AutoAPI),
], debug=True)
