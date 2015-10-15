from google.appengine.api import users

from Stream import StreamModel, CountViewModel, PictureModel
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext import blobstore

import webapp2
from ViewHandler import View

import os
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class ManagementPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        View.more = True
        if (user):

            url = users.create_logout_url(self.request.url)
            url_linktext = 'Logout'
            stream_query = StreamModel.query(StreamModel.author==user).order(-StreamModel.createTime).fetch()
            stream_query_all = StreamModel.query().fetch()
            findone = 0

            if (len(stream_query_all)>0):
                for stream in stream_query_all:
                    if user.nickname() in stream.subscribers:
                        findone = 1

            template_values = {
                'user': user,
                'url': url,
                'url_linktext': url_linktext,
                'stream_query_len': len(stream_query),
                'stream_query': stream_query,
                'stream_query_all': stream_query_all,
                'stream_query_all_len': len(stream_query_all),
                'find_done': findone,
            }
            template = JINJA_ENVIRONMENT.get_template('templates/management.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect('/')

class deleteStream(webapp2.RequestHandler):
    def post(self):
        returnURL = self.request.headers['Referer']
        streams = self.request.get_all("deleteStream")
        if len(streams) > 0:
            countViews = CountViewModel.query(CountViewModel.name.IN(streams)).fetch()
            ndb.delete_multi(ndb.put_multi(countViews))
            stream_query = StreamModel.query(StreamModel.name.IN(streams), StreamModel.author==users.get_current_user())
            streams = stream_query.fetch()
            for stream in streams:
                 pictures = db.GqlQuery("SELECT *FROM PictureModel WHERE ANCESTOR IS :1", db.Key.from_path('StreamModle',stream.name))
                 db.delete(pictures)
            # for stream in streams:
            #     pictures = PictureModel.query(PictureModel.stream == stream.name).fetch()
            #     if len(pictures)>0:
            #         for picture in pictures:
            #             blobstore.delete(picture.blob_key)
            #             picture.key.delete()
            ndb.delete_multi(ndb.put_multi(streams))
        #self.response.write("delete")
        self.redirect(returnURL)

class unSubscribe(webapp2.RequestHandler):
    def post(self):
        returnURL = self.request.headers['Referer']
        streams = self.request.get_all("unSubscribe")

        if len(streams) > 0:
            stream_query = StreamModel.query(StreamModel.name.IN(streams))
            streams = stream_query.fetch()
            for stream in streams:
                stream.subscribers.remove(users.get_current_user().nickname())
                stream.put()

        self.redirect(returnURL)


app = webapp2.WSGIApplication([
    ('/manage', ManagementPage),
    ('/deletestream', deleteStream),
    ('/unsubscribe', unSubscribe),
], debug=True)
