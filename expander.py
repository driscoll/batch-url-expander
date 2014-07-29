# -*- coding: utf-8 -*-
"""
Batch URL expander

Note: Speed up messy data by expanding only known short URLs 

(c) Kevin Driscoll, 2014

"""

from socket import error as SocketError
import fileinput
import multiprocessing
import re
import urllib
import urllib2

# Constants
USER_AGENT = u'shortURL lengthener/0.1 +http://kevindriscoll.info/'

# HTTP Error codes
HTTP_REDIRECT_CODES = [
    301, # Moved Permanently
    302, # Found, Moved temporarily
    303, # See other, Moved
    307,  # Temporary redirect
    '301', # Moved Permanently
    '302', # Found, Moved temporarily
    '303', # See other, Moved
    '307'  # Temporary redirect
]

# HTTP Timeout (in seconds)
# For more info on socket timeout:
# http://www.voidspace.org.uk/python/articles/urllib2.shtml#sockets-and-layers
HTTP_TIMEOUT = 5 # 60 
HTTP_MAX_REDIRECTS = 13

class LazyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, header, newurl):
        """On redirect, raise the HTTPError and die
        """
        return None


# URL utilities

SHORT_DOMAINS = []
fn = "short_domains.txt"
with open(fn, "r") as f:
    for line in f:
        SHORT_DOMAINS.append(line.strip())

def extract_domain(u):
    """Attempt to extract a domain name from u
        Returns string or None
    """
    domain_re = r'^(www.)?([^/]*)/?.*'
    if u.startswith('http'):
        brief = u.split('://', 1)[-1]
    else:   
        brief = u

    m = re.search(domain_re, brief)

    if m:
        return m.group(2)
    else:
        return None

def is_short_url(u):
    """Compare domain name against list of known short domains
        Returns True or False
    """
    domain = extract_domain(u)
    return (domain in SHORT_DOMAINS)
        


# Lengthening functions

def lengthen(u):
    """Return short_long dict of all URLs
        between u and its ultimate location
    """
    
    # For description of error handling, see:
    # http://www.voidspace.org.uk/python/articles/urllib2.shtml#httperror

    # Create URL opener that doesn't auto follow redirs
    opener = urllib2.build_opener(LazyHTTPRedirectHandler)

    # Create list of URLs
    hops = [u]

    # Set nexturl to the first URL
    nexturl = u

    # Follow all redirects, adding URLs to hops 
    while nexturl and (len(hops) < HTTP_MAX_REDIRECTS):
        request = urllib2.Request(nexturl)
        request.add_header('User-agent', USER_AGENT)
        try:
            r = opener.open(request, timeout=HTTP_TIMEOUT)
        except urllib2.HTTPError as err:
            if err.code in HTTP_REDIRECT_CODES:
                if u'location' in err.headers.keys():
                    loc = err.headers[u'location']
                    # Check for relative URL
                    if not loc[:4] == 'http':
                        nexturl = urllib.basejoin(err.geturl(), loc)
                    else:
                        nexturl = loc
                else:
                    nexturl = None
            else:
                nexturl = None
        except urllib2.URLError as err:
            # Server not found, etc.
            nexturl = None
        except ValueError:
            # Most likely an invalid URL
            nexturl = None
        except urllib2.httplib.BadStatusLine as err:
            # The server sent an unfamiliar status code 
            # Not caught by urllib2, see:
            # http://bugs.python.org/issue8823
            print err 
            nexturl = None
        except urllib2.httplib.InvalidURL as err:
            # Usually happens when there is a colon
            # but no port number
            print err
            nexturl = None
        except SocketError as err: 
            print err
            nexturl = None
        else:
            # Ultimate destination reached
            nexturl = None

        # Append the result to the hops list
        # None represents the end of the chain 
        if nexturl:
            hops.append(nexturl)

    return hops

def multilengthen(q):
    """Lengthen a list of short URLs in parallel
        Yields lists with chains of URL "hops" 
        Note: output order will not match input order
    """
    pool = multiprocessing.Pool()
    for urlchain in pool.imap_unordered(lengthen, q, 1000):
        yield urlchain


if __name__=="__main__":

    # Read list of short URLs
    shorturls = []
    for line in fileinput.input():
        url = line.strip()
        if is_short_url(url):
            shorturls.append(url)

    # Expand short URLs in parallel
    # Print short-long pairs as they arrive 
    for urlchain in multilengthen(shorturls):
        output = urlchain[0] 
        output += '\t'
        output += urlchain[-1]
        print output
