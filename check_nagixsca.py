#!/usr/bin/python

import base64
import datetime
import libxml2
import optparse
import sys

parser = optparse.OptionParser()

parser.add_option('-u', '', dest='url', help='URL of status file (nagixsca.xml)')
parser.add_option('-f', '', dest='file', help='(Path and) file name of status file')
parser.add_option('-H', '', dest='hostname', help='Host(name) to search for in stats file')
parser.add_option('-S', '', dest='servicedesc', help='Service description) to search for in stats file')
parser.add_option('-s', '', dest='seconds', type='int', help='Maximum age in seconds of nagixsca.xml timestamp')
parser.add_option('-m', '', action='store_true', dest='markold', help='Mark (Set state) of too old checks as UNKNOWN')
parser.add_option('-v', '', action='count', dest='verb', help='Verbose output')

parser.set_defaults(url=None)
parser.set_defaults(file='nagixsca.xml')
parser.set_defaults(hostname=None)
parser.set_defaults(servicedesc=None)
parser.set_defaults(name=None)
parser.set_defaults(seconds=14400)
parser.set_defaults(verb=0)

(options, args) = parser.parse_args()

if options.servicedesc==None and options.verb <= 1:
	print "Need at least a service description (-S) to search for!"
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
retcode = None

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
	srvdescr = decode(xmlname.get_content(), xmlname.prop('encoding'))

	if options.verb >= 1:
		print 'Got service "%s"' % srvdescr

	if options.servicedesc == srvdescr:
		xmloutput = service.xpathEval('output')[0]
		retcode  = service.xpathEval('returncode')[0].get_content()
		output   = decode(xmloutput.get_content(), xmlname.prop('encoding')).rstrip()

		if options.verb >= 1:
			print 'Found service "%s" with return code "%s" and output "%s"' % (srvdescr, retcode, output)

		if tooold:
			output = 'Nag(ix)SCA: Check result is %s(>%s) seconds old  - %s' % (timedelta, options.seconds, output)
			if options.markold:
				retcode = 3  # Unknown

		break

if retcode==None:
	print 'NAG(IX)SCA: Service "%s" not found!' % options.servicedesc
	sys.exit(127)
else:
	print output
	sys.exit(int(retcode))

