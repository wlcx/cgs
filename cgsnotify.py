#!/usr/bin/env python

import mice
import httplib, urllib

apptoken = "your pushover app token here"

s=mice.m.getServer(1)

if len(s.getUsers().keys()) == 1:
	print "1 user online"

else:
	print str(len(s.getUsers().keys())) + " users online"

def notify(userkey):
	conn = httplib.HTTPSConnection("api.pushover.net:443")
	conn.request("POST", "/1/messages.json",
		urllib.urlencode({
			"token": apptoken,
			"user": userkey,
			"message": "Imma let you test",
		}), { "Content-type": "application/x-www-form-urlencoded" }
	)
	conn.getresponse()
