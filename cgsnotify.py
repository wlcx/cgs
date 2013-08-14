#!/usr/bin/env python

import mice
import httplib, urllib
import argparse, logging
import time, datetime
import sys

userlogininfo = {}
quietloginoffset = 60 # if the user logs in less than this many seconds after logging out then noone is notified

try:
    from cgsnotify_config import pushoverusers, apptoken, icesecret
except ImportError:
    logging.error("No config file found")
    sys.exit()

#Server callback class
class ServerCallbackI(mice.Murmur.ServerCallback):
    """
    Callback interface class to pass to the mumble server
    """
    def __init__(self, server, adapter):
        self.server = server
    
    def userConnected(self, u, current=None):
        logging.info(u.name + " connected")
        currentusers = list_logged_in_users()
        if u.name not in userlogininfo:
            userlogininfo[u.name] = {'lastlogout' : 0, 'lastlogin' : 0,}
        # prevent notifications being sent if the user logs out and in again within quietloginoffset seconds
        if time.mktime(datetime.datetime.now().timetuple()) > (userlogininfo[u.name]["lastlogout"] + quietloginoffset):
            isare = "is" if len(currentusers) == 1 else "are"
            if args.test_mode:
                logging.info("Testing mode: notifying " + args.test_mode)
                send_pushover_notification(pushoverusers[args.test_mode], ("TESTING: " + u.name + " logged in"), 
                list_to_string(currentusers) + " " + isare + " online.")
            else:
                for x in pushoverusers.keys(): # list of names for those with pushover
                    if x in currentusers:
                        logging.info("%s is logged in already, skipping", x)
                    else:
                        logging.info("Notifying %s", x)
                        send_pushover_notification(pushoverusers[x],(u.name + " logged in"), 
                        (list_to_string(currentusers) + " " + isare + " online."))
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
        logging.info("[CHAT] " + p.name + ": " + msg.text)
    
    def userStateChanged(self, u, current=None):
        pass
    
    def channelCreated(self, c, current=None):
        pass

    def channelRemoved(self, c, current=None):
        pass
    
    def channelStateChanged(self, c, current=None):
        pass

# Post notification to pushover servers
def send_pushover_notification(userkey, title, message):
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

def list_logged_in_users():
    users = []
    for x in s.getUsers(): # x is key for dictionary s.getUsers()
        users.append(s.getUsers()[x].name)
    return users

def list_to_string(inputlist):
    """
    Format a list to a string with grammar 
    Inputlist[n] (where n>3) returns "inputlist[0], inputlist[1], ... and inputlist[n]"
    """
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

def initialise_callbacks():
    """
    Setup the mumble server callback interface and register it with the server
    """
    adapter = mice.ice.createObjectAdapterWithEndpoints("Callback.Client", "tcp -h 127.0.0.1")
    adapter.activate()
    cb=mice.Murmur.ServerCallbackPrx.uncheckedCast(adapter.addWithUUID(ServerCallbackI(s, adapter)))
    s.addCallback(cb)

# initialise server object
mice.ice.getImplicitContext().put("secret", icesecret)
s=mice.m.getServer(1)


if __name__ == "__main__":
    
    argparser = argparse.ArgumentParser(description="CGS Mumble server notifications script.")
    argparser.add_argument("-t", "--test-mode", help = "Only sends notifications to the given username's key.")
    #argparser.add_argument("-v", "--verbose", action="count", default = 0, help = "Display info as well as errors")
    args = argparser.parse_args()
 
    logging.basicConfig(format="%(asctime)s [%(levelname)s]: %(message)s",datefmt="%d/%m/%y %H:%M:%S",level=logging.DEBUG)
    
    initialise_callbacks()

    while True:
        try:               
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Caught SIGINT, exiting")
            sys.exit()
