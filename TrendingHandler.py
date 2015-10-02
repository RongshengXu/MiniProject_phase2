from Stream import StreamModel
from Stream import CountModel, CountViewModel
from google.appengine.api import users
from google.appengine.api import mail
import webapp2
from ViewHandler import View

import os
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

SERVICE_DOMAIN="sacred-highway-108321"
MAILBOX=".appspotmail.com"
EMAIL_SENDER="Connexus"

freq_dict = {0: 'No reports', 1:'Every 5 minutes', 12:'Every 1 hour', 288:'Every day'}

DEFAULT_TRENDING_MESSAGE = "Trending update"
DEFAULT_TRENDING_SUBJECT = "Trending digest from "
TAEmail1 = "nima.dini@utexas.edu"
TAEmail2 = "kevzsolo@gmail.com"

class Trending(webapp2.RequestHandler):
    def get(self):
        View.more = True
        template = JINJA_ENVIRONMENT.get_template('templates/trending.html')
        countView_query = CountViewModel.query().order(-CountViewModel.count).fetch()
        index = 0
        infos = []
        if len(countView_query)> 0:
            for view in countView_query:
                if index < 3:
                    index += 1
                    stream_query = StreamModel.query(StreamModel.name == view.name).fetch()
                    if len(stream_query)>0:
                        stream = stream_query[0]
                        infos.append((stream.name, stream.coverpageURL, stream.url, str(view.count)))
        count_query = CountModel.query(CountModel.name=="Trending").fetch()
        freq = "No reports"
        if len(count_query)==0:
            count = CountModel(name="Trending", count=0, freq=0)
            count.put()
        else:
            count = count_query[0]
            freq = freq_dict[count.freq]

        template_values = {
            'infos': infos,
            'freq': freq
        }
        self.response.write(template.render(template_values))

class Update(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        returnURL = self.request.headers['Referer']
        frequency = self.request.get("frequency")
        count_query = CountModel.query(CountModel.name=="Trending").fetch()
        if len(count_query)>0:
            count = count_query[0]
            if frequency == "No reports":
                count.f = 0
                count.freq = 0
            elif frequency == "Every 5 minutes":
                count.f = 1
                count.freq = 1
            elif frequency == "Every 1 hour":
                count.f = 12
                count.freq = 12
            elif frequency == "Every day":
                count.f = 288
                count.freq = 288
            count.put()
        self.redirect(returnURL)

class CountDown(webapp2.RequestHandler):
    def get(self):
        sender = EMAIL_SENDER + "@"+SERVICE_DOMAIN+MAILBOX
        cd_query = CountModel.query(CountModel.name=="Trending").fetch()
        if (len(cd_query)>0):
            cd = cd_query[0]
            if cd.freq != 0:
                cd.count = cd.count + 1
                if (cd.count == cd.freq):
                    cd.count = 0
                    subject = DEFAULT_TRENDING_SUBJECT + EMAIL_SENDER
                    mail.send_mail(sender=sender, to=TAEmail1, subject=subject, body=DEFAULT_TRENDING_MESSAGE)
                    mail.send_mail(sender=sender, to=TAEmail2, subject=subject, body=DEFAULT_TRENDING_MESSAGE)
                    mail.send_mail(sender=sender, to="xurongsheng2010@gmail.com", subject=subject, body=DEFAULT_TRENDING_MESSAGE)
                    mail.send_mail(sender=sender, to="yangxuanemail@gmail.com", subject=subject, body=DEFAULT_TRENDING_MESSAGE)
                cd.put()
        #else:
            #mail.send_mail(sender="test@example.com", to="xurongsheng2010@gmail.com", subject="test", body=DEFAULT_TRENDING_MESSAGE)


app = webapp2.WSGIApplication([
    ('/trending', Trending),
    ('/update', Update),
    ('/countdown', CountDown)
], debug=True)

