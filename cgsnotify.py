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
			"title" : "CGSnotify - " + title,
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
	if len(inlist) == 1:
		outstring += inlist[0]
	if len(inlist) == 2:
		outstring += (inlist[0] + " and " + inlist[1])
	if len(inlist) == 3:
		outstring += (inlist[0] + ", " + inlist[1] + " and " + inlist[2])
	if len(inlist) >= 4:
		for x in (range(len(inlist) - 2)):
			outstring += inlist[x] + ", "
		outstring += (inlist[len(inlist) - 2] + " and " + inlist[len(inlist) - 1])
	return outstring
		
if __name__ == '__main__':
	logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s',datefmt='%d/%m/%y %H:%M:%S',level=logging.DEBUG)
		
	s=mice.m.getServer(1)
	
	while True:
		try:
			currentusers = listLoggedInUsers()
			time.sleep(5)
			if len(s.getUsers().keys()) > len(currentusers):
				newusers = list(set(listLoggedInUsers()) - set(currentusers))
				logging.info('%s logged in!', prettyPrintList(newusers))
				currentusers = listLoggedInUsers()
				for x in users.keys():
					if x in currentusers:
						logging.info("%s is logged in already, skipping", x)
					else:
						logging.info("Notifying %s", x)
						notify(users[x], (prettyPrintList(newusers) + " logged in"), prettyPrintList(currentusers) + " are online.")
						time.sleep(1) #be nice to the api
		except KeyboardInterrupt:
			logging.info("Caught SIGINT, exiting")
			sys.exit()