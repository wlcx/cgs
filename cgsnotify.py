#!/usr/bin/env python

import mice
import httplib, urllib
import argparse, logging
import time, datetime
import sys


try:
    from cgsnotify_config import users, apptoken, icesecret
except ImportError:
    logging.ERROR("No config file found")
    sys.exit()

#Server callback class
class ServerCallbackI(mice.Murmur.ServerCallback):
    def __init__(self, server, adapter):
        self.server = server
    
    def userConnected(self, u, current=None):
        logging.info(u.name + " connected")
        currentusers = listLoggedInUsers()
        if u.name not in userlogininfo:
            userlogininfo[u.name] = {'lastlogout' : 0, 'lastlogin' : 0,}
        # prevent notifications being sent if the user logs out and in again within quietloginoffset seconds
        if time.mktime(datetime.datetime.now().timetuple()) > (userlogininfo[u.name]["lastlogout"] + quietloginoffset):
            isare = "is" if len(currentusers) == 1 else "are"
            if args.test_mode:
                logging.info("Running in testing mode")
                sendPushoverNotification(users[args.test_mode], ("TESTING: " + u.name + " logged in"), 
                formatListToString(currentusers) + " " + isare + " online.")
            else:
                for x in users.keys(): # list of names for those with pushover
                    if x in currentusers:
                        logging.info("%s is logged in already, skipping", x)
                    else:
                        logging.info("Notifying %s", x)
                        sendPushoverNotification(users[x],(u.name + " logged in"), 
                        (formatListToString(currentusers) + " " + isare + " online."))
                        time.sleep(0.5) # be nice to the api
        else:
            logging.info("User logged out and in again within " + str(quietloginoffset) + " seconds. Not notifying.")
        userlogininfo[u.name]["lastlogin"] = time.mktime(datetime.datetime.now().timetuple())
    def userDisconnected(self, u, current=None):
        logging.info(u.name + " disconnected")
        if u.name not in userlogininfo:
            userlogininfo[u.name] = {'lastlogout' : 0, 'lastlogin' : 0,}
        userlogininfo[u.name]["lastlogout"] = time.mktime(datetime.datetime.now().timetuple())
    
    def userTextMessage(self, p, msg, current=None):
        print "[CHAT] " + p.name + ": " + msg.text
    
    def userStateChanged(self, u, current=None):
        pass
    
    def channelCreated(self, c, current=None):
        pass

    def channelRemoved(self, c, current=None):
        pass
    
    def channelStateChanged(self, c, current=None):
        pass

# Post notification to pushover servers
def sendPushoverNotification(userkey, title, message):
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
    for x in s.getUsers(): # x is key for dictionary s.getUsers()
        users.append(s.getUsers()[x].name)
    # WIP: Possible Alternative
    # WIP: users = [s.getUsers()...
    return users

# Format a list with nice grammar (so ["foo", "bar", "baz"] returns "foo, bar and baz")
def formatListToString(inputlist):
    outstring = ""
    numusers=len(inputlist)
    if numusers == 1: # foo
        outstring += inputlist[0]
    if numusers == 2: # foo and bar
        outstring += (inputlist[0] + " and " + inputlist[1])
    if numusers >= 3: # foo, bar and baz
        for x in range(numusers-2):
            outstring += inputlist[x] + ", "
        # exploits wraparound indexing, s[-1] refers to last item
        outstring += (inputlist[-2] + " and " + inputlist[-1])
    return outstring

# initialise callback interface and server object
mice.ice.getImplicitContext().put("secret", icesecret)
adapter = mice.ice.createObjectAdapterWithEndpoints("Callback.Client", "tcp -h 127.0.0.1")
adapter.activate()
s=mice.m.getServer(1)
cb=mice.Murmur.ServerCallbackPrx.uncheckedCast(adapter.addWithUUID(ServerCallbackI(s, adapter)))
s.addCallback(cb)

userlogininfo = {}
quietloginoffset = 60 # if the user logs in less than this many seconds after logging out then noone is notified

if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser(description="CGS Mumble server notifications script.")
    argparser.add_argument("-t", "--test-mode", help = "Only sends notifications to the given username's key.")
    #argparser.add_argument("-v", "--verbose", action="count", default = 0, help = "Display info as well as errors")
    args = argparser.parse_args()
 
    logging.basicConfig(format="%(asctime)s [%(levelname)s]: %(message)s",datefmt="%d/%m/%y %H:%M:%S",level=logging.DEBUG)
    
    while True:
        try:               
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Caught SIGINT, exiting")
            sys.exit()
