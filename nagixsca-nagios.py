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
parser.add_option('-s', '', dest='seconds', type='int', help='Maximum age in seconds of nagixsca.xml timestamp')
parser.add_option('-m', '', action='store_true', dest='markold', help='Mark (Set state) of too old checks as UNKNOWN')
parser.add_option('-v', '', action='count', dest='verb', help='Verbose output')

parser.set_defaults(url=None)
parser.set_defaults(file='nagixsca.xml')
parser.set_defaults(name=None)
parser.set_defaults(pipe=None)
parser.set_defaults(seconds=14400)
parser.set_defaults(verb=0)

(options, args) = parser.parse_args()

if options.name==None and options.verb <= 1:
	print "Need a hostname for Nagios!"
	sys.exit(127)

if options.pipe==None and options.verb <= 1:
	print "Need full path to the nagios.cmd pipe!"
	sys.exit(127)

##############################################################################

def decode(data, encoding):
	if encoding == 'plain':
		return data
	else:
		return base64.b64decode(data)

##############################################################################

now = datetime.datetime.now().strftime('%s')
commands = ""
tooold = False

# Open pipe only if not in debugging mode
if options.verb <= 2:
	pipe = open(options.pipe, "w")

# Get URL or file
if options.url != None:
	import urllib2

	response = urllib2.urlopen(options.url)
	doc = libxml2.parseDoc(response.read())
	response.close()
else:
	doc = libxml2.parseFile(options.file)

# Start XML work
try:
	timestamp = doc.xpathNewContext().xpathEval('/nagixsca/timestamp')[0].get_content()
except:
	print 'No timestamp found in XML file, exiting because of invalid XML data...'
	sys.exit(127)

timedelta = int(now) - int(timestamp)
if options.verb >= 2:
	print 'Age of XML checks: %s secods, max allowed: %s seconds' % (timedelta, options.seconds)
if timedelta > options.seconds:
	if options.verb >= 2:
		print 'Checks are too old (Delta: %s secods)' % timedelta
	tooold = True

services = doc.xpathNewContext().xpathEval("/nagixsca/service")

for service in services:
	xmlname   = service.xpathEval('name')[0]
	xmloutput = service.xpathEval('output')[0]

	srvdescr = decode(xmlname.get_content(), xmlname.prop('encoding'))
	retcode  = service.xpathEval('returncode')[0].get_content()
	output   = decode(xmloutput.get_content(), xmlname.prop('encoding')).rstrip()

	if tooold:
		output = 'Nag(ix)SCA: Check result is %s(>%s) seconds old  - %s' % (timedelta, options.seconds, output)
		if options.markold:
			retcode = 3  # Unknown

	line = '[%s] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%s;%s' % (now, options.name, srvdescr, retcode, output )

	if options.verb <= 2:
		pipe.write(line + '\n')

	if options.verb >= 1:
		print line

if options.verb <= 2:
	pipe.close()
else:
	print "Passive check results NOT written to Nagios pipe due to -vv!"

