__author__ = 'rongshengxu'
# -*- coding: utf-8 -*-
#
# jQuery File Upload Plugin GAE Python Example
# https://github.com/blueimp/jQuery-File-Upload
#
# Copyright 2011, Sebastian Tschan
# https://blueimp.net
#
# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT
#
from google.appengine.ext import ndb, db
from google.appengine.ext import blobstore, deferred
from google.appengine.api import memcache, images
from Stream import StreamModel, PictureModel
import json
import os
import re
import urllib
import webapp2
import random

DEBUG=os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
WEBSITE = 'https://blueimp.github.io/jQuery-File-Upload/'
MIN_FILE_SIZE = 1  # bytes
# Max file size is memcache limit (1MB) minus key size minus overhead:
MAX_FILE_SIZE = 999000  # bytes
IMAGE_TYPES = re.compile('image/(gif|p?jpeg|(x-)?png)')
ACCEPT_FILE_TYPES = IMAGE_TYPES
THUMB_MAX_WIDTH = 80
THUMB_MAX_HEIGHT = 80
THUMB_SUFFIX = '.'+str(THUMB_MAX_WIDTH)+'x'+str(THUMB_MAX_HEIGHT)+'.png'
EXPIRATION_TIME = 300  # seconds
# If set to None, only allow redirects to the referer protocol+host.
# Set to a regexp for custom pattern matching against the redirect value:
REDIRECT_ALLOW_TARGET = None

class CORSHandler(webapp2.RequestHandler):
    def cors(self):
        headers = self.response.headers
        headers['Access-Control-Allow-Origin'] = '*'
        headers['Access-Control-Allow-Methods'] =\
            'OPTIONS, HEAD, GET, POST, DELETE'
        headers['Access-Control-Allow-Headers'] =\
            'Content-Type, Content-Range, Content-Disposition'

    def initialize(self, request, response):
        super(CORSHandler, self).initialize(request, response)
        self.cors()

    def json_stringify(self, obj):
        return json.dumps(obj, separators=(',', ':'))

    def options(self, *args, **kwargs):
        pass

class UploadHandler(webapp2.RequestHandler):

    def initialize(self, request, response):
        super(UploadHandler, self).initialize(request, response)
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Methods'] =\
            'OPTIONS, HEAD, GET, POST, DELETE'
        self.response.headers['Access-Control-Allow-Headers'] =\
            'Content-Type, Content-Range, Content-Disposition'

    def json_stringify(self, obj):
        return json.dumps(obj, separators=(',', ':'))

    def validate(self, file):
        if file['size'] < MIN_FILE_SIZE:
            file['error'] = 'File is too small'
        elif file['size'] > MAX_FILE_SIZE:
            file['error'] = 'File is too big'
        elif not ACCEPT_FILE_TYPES.match(file['type']):
            file['error'] = 'Filetype not allowed'
        else:
            return True
        return False

    # def validate_redirect(self, redirect):
    #     if redirect:
    #         if REDIRECT_ALLOW_TARGET:
    #             return REDIRECT_ALLOW_TARGET.match(redirect)
    #         referer = self.request.headers['referer']
    #         if referer:
    #             from urlparse import urlparse
    #             parts = urlparse(referer)
    #             redirect_allow_target = '^' + re.escape(
    #                 parts.scheme + '://' + parts.netloc + '/'
    #             )
    #         return re.match(redirect_allow_target, redirect)
    #     return False

    def get_file_size(self, file):
        file.seek(0, 2)  # Seek to the end of the file
        size = file.tell()  # Get the position of EOF
        file.seek(0)  # Reset the file position to the beginning
        return size

    # def write_blob(self, data, info):
    #     key = urllib.quote(info['type'].encode('utf-8'), '') +\
    #         '/' + str(hash(data)) +\
    #         '/' + urllib.quote(info['name'].encode('utf-8'), '')
    #     try:
    #         user_picture = PictureModel(parent = db.Key.from_path('StreamModel', stream_name))
    #         user_picture.id = str(stream.totalPicture)
    #         picture = images.resize(picture, 320, 400)
    #         user_picture.picture = db.Blob(picture)
    #         #memcache.set(key, data, time=EXPIRATION_TIME)
    #     except: #Failed to add to memcache
    #         return (None, None)
    #     thumbnail_key = None
    #     if IMAGE_TYPES.match(info['type']):
    #         try:
    #             img = images.Image(image_data=data)
    #             img.resize(
    #                 width=THUMB_MAX_WIDTH,
    #                 height=THUMB_MAX_HEIGHT
    #             )
    #             thumbnail_data = img.execute_transforms()
    #             thumbnail_key = key + THUMB_SUFFIX
    #             memcache.set(
    #                 thumbnail_key,
    #                 thumbnail_data,
    #                 time=EXPIRATION_TIME
    #             )
    #         except: #Failed to resize Image or add to memcache
    #             thumbnail_key = None
    #     return (key, thumbnail_key)
    
    #@db.transactional(xg=True)
    def write_data(self, stream, stream_name, picture):
        stream.totalPicture = stream.totalPicture + 1
        user_picture = PictureModel(parent = db.Key.from_path('StreamModel', stream_name))
        user_picture.id = str(stream.totalPicture)
        picture = images.resize(picture, 320, 400)
        user_picture.picture = db.Blob(picture)
        stream.lastUpdated = user_picture.uploadDate
        db.put_async(user_picture)

    @ndb.transactional(retries=20)
    def add(self, key):
        s = key.get()
        s.totalPicture = s.totalPicture + 1
        num = s.totalPicture
        s.put()
        return num

    #@ndb.transactional
    def handle_upload(self, stream_name):
        results = []
        stream_query = StreamModel.query(StreamModel.name==stream_name)
        stream = stream_query.fetch()[0]
        for name, fieldStorage in self.request.POST.items():
            if type(fieldStorage) is unicode:
                continue
            result = {}
            result['name'] = re.sub(
                r'^.*\\',
                '',
                fieldStorage.filename)
            result['type'] = fieldStorage.type
            result['size'] = self.get_file_size(fieldStorage.file)
            if self.validate(result):
                picture = fieldStorage.value
                #self.write_data(stream, stream_name, picture)
                #num = num+1
                num = self.add(ndb.Key('StreamModel', stream.key.id()))
                user_picture = PictureModel(parent = db.Key.from_path('StreamModel', stream_name))
                user_picture.id = str(num)
                picture = images.resize(picture, 640, 800)
                user_picture.picture = db.Blob(picture)
                stream.lastUpdated = user_picture.uploadDate
                user_picture.lat = random.random()
                user_picture.lg = random.random()
                user_picture.put()
                # key = self.write_blob(
                #     picture, result
                # )
                # if key is not None:
            results.append(result)
        return results
    def get(self):
        returnURL = self.request.headers['Referer']
        self.redirect(returnURL)

    def post(self):
        returnURL = self.request.headers['Referer']
        stream_name = re.findall('=(.*)', returnURL)[0]
        # if (self.request.get('_method') == 'DELETE'):
        #     return self.delete()
        results = self.handle_upload(stream_name)
        result = {'files': results}
        s = self.json_stringify(result)
        if 'application/json' in self.request.headers.get('Accept'):
            self.response.headers['Content-Type'] = 'application/json'
        self.response.write(s)

app = webapp2.WSGIApplication(
    [
        ('/upload', UploadHandler)
    ],
    debug=True
)