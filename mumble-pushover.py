#!/usr/bin/env python

import yaml
import mice
import httplib, urllib
import argparse, logging
import time, datetime
import sys
import random
import operator

class ServerCallbackI(mice.Murmur.ServerCallback):
    """
    Callback interface class to pass to the mumble server
    """
    def __init__(self, server, adapter):
        self.server = server

    def userConnected(self, u, current=None):
        currentusers = list_logged_in_users()
        logging.info("{} connected".format(u.name))
        # Notify if 1) we have no last logout data for the user or 2) the user logged out less than quietloginoffset seconds ago
        if u.name not in lastlogouts.keys() or datetime.datetime.now() > (lastlogouts[u.name] + datetime.timedelta(seconds=config['quietloginoffset'])):
            isare = "is" if len(currentusers) == 1 else "are"
            notify_users("{} logged in".format(u.name), "{} {} online.".format(list_to_string(currentusers), isare), currentusers=currentusers)
        else:
            logging.info("User logged out and in again within {} seconds. Not notifying.".format(str(config['quietloginoffset'])))

    def userDisconnected(self, u, current=None):
        logging.info(u.name + " disconnected")
        lastlogouts[u.name] = datetime.datetime.now()

    def userTextMessage(self, u, msg, current=None):
        if msg.text[0] == config['commandprefix']:
            parse_text_command(u, msg.text)
            logging.info("[CMD:] " + u.name + ": " + msg.text)
        else:
            logging.info("[CHAT] " + u.name + ": " + msg.text)

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
    logging.info('Notifying {}'.format(userkey))
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
        urllib.urlencode({
            "token": config['apptoken'],
            "user": userkey,
            "message": message,
            "title" : config['name'] + " - " + title,
        }), { "Content-type": "application/x-www-form-urlencoded" }
    )
    conn.getresponse()

def list_logged_in_users():
    users = []
#    for x in s.getUsers(): # x is key for dictionary s.getUsers(). 
#        users.append(s.getUsers()[x].name)
    for userobj in s.getUsers().values: # userobj is value for dictionary s.getUsers(). 
        users.append(userobj.name)
    return users

def notify_users(title, message, currentusers=[]):
    """notifies users via pushover. If currentusers (list of usernames) is specified,
    these users are not notified"""
    if args.test_mode:
        send_pushover_notification(config['pushoverusers'][args.test_mode], "[TEST] " + title, message)
    else:
        for u in config['pushoverusers'].keys(): # list of names for those with pushover
            if u not in currentusers:
                send_pushover_notification(config['pushoverusers'][u], title, message)
                time.sleep(0.5) # be nice to the api

def list_to_string(inputlist):
    """
    Format a list to a string with grammar
    Inputlist[n] (where n>3) returns "inputlist[0], inputlist[1], ... and inputlist[n]"
    """
    outstring = ""
    numusers = len(inputlist)
    if numusers == 1: # foo
        outstring += inputlist[0]
    if numusers == 2: # foo and bar
        outstring += (inputlist[0] + " and " + inputlist[1])
    if numusers >= 3: # foo, bar and baz
        for x in range(numusers-2):
            outstring += inputlist[x] + ", "
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

def parse_text_command(user, command):
    command = command[1:]
    if command == 'hello':
        s.sendMessageChannel(0, True, "Hello")
    elif command == 'stillhere' or command == 'poke':
        isare = "is" if len(list_logged_in_users()) == 1 else "are"
        notify_users('Poke!',
                     list_to_string(list_logged_in_users()) + ' '+ isare +' still online',
                     currentusers=list_logged_in_users()
                     )
        s.sendMessage(user.session,"Poke sent!")
    elif command == 'roulette':
        kicksession = random.choice(s.getUsers().keys())
        s.kickUser(kicksession, 'You lose! >:D')
    elif command == 'history' or command == 'hist':
        cmdHist(user)

def cmdHist(user):
    try:
        msg_list = ["<br>User  -  Last Logged Out"] #Start everything on line below [server]
        # Iterate through list of ordered tuple pairs (of user and last logout) sorted by most recent logout.
        for user_name,ll in sorted(lastlogouts.items(), key=operator.itemgetter(1), reverse=true):
            content = "{0} - {1:%H:%M  %d/%m/%y}".format(user_name,ll)
            msg_list.append(content)
        msg = "<br>".join(msg_list)
        s.sendMessage(user.session,msg)
    except Exception as e: # catches all errors ?
        s.sendMessageChannel(0, True, "Error: {}".format(e))


if __name__ == "__main__":
    lastlogouts = {}

    with open('config.yaml', 'r') as f:
        config = yaml.load(f)

    argparser = argparse.ArgumentParser(description="Mumble-pushover notifications script.")
    argparser.add_argument("-t", "--test-mode", help = "Only sends notifications to the given username's key.")
    #argparser.add_argument("-v", "--verbose", action="count", default = 0, help = "Display info as well as errors")
    args = argparser.parse_args()

    logging.basicConfig(format="%(asctime)s [%(levelname)s]: %(message)s",datefmt="%d/%m/%y %H:%M:%S",level=logging.DEBUG)

    mice.ice.getImplicitContext().put("secret", config['icesecret'])
    s=mice.m.getServer(1)

    initialise_callbacks()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Caught SIGINT, exiting")
            sys.exit()
