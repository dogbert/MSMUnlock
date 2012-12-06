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

import serial, string, os, getopt, sys, crctable, bootloader
from struct import pack, unpack, unpack_from
from time import sleep

def crc16(s):
	crc = 0
	for c in s:
		crc = crctable.crcTable[(crc&0xff)^ord(c)] ^ (crc >> 8)
	return crc & 0xFFFF

def readSerial(ser):
	while 1:
		if ser.inWaiting() > 0:
			dumphex(ser.read(ser.inWaiting()))
		else:
			sleep(0.2)

def sendRawCommand(ser, command, bufsize=0, timeout=1000, dwnMode=False):
	if len(command) > 0: 
		ser.write(command)
	t = 0
	r = ""
	while bufsize > 0:
		if dwnMode:
			r += ser.read(ser.inWaiting())
			if len(r) > 2:
				if (ord(r[len(r)-1]) == 0x7e) and (ord(r[len(r)-2]) != 0x7d):
					return r
				else:
					sleep(0.001)
					t += 1
		else:
			if ser.inWaiting() >= bufsize:
				return ser.read(bufsize)
			else:
				sleep(0.001)
				t += 1
		if t > timeout:
#			print "timeout (buffer size %d)" % ser.inWaiting()
			return ""

def sendCommand(ser, command, bufsize=0, timeout=1000, dwnMode=False):
	if command[0] == "\x7e":
		crc = crc16(command[1:len(command)])
	else:
		crc = crc16(command)
	command = command + pack('H', crc)

	command = command[0] + command[1:len(command)].replace('\x7D', '\x7D\x5D').replace('\x7E', '\x7D\x5E')
	command += '\x7E'
#	dumphex(command)
	r = sendRawCommand(ser, command, bufsize, timeout, dwnMode)
	if not r is None:
		i = 2
		while i < len(r):
			if (r[i] == "\x5D") and (r[i-1] == "\x7D"):
				r = r[0:i-1] + "\x7D" + r[i+1:len(r)] 
			elif (r[i] == "\x5E") and (r[i-1] == "\x7D"):
				r = r[0:i-1] + "\x7E" + r[i+1:len(r)]
			i += 1
	else:
		r = ""
	return r
	
def dumphex(s):
	i = -1
	if s is None:
		return
	print "dumping %d bytes..." % len(s)
	for i in xrange(0,len(s)/16+1):
		o = '%08x  ' % (i*16)
		for j in range(0, 16):
			if len(s) > i*16+j:
				o += '%02x ' % ord(s[i*16+j])
			else:
				o += '	 '
		o += ' |'
		for j in range(0, 16):
			if len(s) > i*16+j:
				if (ord(s[i*16+j]) > 0x1F) and (ord(s[i*16+j]) < 0x7F):
					o += s[i*16+j]
				else:
					o += '.'
			else:
				break
		o += '|'
		print o 

def getInfo(ser):
	return sendCommand(ser, "\x00", 58)

def enableDwnMode(ser):
	command = '\x7e\x3a'
	r = sendCommand(ser, command, 4, dwnMode=True)
	r = ""
	ser.close()
#       sleep(0.2)
        ser.open()
	while len(r) == 0:
		command = '\x7e\x0c'
		r = sendCommand(ser, command, 12, dwnMode=True, timeout=2000)
#		dumphex(r)
		if len(r) == 0:
			ser.close()
			sleep(0.05)
			ser.open()
	command = '\x7e\x07'
	r = sendCommand(ser, command, 11, dwnMode=True, timeout=10000)
	print "Download mode activated"
	
def dwnResetPhone(ser):
	return sendCommand(ser, '\x7e\x0a', 5, dwnMode=True)

def dwnWriteMem(ser, buffer, address, size):
	# little endian !
	command = "\x7e\x0f" + pack('>I', address) + pack('>H', size) + buffer
	return sendCommand(ser, command, 5, dwnMode=True)

def dwnExecute(ser, address):
	command = '\x7e\x05' + pack('>I', address)
	r = sendCommand(ser, command, timeout=5, dwnMode=True)
	
def sendBootloader(ser, bootloader):
	enableDwnMode(ser)
	sleep(0.2)

	startAddress = 0x800000
	bufferSize   = 0x3f9
	address      = startAddress

	statinfo = os.stat(bootloader)
	bootloaderSize = statinfo.st_size
	written = 0

	f = open(bootloader, "rb")
	while 1:
		buffer = f.read(bufferSize)
		r = dwnWriteMem(ser, buffer, address, len(buffer))
		if ord(r[1]) != 0x02:
			print "Error while sending bootloader: write memory failed at %08x" % address
			return False
		written += len(buffer)
		print "\r %d %% complete" % (written / bootloaderSize * 100.0)
		sleep(0.1)
		address += bufferSize
		if len(buffer) < bufferSize:
			break
	print "Executing bootloader..."
	dwnExecute(ser, startAddress)
	return True
	
def testBootloader(ser):
	r = ''
	while len(r) < 500:
		sleep(0.5)
		r = sendCommand(ser, '\x7e\x01' + "QCOM fast download protocol host" + "\x03\x03\x09", 500, timeout=10000, dwnMode=True)
	return r[0x2D:r.find('\x00', 0x2D)]

def readUnlockCode(ser):
	r = sendCommand(ser, '\x05\x00\x00\x00\x00\x00', 500, timeout=10000, dwnMode=True)
	return r[1:9]

def getATAnswer(ser):
	s = ''
	while 1:
		s += ser.read()
		if s[len(s)-4:len(s)] == 'OK\r\n':
			break
		sleep(0.05)
		if s.find("ERROR") != -1:
			return s
	return s.splitlines()[2]

