#!/usr/bin/python

import base64
import datetime
import libxml2
import optparse
import re
import subprocess
import sys

services = []
available_encodings = ['base64', 'plain',]


parser = optparse.OptionParser()

parser.add_option('-c', '', dest='cfgfile', help='Config file')
parser.add_option('-o', '', dest='xmlfile', help='Output file')
parser.add_option('-e', '', dest='encoding', help='Encoding (ATM only "base64")')
parser.add_option('-v', '', action='count', dest='verb', help='Verbose output')

parser.set_defaults(cfgfile='nagixsca-client.conf')
parser.set_defaults(xmlfile='nagixsca.xml')
parser.set_defaults(encoding='base64')
parser.set_defaults(verb=0)

(options, args) = parser.parse_args()

if options.encoding not in available_encodings:
	print 'Wrong encoding method "%s"!' % options.encoding
	print 'Could be one of: %s' % ', '.join(available_encodings)
	sys.exit(127)

##############################################################################

def encode(data):
	if options.encoding == 'plain':
		return data
	else:
		return base64.b64encode(data)

##############################################################################

try:
	file = open(options.cfgfile)
except IOError:
	print 'Config file "%s" does not exist!' % options.cfgfile
	sys.exit(127)

for line in file:
	result = re.match('^command\[([-_a-zA-Z0-9]+)\]=(.*)$', line)
	if result:
		services.append([result.group(1), result.group(2)])

if options.verb >= 3:
	print 'Python list of services:'
	print services

xmldoc = libxml2.newDoc('1.0')
xmlroot = xmldoc.newChild(None, 'nagixsca', None)
xmltimestamp = xmlroot.newChild(None, 'timestamp', datetime.datetime.now().strftime('%s'))

for service, cmdline in services:

	cmd = subprocess.Popen(cmdline.split(' '), stdout=subprocess.PIPE)
	output = cmd.communicate()[0].rstrip()
	retcode = cmd.returncode

	if options.verb >= 1:
		print "\nCommand line: %s\n+--> Output: %s\n+--> Returncode: %s" % (cmdline, output.rstrip(), retcode)

	xmlchild = xmlroot.newChild(None, 'service', None)
	xmlname = xmlchild.newChild(None, 'name', encode(service))
	xmlname.setProp('encoding', options.encoding)
	xmlreturncode = xmlchild.newChild(None, 'returncode', str(retcode))
	xmloutput = xmlchild.newChild(None, 'output', encode(output))
	xmloutput.setProp('encoding', options.encoding)

xmldoc.saveFile(options.xmlfile)
