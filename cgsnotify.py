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
    for x in s.getUsers():
        users.append(s.getUsers()[x].name)
    return users
    
def prettyPrintList(inlist):
    outstring = ""
    numUsers=len(inlist)
    if numUsers == 1:
        outstring += inlist[0]
    if numUsers == 2:
        outstring += (inlist[0] + " and " + inlist[1])
    if numUsers >= 3:
        for x in range(numUsers-2):
            outstring += inlist[x] + ", "
        outstring += (inlist[-2] + " and " + inlist[-1])
    return outstring

if __name__ == '__main__':
    
    argparser = argparse.ArgumentParser(description='CGS Mumble server notifications script.')
    argparser.add_argument('-t', '--test-mode', help = "Only sends notifications to the given API key.")
    #argparser.add_argument('-v', '--verbose', action='count', default = 0, help = "Display info as well as errors")
    args = argparser.parse_args()
 
    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',datefmt='%d/%m/%y %H:%M:%S',level=logging.DEBUG)
    
    s = mice.m.getServer(1)
    
    while True:
        try:
            currentusers = listLoggedInUsers()
            time.sleep(5)
            if len(s.getUsers().keys()) > len(currentusers): #user logs in
                newusers = list(set(listLoggedInUsers()) - set(currentusers)) 
                logging.info('%s logged in!', prettyPrintList(newusers))
                currentusers = listLoggedInUsers()
                if len(currentusers) == 1:
                    isare = 'is'
                else: isare = 'are'
                if args.test_mode:
                    logging.info('Running in testing mode')
                    notify(args.test_mode, ("TESTING:" + prettyPrintList(newusers) + " logged in"), 
                                   prettyPrintList(currentusers) + " " + isare + " online.")
                else:
                    for x in users.keys():
                        if x in currentusers:
                            logging.info("%s is logged in already, skipping", x)
                        else:
                            logging.info("Notifying %s", x)
                            notify(users[x], (prettyPrintList(newusers) + " logged in"), 
                                   prettyPrintList(currentusers) + " " + isare + " online.")
                            time.sleep(1) #be nice to the api
        except KeyboardInterrupt:
            logging.info("Caught SIGINT, exiting")
            sys.exit()