def checkLockStatus(appPort):
	ser = serial.Serial(appPort, 115200, timeout=2)
	ser.write('ATE\r\n')
        getATAnswer(ser)
	
	locked = False
	locks = [ 'PN', 'PU', 'PC', 'PP', 'PF' ]
	for i in locks:
		ser.write('AT+CLCK="%s",2\r\n' % i)
		response = getATAnswer(ser)
                if response.find('+CLCK:') != -1:
                        if (response.split('+CLCK: ')[1][0] == '1'):
                                print "Lock %s set" % i
        			locked = True
        		else:
                                print "Lock %s is not set" % i
	ser.close()
	return locked

def checkSoftwareVersion(appPort):
	ser = serial.Serial(appPort, 115200, timeout=2)
	ser.write('AT+GMR\r\n')
	response = getATAnswer(ser)
	ser.close()
	return response

def unlockModem(appPort, unlockCode):
	ser = serial.Serial(appPort, 115200, timeout=5)
	locks = [ 'PN', 'PU', 'PC', 'PP', 'PF' ]
	result = False
	for i in locks:
            	ser.write('AT+CLCK="%s",2\r\n' % i)
            	response = getATAnswer(ser)
                if response.find('+CLCK:') != -1:
                        if (response.split('+CLCK: ')[1][0] == '1'):
                                ser.write('AT+CLCK="%s",0,"%08d"\r\n' % (i, unlockCode))
                                response = getATAnswer(ser)
                		if (response.find('OK') != -1):
                                        print "Disabled %s lock" % i
                                	result = True
	ser.close()
	return result

def checkAppPort(port):
	try:
		ser = serial.Serial(port, 115200, timeout=2)
		ser.write('\r\nAT+CGSN\r\n')
		response = ser.read(13+28)
		result = (response.find("DR") != -1)
		ser.close()
	except serial.SerialException:
		result = False
	return result

def checkDiagPort(port):
	try:
		ser = serial.Serial(port, 115200, timeout=0)
		response = getInfo(ser)
		result = (response.find("FUJI_NAN") != -1)
		ser.close()
	except serial.SerialException:
		result = False
	return result

def findSerialPorts(pattern):
	appPort = None
	diagPort = None
	for i in range(0, 255):
		port = pattern % i
		if (appPort != None) and (diagPort != None):
			break
		if appPort == None:
			if checkAppPort(port):
				appPort = port
				continue
		if diagPort == None:
			if checkDiagPort(port):
				diagPort = port
	return (appPort, diagPort)

def info():
	print "msm_unlock.py v1.6"
	print "Copyright (c) 2009 dogbert <dogber1@gmail.com>, http://dogber1.blogspot.com"
	print "This scripts reads the unlock code of Option 3G modems (Icon 225)."
	print ""

def usage():
	print "Options: -a, --appPort=	 name of the serial application port (e.g. COM4)"
	print "		-d, --diagPort=  name of the serial diagnostics port (e.g. COM5)."
	print ""
	print "Example: msm_unlock.py -a COM3 -d COM4"

		
def main():
	info()
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hd:a:", ["help", "appPort=", "diagPort="])
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)

	diagPort = None
	appPort  = None
	baud	 = 115200
	Init	 = True
	didProbe = False

	for o, a in opts:
		if o in ("-d", "--diagPort"):
			diagPort = a
		if o in ("-a", "--appPort"):
			appPort = a
		elif o in ("-h", "--help"):
			usage()
			sys.exit()

	print "Checking bootloader..."
	if not bootloader.getBootloader():
		print "ERROR: The bootloader has not been found. Please place a correct file 'Superfire.exe' in this folder."
		if (os.name == 'nt'):
			raw_input()
		sys.exit(-1)
	print "Bootloader OK, proceeding..."
	print ""

	if (os.name == 'posix') and ((appPort == None) or (diagPort == None)):
		print "Searching for serial ports..."
		(appPort, diagPort) = findSerialPorts("/dev/ttyHS%d")
		didProbe = True
	if (os.name == 'nt') and ((appPort == None) or (diagPort == None)):
		print "Searching for serial ports..."
		(appPort, diagPort) = findSerialPorts("COM%d")
		didProbe = True

	if appPort == None:
		print "Failed to find the application port. Please shutdown the device software."
		sys.exit(-1)

	if diagPort == None:
		print "Failed to find the diagnostics port. Please shutdown the device software."
		sys.exit(-1)

	print "Application serial port: %s" % appPort
	print "Diagnostics serial port: %s" % diagPort
	print ""
	if didProbe == True:
		print "Launch again with:\n\t%s --appPort %s --diagPort %s" % (sys.argv[0], appPort, diagPort)
		sys.exit(0)

	print "Checking software version..."
	checkSoftwareVersion(appPort)
	
	print "Checking netlock status..."
	if not checkLockStatus(appPort):
                print "Status of the locks unknown/opened. Proceed? (Y/N)"
                if raw_input().lower() != 'y':
        		sys.exit(0)
	else:
                print "Netlock active"
	print ""

	print "Opening diagnostics port..."
	ser = serial.Serial(diagPort, baud, timeout=0)
	getInfo(ser)
	print "Sending bootloader..."
	if not sendBootloader(ser, 'msm6280-patched.bin'):
		sys.exit(-1)
	print ""

	print "Getting flash type..."
	s = testBootloader(ser)
	print "Flash type: %s" % s

	print "Reading unlock code..."
	unlockCode = readUnlockCode(ser)
	print "Unlock code: %s" % unlockCode
	ser.close()
	print ""
	print "Write down the code, close this window and wait 30 seconds. Then apply the unlock code using msm_apply.py..."
	raw_input()
	print "done."

if __name__ == "__main__":
	main()

