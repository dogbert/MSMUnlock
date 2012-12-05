#!/usr/bin/env python
#
# Copyright 2009: dogbert <dogber1@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

import getopt, sys, os, msm_unlock

def info():
	print "msm_apply.py v1.6"
	print "Copyright (c) 2009 dogbert <dogber1@gmail.com>, http://dogber1.blogspot.com"
	print "This scripts applies the unlock code of Option 3G modems (Icon 225)."
	print ""

def usage():
	print "Options: -a, --appPort=  name of the serial application port (e.g. COM4)"
	print "		-c, --code=     unlock code"
	print "Example: msm_apply.py -a COM3 -c 12345678"

def main():
	info()
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hc:a:", ["help", "code=", "diagPort="])
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)

	appPort = None
	code	= ''
	baud	= 115200
	Init	= True

	for o, a in opts:
		if o in ("-c", "--code"):
			code = int(a)
		if o in ("-a", "--appPort"):
			appPort = a
		elif o in ("-h", "--help"):
			usage()
			sys.exit()

	if (os.name == 'nt') and (appPort == None):
		print "Searching for serial ports..."
		appPort = msm_unlock.findSerialPorts()[0]

	if appPort == None:
		print "Failed to find the application port. Please shutdown the device software."
		sys.exit(-1)

	print "Application serial port: %s" % appPort
	print ""

	if code == '':
		print "Please enter the unlock code:"
		code = int(raw_input())
	
	print ""
	print "Unlocking modem..."
	if msm_unlock.unlockModem(appPort, code):
		print "Unlock successful."
	else:
		print "ERROR: Unlock unsuccessful"
	print ""
	print "done."
	raw_input()

if __name__ == "__main__":
	main()
