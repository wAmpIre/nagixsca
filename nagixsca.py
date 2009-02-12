#!/usr/bin/python

import base64
import datetime
import libxml2
import optparse
import sys

parser = optparse.OptionParser()

parser.add_option('-u', '', dest='url', help='URL of status file (nagixsca.xml)')
parser.add_option('-f', '', dest='file', help='(Path and) file name of status file')
parser.add_option('-n', '', dest='name', help='HostName in Nagios')
parser.add_option('-p', '', dest='pipe', help='Full path to nagios.cmd')
parser.add_option('-v', '', action='count', dest='verb', help='Verbose output')

parser.set_defaults(url=None)
parser.set_defaults(file='nagixsca.xml')
parser.set_defaults(name=None)
parser.set_defaults(pipe=None)
parser.set_defaults(verb=0)

(options, args) = parser.parse_args()

if options.name==None:
	print "Need a hostname for Nagios!"
	sys.exit(127)

if options.pipe==None:
	print "Need full path to the nagios.cmd pipe!"
	sys.exit(127)

##############################################################################

now = datetime.datetime.now().strftime('%s')
commands =""

if options.url != None:
	import urllib2

	response = urllib2.urlopen(options.url)
	doc = libxml2.parseDoc(response.read())
	response.close()
else:
	doc = libxml2.parseFile(options.file)

ctxt = doc.xpathNewContext()
services = ctxt.xpathEval("//service")

for service in services:
	srvdescr = base64.b64decode(service.xpathEval('name')[0].get_content())
	retcode  = service.xpathEval('returncode')[0].get_content()
	output   = base64.b64decode(service.xpathEval('output')[0].get_content()).rstrip()

	line = "[%s]; PROCESS_SERVICE_CHECK_RESULT;%s;%s;%s;%s" % (now, options.name, srvdescr, retcode, output )
	commands += line + '\n'

	if options.verb >= 1:
		print line

pipe = open(options.pipe, "w")
pipe.write(commands)
pipe.close()
