from google.appengine.api import users

import webapp2
import os
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class LoginPage(webapp2.RequestHandler):
    def get(self):
        if users.get_current_user():
            self.redirect('/manage')
        else:
            url = users.create_login_url(self.request.url)
            url_linktext = 'Sign in with Google'
            template_values = {
                'url' : url,
                'url_linktext': url_linktext
            }
            template = JINJA_ENVIRONMENT.get_template('templates/login.html')
            self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/', LoginPage),
], debug=True)
