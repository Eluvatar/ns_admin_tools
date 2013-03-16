import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError as EE
import urllib2,fcntl,time,logging

from getpass import getuser
try:
  from os import uname
except:
  def uname():
    return "Non-UNIX system?"
from socket import gethostname

uname_tuple=uname()
uname_str=str((uname_tuple[0],uname_tuple[2],uname_tuple[4]))
USER_AGENT=getuser()+'@'+gethostname()+" ("+uname_str+")"

LOCK_FILE_PATH="/tmp/ns.lock"

# Get the exclusive lock for talking to the NS API. This is a simple way
# of ensuring you don't break the API Rate limit: All programs relying
# on this lock will wait for it to be free before beginning.
LOCK_FILE=open(LOCK_FILE_PATH,'w+')
fcntl.flock(LOCK_FILE,fcntl.LOCK_EX)

logger = logging.getLogger(__name__)

last_request=0.0
def api_request(query,user_agent=USER_AGENT):
  """ requests information from version 3 of the NS API. Raises an urllib2.HTTPError if the requested object does not exist or you have been banned from the API. """ 
  global last_request
  query['v']='3'
  qs = map(lambda k: k+"="+(query[k] if isinstance(query[k],basestring) else "+".join(query[k])), query)
  url="http://www.nationstates.net/cgi-bin/api.cgi?"+"&".join(qs)
  req=urllib2.Request(url=url,headers={'User-Agent':user_agent})
  logger.debug("Waiting to get %s", url)
  now=time.time()
  while( now < last_request + 0.625 ):
    time.sleep( last_request + 0.625 - now )
    now=time.time()
  last_request=now
  logger.debug("Getting %s", url)
  try:
    try:
      return ET.parse(urllib2.urlopen(req))
    except EE:
      __handle_ee
      raise
  except urllib2.URLError as e:
    if not isinstance(e,urllib2.HTTPError) and e.reason[0] == 110:
      now=time.time()
      last_request=now
      logger.debug("Retrying %s", url)
      try:
        return ET.parse(urllib2.urlopen(req))
      except EE:
        __handle_ee(req)
        raise
    else:
      raise

def __handle_ee(req):
  logger.error("api_request of %s failed to parse",url)
  if logger.isEnabledFor(logging.DEBUG):
    now=time.time()
    while( now < last_request + 0.625 ):
      time.sleep( last_request + 0.625 - now )
      now=time.time()
    last_request=now
    f=urllib2.urlopen(req)
    logger.debug("---begin---")
    logger.debug(f.read())
    logger.debug("---end---")

import atexit
from os import remove as remove_file

def __cleanup():
  now = time.time()
  time.sleep( last_request + 0.625 - now)
  LOCK_FILE.close()
  remove_file(LOCK_FILE_PATH)

atexit.register(__cleanup)
