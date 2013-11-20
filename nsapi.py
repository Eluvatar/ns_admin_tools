import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError as EE
from xml.etree.ElementTree import ParseError as PE
import httplib,fcntl,time,logging,socket,threading

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

conn = httplib.HTTPConnection("www.nationstates.net")

class CTE(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

last_request=0.0
def api_request(query,user_agent=USER_AGENT):
  """ requests information from version 3 of the NS API. Raises an httplib.HTTPError if the requested object does not exist or you have been banned from the API. """ 
  global last_request, conn
  query['v']='3'
  qs = map(lambda k: k+"="+(query[k] if isinstance(query[k],basestring) else "+".join(query[k])), query)
  path = "/cgi-bin/api.cgi?"+"&".join(qs)
  url = "http://www.nationstates.net"+path
  logger.debug("Waiting to get %s", url)
  now=time.time()
  while( now < last_request + 0.625 ):
    time.sleep( last_request + 0.625 - now )
    now=time.time()
  last_request=now
  logger.debug("Getting %s", url)
  f = None
  try:
    conn.request("GET",path,None,{'User-Agent':user_agent})
    done = False
    tries = 0
    while( not done ):
      try:
        tries += 1
        f = conn.getresponse()
        done = True
      except httplib.ResponseNotReady:
        logger.debug("Waiting for response...")
        time.sleep(1)
        if tries > 10:
          raise
      except httplib.BadStatusLine:
        conn = httplib.HTTPConnection("www.nationstates.net")
        conn.request("GET",path,None,{'User-Agent':user_agent})
        if tries > 10:
          raise
    if f.status == 200:
      return ET.parse(f)
    elif f.status == httplib.NOT_FOUND:
      f.read()
      if 'nation' in query:
        raise CTE(query['nation'])
      elif 'region' in query:
        raise CTE(query['region'])
      else:
        raise f
    elif f.status == httplib.REQUEST_TIMEOUT:
      now=time.time()
      last_request=now
      logger.debug("Retrying %s", url)
      conn.request("GET",path,None,{'User-Agent':user_agent})
      f = conn.getresponse()
      return ET.parse(f)
  except (EE,PE):
    __handle_ee(f,path,user_agent)
    raise
  finally:
    del f

def __handle_ee(f,path,user_agent):
  logger.error("api_request of %s failed to parse",url)
  if logger.isEnabledFor(logging.DEBUG):
    last_request=now
    logger.debug("---begin---")
    logger.debug(f.read())
    logger.debug("---end---")
    del f
  else:
    f.read()

import atexit
from os import remove as remove_file

def __unlock_rm():
  now = time.time()
  time.sleep( last_request + 0.625 - now)
  LOCK_FILE.close()
  remove_file(LOCK_FILE_PATH)

def __cleanup():
  t = threading.Thread(target=__unlock_rm)
  t.daemon = True
  t.start()

atexit.register(__cleanup)
