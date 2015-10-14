from Stream import PictureModel, StreamModel, CountViewModel
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.api import blobstore
from google.appengine.ext import ndb
from google.appengine.ext import db
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
from ViewHandler import View
from datetime import datetime, date


import webapp2
import re
import urllib
import json
import time

import os
import jinja2
import random

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


NUM_PICTURE_PER_STREAM = 3

index = 0

class RoutingError(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/routingerror.html')
        self.response.write(template.render())

class ViewSingle(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        stream_name = re.findall('%3D(.*)', self.request.url)[0]
        if (stream_name == ""):
            self.redirect('/routingerror')
        template = JINJA_ENVIRONMENT.get_template('templates/viewsingle.html')

        stream_query = StreamModel.query(StreamModel.name==stream_name).fetch()
        if (len(stream_query) == 0):
            self.redirect('/routingerror')
        else:
            stream = stream_query[0]

            picture_query = db.GqlQuery("SELECT *FROM PictureModel WHERE ANCESTOR IS :1 ORDER BY uploadDate DESC",
                                      db.Key.from_path('StreamModel', stream_name))
            #picture_query = PictureModel.query(PictureModel.stream == stream_name).order(-PictureModel.uploadDate).fetch()

            global index

            showNum = 0

            picture_info = []
            #upload_url = blobstore.create_upload_url('/upload')
            for picture in picture_query[index:stream.totalPicture]:
                if (showNum < NUM_PICTURE_PER_STREAM):
                    picture_info.append((showNum, picture.id, picture.key()))
                    showNum += 1
                    #self.response.write(picture.id)

            morePictureURL = urllib.urlencode({'showmore':stream_name+"=="+str(index)})
            geoviewURL = urllib.urlencode({'geoview':stream_name})

            countView_query = CountViewModel.query(CountViewModel.name==stream_name).fetch()

            if user.nickname() in stream.subscribers:
                url = urllib.urlencode({'unsubscribesingle':stream_name})
            else:
                url = urllib.urlencode({'subscribe':stream_name})
            if (stream.author == user):
                pass
            else:
                #if len(countView_query)>0:
                if View.more == True:
                    countView = countView_query[0]
                    countView.count = countView.count + 1
                    countView.total = countView.total + 1
                    countView.put()
                View.more = False

            template_values = {
                'user': user,
                'stream_name': stream_name,
                'stream': stream,
                'picture_info': picture_info,
                #'upload_url': upload_url,
                'picture_per_stream': NUM_PICTURE_PER_STREAM,
                'more_pictureURL': morePictureURL,
                'countView_query': countView_query,
                'url': url,
                'GeoViewURL': geoviewURL
            }
            self.response.write(template.render(template_values))



#class ViewPictureHandler(blobstore_handlers.BlobstoreDownloadHandler):
    # def get(self, photo_key):
    #     self.send_blob(photo_key)

class ViewPictureHandler(webapp2.RequestHandler):
    def get(self):
        #self.send_blob(photo_key)
        pic = db.get(self.request.get('pic_id'))
        self.response.out.write(pic.picture)

# class Upload(blobstore_handlers.BlobstoreUploadHandler):
#     def post(self):
#         returnURL = self.request.headers['Referer']
#         #picture = self.request.get('file')
#         upload = self.get_uploads()[0]
#         if (len(picture)>0):
#             stream_name = re.findall('=(.*)', returnURL)[0]
#             stream_query = StreamModel.query(StreamModel.name==stream_name)
#             stream = stream_query.fetch()[0]
#             if (stream.author == users.get_current_user()):
#                 stream.totalPicture = stream.totalPicture + 1
#                 #user_picture = PictureModel(parent = db.Key.from_path('StreamModel', stream_name))
#                 #user_picture.id = str(stream.totalPicture)
#                 #picture = images.resize(picture, 320, 400)
#                 #user_picture.picture = db.Blob(picture)
#                 user_picture = PictureModel(stream=stream_name,
#                                             id=str(stream.totalPicture),
#                                             blob_key=upload.key())
#                 stream.lastUpdated = user_picture.uploadDate
#                 user_picture.put()
#                 stream.put()
#         self.redirect(returnURL)

class Upload(webapp2.RequestHandler):
    def post(self):
        returnURL = self.request.headers['Referer']
        pictures = self.request.get_all('files[]')
        #upload = self.get_uploads()[0]
        if (len(pictures)>0):
            stream_name = re.findall('=(.*)', returnURL)[0]
            stream_query = StreamModel.query(StreamModel.name==stream_name)
            stream = stream_query.fetch()[0]
            if (stream.author == users.get_current_user()):
                for picture in pictures:
                    stream.totalPicture = stream.totalPicture + 1
                    user_picture = PictureModel(parent = db.Key.from_path('StreamModel', stream_name))
                    user_picture.id = str(stream.totalPicture)
                    picture = images.resize(picture, 320, 400)
                    user_picture.picture = db.Blob(picture)
                    # user_picture = PictureModel(stream=stream_name,
                    #                             id=str(stream.totalPicture),
                    #                             blob_key=upload.key())
                    stream.lastUpdated = user_picture.uploadDate
                    user_picture.put()
                stream.put()
        self.redirect(returnURL)

class ShowMore(webapp2.RequestHandler):
    def post(self):
        global index
        returnURL = self.request.headers['Referer']
        stream_name = re.findall('%3D(.*)%3D%3D', self.request.url)[0]
        oldIndex = int(re.findall('%3D%3D(.*)', self.request.url)[0])
        stream = StreamModel.query(StreamModel.name == stream_name).fetch()[0]
        index = oldIndex + NUM_PICTURE_PER_STREAM
        if index >= stream.totalPicture:
            index = 0
        self.redirect(returnURL)

class clearViewCount(webapp2.RequestHandler):
    def get(self):
        countView = CountViewModel.query().fetch()
        if len(countView)>0:
            for count in countView:
                count.count = 0
                count.put()

class Subscirbe(webapp2.RequestHandler):
    def post(self):
        returnURL = self.request.headers['Referer']
        stream_name = re.findall("subscribe%3D(.*)",self.request.url)[0]
        stream_query = StreamModel.query(StreamModel.name==stream_name).fetch()
        if len(stream_query)>0:
            stream = stream_query[0]
            stream.subscribers.append(users.get_current_user().nickname())
            stream.put()
        self.redirect(returnURL)

class UnsubscribeSingle(webapp2.RequestHandler):
    def post(self):
        returnURL = self.request.headers['Referer']
        stream_name = re.findall("unsubscribesingle%3D(.*)",self.request.url)[0]
        stream_query = StreamModel.query(StreamModel.name==stream_name).fetch()
        if len(stream_query)>0:
            stream = stream_query[0]
            stream.subscribers.remove(users.get_current_user().nickname())
            stream.put()
        self.redirect(returnURL)

class GeoView(webapp2.RequestHandler):
    def get(self):
        stream_name = re.findall('%3D(.*)', self.request.url)[0]
        stream_query = StreamModel.query(StreamModel.name == stream_name).fetch()
        if (stream_name == ""):
            self.redirect('/routingerror')
        if (len(stream_query) == 0):
            self.redirect('/routingerror')
        else:
            stream = stream_query[0]
            pictures = db.GqlQuery("SELECT *FROM PictureModel WHERE ANCESTOR IS :1 ORDER BY uploadDate DESC",
                                          db.Key.from_path('StreamModel', stream_name))
            pictures_key = []
            for picture in pictures:
                pictures_key.append(str(picture.key()))
            stream_url = urllib.urlencode({'streamname': stream.name})

            template = JINJA_ENVIRONMENT.get_template('templates/geoview.html')
            template_values = {
                'stream_name': stream_name,
                'min': str(stream.createTime),
                'num': str(),
                'keys': pictures_key,
                'stream_url': stream_url
            }
            self.response.write(template.render(template_values))

class GeoViewHandler(webapp2.RequestHandler):
    def post(self):
        stream_name = self.request.get("stream_name")
        min = self.request.get("min")
        max = self.request.get("max")
        pictures = db.GqlQuery("SELECT *FROM PictureModel WHERE ANCESTOR IS :1 ORDER BY uploadDate DESC",
                                      db.Key.from_path('StreamModel', stream_name))
        info = {}
        begin = min.split(" ")
        end = max.split(" ")
        lower = begin[1] + " " + begin[2] + " " + begin[3]
        upper = end[1] + " " + end[2] + " " + end[3]
        l = datetime.strptime(lower, "%b %d %Y")
        u = datetime.strptime(upper, "%b %d %Y")
        stream_url = urllib.urlencode({'streamname': stream_name})
        info["label"] = []
        pos = {}
        for picture in pictures:
            if picture.Date > l.date() and picture.Date <= u.date():
                m = {}
                label = '<a href="'+ stream_url +'">'+\
                         '<img src="pic?pic_id=' + str(picture.key()) +'"  height="100" width="100" />' +\
                         '<br>' + str(picture.Date) + '</a>'
                m['lat'] = picture.lat
                m['lg'] = picture.lg
                m["label"] = label
                info["label"].append(m)
        info=json.dumps(info)
        self.response.headers['Content-Type'] = "application/json"
        self.response.write(info)

class Image(webapp2.RequestHandler):
    def get(self):
        pic = db.get(self.request.get('pic_id'))
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(pic.picture)

app = webapp2.WSGIApplication([
    ('/showmore.*', ShowMore),
    ('/stream.*', ViewSingle),
    ('/upload', Upload),
    ('/pic.*', ViewPictureHandler),
    ('/subscribe.*', Subscirbe),
    ('/clearviewcount', clearViewCount),
    ('/unsubscribesingle.*', UnsubscribeSingle),
    ('/routingerror', RoutingError),
    ('/geoview.*', GeoView),
    ('/getimage.*', Image),
    ('/geo', GeoViewHandler)
], debug=True)
