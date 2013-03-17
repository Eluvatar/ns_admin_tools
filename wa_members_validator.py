#!/usr/bin/python
from nsapi import api_request,CTE
from ns import id_str
from itertools import ifilterfalse
import json,urllib2
from getpass import getuser
try:
  from os import uname
except:
  def uname():
    return "Non-UNIX system?"
from socket import gethostname
import logging,sys

logging.basicConfig(format="%(asctime)s %(message)s")
if '-v' in sys.argv or '--verbose' in sys.argv:
  logging.getLogger().setLevel(logging.DEBUG)

uname_tuple=uname()
uname_str=str((uname_tuple[0],uname_tuple[2],uname_tuple[4]))
user_agent=getuser()+'@'+gethostname()+" WA members validator ("+uname_str+")"

nat_is_wa = {}
nat_exists = {}

def check_wa_status(nat):
  if nat not in nat_is_wa:
    try:
      natxml = None
      try:
        natxml = api_request({'nation':nat,'q':'wa'},user_agent)
        nat_is_wa[nat] = natxml.find('UNSTATUS').text != 'Non-member'
      finally:
        del natxml
      nat_exists[nat] = True
    except CTE:
      nat_is_wa[nat] = False
      nat_exists[nat] = False
  return nat_is_wa[nat]

def exists(nat):
  if nat not in nat_exists:
    check_wa_status(nat)
  return nat_exists[nat]

wa_xml = api_request({'wa':'1','q':'members'},user_agent)

wa_members = wa_xml.find('MEMBERS').text.split(',')
  
del wa_xml

def page(nat):
  i=wa_members.index(nat)
  return i-i%15

__page_url__fmts="http://www.nationstates.net/page=list_nations/un=UN?start=%d"
def page_url(nat):
  return __page_url__fmts%page(nat)

wa_member_set=set(wa_members)

# I'm relying on some other code I run nightly to generate a list of nations in
# the WA as of the last major update which I run right after each major update
# ends here, which makes a list of WA members in update order at the below URL.
major_wa_members = map(id_str,json.load(urllib2.urlopen('http://www.thenorthpacific.org/api/wa.json')))
major_wa_member_set=set(major_wa_members)

new_wa_set = wa_member_set - major_wa_member_set
ex_wa_set = major_wa_member_set - wa_member_set

erroneously_listed = []
erroneously_not_listed = []

for nat in ifilterfalse(check_wa_status,new_wa_set):
  erroneously_listed.append(nat)

erroneously_not_listed = filter(check_wa_status,ex_wa_set)

print "The following nations listed in http://www.nationstates.net/cgi-bin/api.cgi/wa=1/q=members are not WA nations:"
print "[spoiler=%d nations erroneously listed][list=1]" % len(erroneously_listed)
for nat in erroneously_listed:
  if exists(nat):
    cte=""
  else:
    cte="(CTE)"
  print "[*][nation]%s[/nation] %s [[url=%s]page[/url]]"%(nat,cte,page_url(nat))

print "[/list][/spoiler]"

print "Worse, the following WA nations are not listed in [url]http://www.nationstates.net/cgi-bin/api.cgi/wa=1/q=members[/url]:"
print "[spoiler=%d nations erroneously not listed][list=1]" % len(erroneously_not_listed)
for nat in erroneously_not_listed:
  print "[*][nation]%s[/nation]" % nat

print "[/list][/spoiler]"

