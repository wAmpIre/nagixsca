#!/usr/bin/python

import base64
import datetime
import libxml2
import optparse
import re
import subprocess

services = []

parser = optparse.OptionParser()

parser.add_option('-c', '', dest='cfgfile', help='Config file')
parser.add_option('-o', '', dest='xmlfile', help='Output file')
parser.add_option('-v', '', action='count', dest='verb', help='Verbose output')

parser.set_defaults(cfgfile='nagixsca-cron.conf')
parser.set_defaults(xmlfile='nagixsca.xml')
parser.set_defaults(verb=0)

(options, args) = parser.parse_args()

##############################################################################

file = open(options.cfgfile)
for line in file:
	result = re.match('^command\[([-_a-zA-Z0-9]+)\]=(.*)$', line)
	if result:
		services.append([result.group(1), result.group(2)])

if options.verb >= 1:
	print services

xmldoc = libxml2.newDoc('1.0')
xmlroot = xmldoc.newChild(None, 'nagixsca', None)
xmltimestamp = xmlroot.newChild(None, 'timestamp', datetime.datetime.now().strftime('%s'))

for service, cmdline in services:

	cmd = subprocess.Popen(cmdline.split(' '), stdout=subprocess.PIPE)
	output = cmd.communicate()[0]
	retcode = cmd.returncode

	if options.verb >= 1:
		print "\n\n%s\n== %s\n== %s" % (cmdline, output, retcode)

	xmlchild = xmlroot.newChild(None, 'service', None)
	xmlname = xmlchild.newChild(None, 'name', base64.b64encode(service))
	xmlname.setProp('encoding', 'base64')
	xmlreturncode = xmlchild.newChild(None, 'returncode', str(retcode))
	xmloutput = xmlchild.newChild(None, 'output', base64.b64encode(output))
	xmloutput.setProp('encoding', 'base64')

xmldoc.saveFile(options.xmlfile)
