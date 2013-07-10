#!/usr/bin/env python

import mice
import httplib, urllib
import argparse, logging
import time
import sys


try:
    from cgsnotify_config import users, apptoken
except ImportError:
    logging.ERROR("No config file found")
    sys.exit()

#Server callback class
class ServerCallbackI(Murmur.ServerCallback):
    def __init__(self, server, adapter):
        self.server = server
    
    def userConnected(self, u):
        logging.info(u.name + " connected")
    
    def userDisconnected(self, u):
        logging.info(u.name + " disconnected")
    
    def userTextMessage(self, p, msg, current=None):
        print "userTextMessage"
        print self.server
        print p
        print msg
    
    def userStateChanged(self, u):
        pass
    
    def channelCreated(self, c):
        pass

    def channelRemoved(self, c):
        pass
    
    def channelStateChanged(self, c):
        pass

# Post notification to pushover servers
def notify(userkey, title, message):
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
        urllib.urlencode({
            "token": apptoken,
            "user": userkey,
            "message": message,
            "title" : "CGSNotify - " + title,
        }), { "Content-type": "application/x-www-form-urlencoded" }
    )
    conn.getresponse()

def listLoggedInUsers():
    users = []
    for x in s.getUsers(): # x is key for dictioary s.getUsers()
        users.append(s.getUsers()[x].name)
    # WIP: Possible Alternative
    # WIP: users = [s.getUsers()...
    return users

# Format a list with nice grammar (so ['foo', 'bar', 'baz'] returns 'foo, bar and baz')
def prettyPrintList(inlist):
    outstring = ""
    numUsers=len(inlist)
    if numUsers == 1: # foo
        outstring += inlist[0]
    if numUsers == 2: # foo and bar
        outstring += (inlist[0] + " and " + inlist[1])
    if numUsers >= 3: # foo, bar and baz
        for x in range(numUsers-2):
            outstring += inlist[x] + ", "
        # exploits wraparound indexing, s[-1] refers to last item
        outstring += (inlist[-2] + " and " + inlist[-1])
    return outstring

isorare=["is","are"]

if __name__ == '__main__':
    
    argparser = argparse.ArgumentParser(description='CGS Mumble server notifications script.')
    argparser.add_argument('-t', '--test-mode', help = "Only sends notifications to the given username's key.")
    #argparser.add_argument('-v', '--verbose', action='count', default = 0, help = "Display info as well as errors")
    args = argparser.parse_args()
 
    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',datefmt='%d/%m/%y %H:%M:%S',level=logging.DEBUG)
    
    # retrieve 1st virtual server object
    s = mice.m.getServer(1)
    
    while True:
        try:
            oldusers = listLoggedInUsers()
            time.sleep(5)
            currentusers = listLoggedInUsers()

            # Will show new users, so if oldusers = ["a","b","c","d"],
            # currentusers = ["a","e","f"], newusers = ["e","f"]
            newusers = list(set(currentusers) - set(oldusers))
            if len(newusers) > 0:
                logging.info('%s logged in!', prettyPrintList(newusers))

                # Only works for non-zero users (but in if so its fine)
                isare = isorare[bool(len(currentusers) - 1)]
                # Alternative:
                # if len(currentusers) == 1: isare = 'is'
                # else: isare = 'are'
                
                # Output below
                if args.test_mode:
                    logging.info('Running in testing mode')
                    notify(users[args.test_mode], ("TESTING:" + prettyPrintList(newusers) + " logged in"), 
                                   prettyPrintList(currentusers) + " " + isare + " online.")
                else:
                    for x in users.keys(): # list of names for those with pushover
                        if x in currentusers:
                            logging.info("%s is logged in already, skipping", x)
                        else:
                            logging.info("Notifying %s", x)
                            notify(users[x],(prettyPrintList(newusers) + " logged in"), 
                            (prettyPrintList(currentusers) + " " + isare + " online."))
                            time.sleep(0.5) # be nice to the api
        except KeyboardInterrupt:
            logging.info("Caught SIGINT, exiting")
            sys.exit()
