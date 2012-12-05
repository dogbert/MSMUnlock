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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307	USA
#

import hashlib, os

def sha1sum(filename):
	return hashlib.sha1(open(filename,'rb').read()).hexdigest()

def checkUnpatchedBootloader(filename):
	return (sha1sum(filename) in ("cbcef9e634999b6b778a04b45b178fec0ea709c9", "e6a537b16f35bf7e4cc207fb157dc5eef73ab3ee", "a2fd786181c3f75dd88395c0badc01e0acd6e086", "53a69d0e0aa8479366bc2378b67bbdc15b63c42a"))

def checkPatchedBootloader(filename):
	return (sha1sum(filename) == "4252e74d48fe60d1173ecd898e2d3cdfd2a96c53")

def extractBootloader(inFile, outFile, offset):
	f = open(inFile, 'rb')
	f.seek(offset)
	intelHex = f.read(0x18c97)
	f.close()
	data = ''
	for s in intelHex.splitlines():
		if s[0] != ':':
			continue
		if int(s[1]+s[2],16) < 5:
			continue
		for i in range(0, (len(s)-11)/2):
			data += chr(int(s[i*2+9]+s[i*2+10],16))
	f = open(outFile, 'wb')
	f.write(data)
	f.close()
	return

def patchBootloader(inFile, outFile, patchFile):
	inF = open(inFile, 'rb')
	orig = inF.read()
	inF.close()

	paF = open(patchFile, 'rb')
	patch = paF.read()
	paF.close()
 
	patchedLoader = orig[0:0x89df] + '\x00' + patch[0x9e0:0x9e0+0x110]
	patchedLoader += orig[0x89e0+0x110:0x8b14] + '\xe1\x89' + orig[0x8b16:len(orig)]

	outF = open(outFile, 'wb')
	outF.write(patchedLoader)
	outF.close()

	return

def getBootloader():
	if not os.path.exists('msm6280.bin'):
		if not os.path.exists('Superfire.exe'):
			return False
		sum = sha1sum('Superfire.exe')

		if sum == 'd584e3fb5bd786bba7d3bcf3391523d88fd6128e':
			extractBootloader('Superfire.exe', 'msm6280.bin', 0x9c5cc)
		elif sum in ('534ecd8f693cd4d9a89c31d00d17885d3abcb26a', '4ecda86f0816f2641fbfa19c00dd0034108b86b7', 'fef058fbcedcbfb3a77f99812c14815d6b3abd83', '68fd7d98360f2ac2c09a30e6b9d2af9eb6b314b9', 'ff79c921fcd360c3674d57bf07c948b4d528897d'):
			extractBootloader('Superfire.exe', 'msm6280.bin', 0x9c44c)
		else:
			return False
	if not os.path.exists('msm6280-patched.bin'):
		if not checkUnpatchedBootloader('msm6280.bin'):
			return False
		patchBootloader('msm6280.bin', 'msm6280-patched.bin', os.path.join('patch','patch.bin'))
	return checkPatchedBootloader('msm6280-patched.bin')
