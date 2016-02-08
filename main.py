# -*- coding: utf-8 -*-
import os
import json
import logging
import urllib
import urllib2
import string
import random
from settings import TOKEN, HOOK_TOKEN

# standard app engine imports
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google.appengine.api import memcache
import webapp2

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'
# ================================

class Chat(ndb.Model):
    # key name: str(apikey)
    chat_id = ndb.IntegerProperty()

# ================================

def token():
    smpl = string.digits+string.lowercase+string.uppercase
    tkn = ''.join(random.sample(smpl,32))
    if tkn == HOOK_TOKEN:
        return token()
    return tkn

def createChat(chat_id):
    chat = Chat.query(Chat.chat_id==chat_id).get(keys_only=True)
    if not chat:
        tkn = token()
        chat = Chat.get_or_insert(str(tkn))
        chat.chat_id = chat_id
        cid = chat.put()
        return cid.id()
    else:
        return chat.id()


def deleteChat(chat_id):
    pass

def getChat(token):
    chat = Chat.get_by_id(str(token))
    if chat:
        return chat.chat_id
    return False

# ================================

class MessageHandler(webapp2.RequestHandler):
    def get(self, **kwargs):

        def sendMessage(chat_id, msg, mode):
            payload = {
                'chat_id': str(chat_id),
                'text': msg.encode('utf-8'),
                'disable_web_page_preview': 'true',
            }
            if mode: payload.update({'parse_mode': mode})

            resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode(payload)).read()

        user = kwargs['user']
        message = self.request.get('message')
        if not message:
            self.response.set_status(400)
            self.response.write('<html><head><title>400 Bad Request</title></head><body><h1>400 Bad Request</h1>The Message is empty.<br /><br /></body></html>')
            return
        chat_id = getChat(user)
        if not chat_id:
            self.response.set_status(400)
            self.response.write('<html><head><title>400 Bad Request</title></head><body><h1>400 Bad Request</h1>User Unknown.<br /><br /></body></html>')
            return

        mode = self.request.get('mode')
        if not mode: mode = False
        elif not mode or mode.lower() not in ['markdown', 'html']:
            self.response.set_status(400)
            self.response.write('<html><head><title>400 Bad Request</title></head><body><h1>400 Bad Request</h1>Parse mode Unknown.<br /><br /></body></html>')
            return

        sendMessage(chat_id, message, mode)
        self.response.write('')



# ================================

class HomeHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'rnd': '1',
        }
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path,template_values))

# ================================

class hookHandler(webapp2.RequestHandler):
    def post(self):
        body = json.loads(self.request.body)

        update_id = body['update_id']
        message = body['message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']

        if not text:
            logging.info('no text')
            return

        def reply(msg=None):
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                })).read()
            else:
                logging.error('no msg specified')
                resp = None

        if text.startswith('/'):
            if text == '/start':
                tkn = createChat(chat_id)
                reply(tkn)
#            elif text == '/token':
#                reply('token')
#            elif text == '/help':
#                reply('Help')
#            elif text == '/stop':
#                reply('token removed, bot stopped')
            else:
                reply('Bzz')


app = webapp2.WSGIApplication([
    webapp2.Route('/', HomeHandler),
    webapp2.Route('/<user>/send', MessageHandler, name='user'),
    webapp2.Route('/' + HOOK_TOKEN + '/hook', hookHandler),
], debug=True)
