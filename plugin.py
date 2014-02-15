###
# Copyright (c) 2014, Gabriel Morell-Pacheco
# All rights reserved.
#
#
###
import requests
import json
import datetime
import pytz
import json
import threading
import time

import dateutil.parser

from random import choice
import os

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs

from secrets import GITHUB_KEY
from conf import TARGET_CHANNEL
SLEEP_TIME = 300

class FlexoGit(callbacks.Plugin):
    """Add the help for "@plugin help FlexoGit" here
    This should describe *how* to use this plugin."""
    threaded = True
    def __init__(self,irc):
        self.__parent = super(FlexoGit, self)
        self.__parent.__init__(irc)
        self.followers = []
        self._get_setfollowed()
        self.e = threading.Event()
        
        self.last_poll = datetime.datetime.now(pytz.utc)
        

        
    def stop_poll(self,irc,msg,args):
        irc.sendMsg(ircmsgs.privmsg(TARGET_CHANNEL, "Polling Stopped" ))
        self.e.set()
        
    gitpollstop = wrap(stop_poll)
    
    def _poll_events(self,irc):
        while not self.e.isSet():
            request_url = "https://api.github.com/users/%s/events"
            now = datetime.datetime.now(pytz.utc)
            if self.followers:
                for f in self.followers:
                    final_url = request_url % f
                    r = self.make_api_request(final_url)
                    j = json.loads(r.text)
                    j.reverse()
                    if j:
                        for i in j:
                            print self.last_poll
                            if i['type'] == "PushEvent" and dateutil.parser.parse(i['created_at']) >= self.last_poll: # commit
                                for commit in i['payload']['commits']:
                                    msg = "New Commit on %s [%s]" % (i['repo']['name'],commit['message'])
                                    irc.sendMsg(ircmsgs.privmsg(TARGET_CHANNEL, msg))
                            else: # more support later
                                continue
                    
                
            else:
                pass
            self.last_poll = now
            print "polled @ '%s', sleeping" % self.last_poll
            time.sleep(SLEEP_TIME)
            
    def start_poll(self,irc,msg,args):
        self.e.clear()
        t = threading.Thread(target=self._poll_events, kwargs={'irc':irc})
        t.start()            
        irc.sendMsg(ircmsgs.privmsg(TARGET_CHANNEL, "Polling Started" ))
    
    gitpoll = wrap(start_poll)
        
    def make_api_request(self,url,rtype="get"):
        headers = {'Content-Type' : 'application/json', "Authorization": "token %s" % GITHUB_KEY}
        if rtype == "get":
            r = requests.get(url,headers=headers)
        if rtype == "put":
            r = requests.put(url,headers=headers)
        if rtype == "post":
            r = requests.post(url,headers=headers)
        if rtype == "delete":
            r = requests.delete(url,headers=headers)
        return r
    def follow(self,irc,msg,args,text):
        request_url = "https://api.github.com/user/following/" # ex: https://api.github.com/user/following/:gmorell
        user = text.split()[0]
        final_url = request_url + user
        
        
        r = self.make_api_request(final_url, rtype="put")
        if r.status_code == 404:
            irc.sendMsg(ircmsgs.privmsg(msg.args[0], "user doesn't exist" ))
            return
        elif r.status_code == 204:
            irc.sendMsg(ircmsgs.privmsg(msg.args[0], "User Followed" ))
            self.followers.append(user)
        
    gitfollow = wrap(follow, ['text'])
        
        
    def unfollow(self,irc,msg,args,text):
        request_url = "https://api.github.com/user/following/" # ex: https://api.github.com/user/following/:gmorell
        user = text.split()[0]
        final_url = request_url + user
        
        r = self.make_api_request(final_url, rtype="delete")

        if r.status_code == 404:
            irc.sendMsg(ircmsgs.privmsg(msg.args[0], "User doesn't exist" ))
            return
        elif r.status_code == 204:
            irc.sendMsg(ircmsgs.privmsg(msg.args[0], "User UnFollowed" ))
            self.followers.remove(user)
        
    gitunfollow = wrap(unfollow, ['text'])
    
    
    def _get_setfollowed(self):
        self.followers_old = self.followers
        request_url = "https://api.github.com/user/following"
        res = self.make_api_request(request_url)
        j = json.loads(res.text)
        self.followers = []
        for i in j:
            self.followers.append(i['login'])
            
        if self.followers_old != self.followers:
            return True
            
        else:
            return False
            
    def get_setfollowed(self,irc,msg,args):
        status = self._get_setfollowed()
        if status:
            irc.sendMsg(ircmsgs.privmsg(msg.args[0], "Updated Followed"))
        else:
            irc.sendMsg(ircmsgs.privmsg(msg.args[0], "Nothing has changed"))
    
    gitupdatefollow = wrap(get_setfollowed)

Class = FlexoGit


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
