from Stream import PictureModel, StreamModel, CountViewModel
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import db
from ViewHandler import View

import webapp2
import re
import urllib

import os
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


NUM_PICTURE_PER_STREAM = 3

UPLOAD_ENTRY_TEMPLATE = """\
<form action="/upload" method="post" enctype="multipart/form-data">
    Upload File:
    <input type="file"  name="file" >
    <br>
    <input type="submit" name="submit" value="Submit">
</form>
"""

SUBSCRIBE_ENTRY_TEMPLATE = """\
<form action="%s" method="post">
    <input type="submit" value="Subscribe">
</form>
"""

UNSUBSCRIBE_ENTRY_TEMPLATE = """\
<form action="%s" method="post">
    <input type="submit" value="Unsubscribe">
</form>
"""

MORE_ENTRY_TEMPLATE = """\
<form action="%s" ,method="post">
    <input type="submit" value="More Pictures">
</form>
<hr>
"""

PICTURE_ENTRY_TEMPLATE = """\
<td><img src="pic?pic_id=%s"></img></td>
"""

index = 0

class ViewSingle(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        stream_name = re.findall('%3D(.*)', self.request.url)[0]
        template = JINJA_ENVIRONMENT.get_template('templates/viewsingle.html')

        stream_query = StreamModel.query(StreamModel.name==stream_name)
        stream = stream_query.fetch()[0]

        picture_query = db.GqlQuery("SELECT *FROM PictureModel WHERE ANCESTOR IS :1 ORDER BY uploadDate DESC",
                                  db.Key.from_path('StreamModel', stream_name))

        global index

        showNum = 0

        picture_info = []

        for picture in picture_query[index:stream.totalPicture]:
            if (showNum < NUM_PICTURE_PER_STREAM):
                picture_info.append((showNum, picture.id, picture.key()))
                showNum += 1

        morePictureURL = urllib.urlencode({'showmore':stream_name+"=="+str(index)})
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
            'picture_per_stream': NUM_PICTURE_PER_STREAM,
            'more_pictureURL': morePictureURL,
            'countView_query': countView_query,
            'url': url
        }
        self.response.write(template.render(template_values))



class ViewPictureHandler(webapp2.RequestHandler):
    def get(self):
        pic = db.get(self.request.get('pic_id'))
        self.response.out.write(pic.picture)

class Upload(webapp2.RequestHandler):
    def post(self):
        returnURL = self.request.headers['Referer']
        picture = self.request.get('file')
        if (len(picture)>0):
            stream_name = re.findall('=(.*)', returnURL)[0]
            stream_query = StreamModel.query(StreamModel.name==stream_name)
            stream = stream_query.fetch()[0]
            if (stream.author == users.get_current_user()):
                stream.totalPicture = stream.totalPicture + 1
                user_picture = PictureModel(parent = db.Key.from_path('StreamModel', stream_name))
                user_picture.id = str(stream.totalPicture)
                picture = images.resize(picture, 320, 400)
                user_picture.picture = db.Blob(picture)
                stream.lastUpdated = user_picture.uploadDate
                user_picture.put()
                stream.put()
        self.redirect(returnURL)

class ShowMore(webapp2.RequestHandler):
    def get(self):
        global index
        returnURL = self.request.headers['Referer']
        stream_name = re.findall('%3D(.*)%3D%3D', self.request.url)[0]
        oldIndex = int(re.findall('%3D%3D(.*)', self.request.url)[0])
        stream = StreamModel.query(StreamModel.name == stream_name).fetch()[0]
        # countView_query = CountViewModel.query(CountViewModel.name==stream_name).fetch()
        #
        # if stream.author == users.get_current_user():
        #     pass
        # else:
        #     countView = countView_query[0]
        #     self.response.write(countView.count)
        #     countView.count = countView.count - 1
        #     countView.total = countView.total - 1
        #     countView.put()
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
        self.response.write(self.request.url)
        stream_name = re.findall("subscribe%3D(.*)",self.request.url)[0]
        self.response.write(stream_name)
        stream_query = StreamModel.query(StreamModel.name==stream_name).fetch()
        if len(stream_query)>0:
            stream = stream_query[0]
            stream.subscribers.append(users.get_current_user().nickname())
            stream.put()
        self.redirect(returnURL)

class UnsubscribeSingle(webapp2.RequestHandler):
    def post(self):
        returnURL = self.request.headers['Referer']
        self.response.write(self.request.url)
        stream_name = re.findall("unsubscribesingle%3D(.*)",self.request.url)[0]
        self.response.write(stream_name)
        stream_query = StreamModel.query(StreamModel.name==stream_name).fetch()
        if len(stream_query)>0:
            stream = stream_query[0]
            stream.subscribers.remove(users.get_current_user().nickname())
            stream.put()
        self.redirect(returnURL)

app = webapp2.WSGIApplication([
    ('/showmore.*', ShowMore),
    ('/stream.*', ViewSingle),
    ('/upload', Upload),
    ('/pic.*', ViewPictureHandler),
    ('/subscribe.*', Subscirbe),
    ('/clearviewcount', clearViewCount),
    ('/unsubscribesingle.*', UnsubscribeSingle)
], debug=True)
