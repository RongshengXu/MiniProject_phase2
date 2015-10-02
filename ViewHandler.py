from Stream import StreamModel
import webapp2

import os
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class View(webapp2.RequestHandler):
    more = True
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/view.html')
        stream_query = StreamModel.query().order(StreamModel.createTime).fetch()
        index_info = []
        num = 0
        if len(stream_query) > 0:
            self.more = True
            for stream in stream_query:
                index_info.append((stream.name, stream.coverpageURL, stream.url, num))
                if num==3:
                    num = 0
                else:
                    num += 1
        template_values = {
            'stream_query_len': len(stream_query),
            'index_info': index_info
        }
        self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/view', View)
], debug=True)