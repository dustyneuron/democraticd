#!/usr/bin/env python3.3

import json
import httplib2
import urllib
import time
import math


h = httplib2.Http("cache-dir")
h.add_credentials('name', 'password', 'api.github.com')

headers = {}
#headers["If-Modified-Since"] = r["last-modified"]
url = "https://api.github.com"
url = url + "/repos/dustyneuron/github-api-test/pulls/1?" + urllib.urlencode(dic)
r, content = h.request(url, headers=headers)
status = int(r['status'])

if status != 200 or status != 304:
        print(r['status'])
        print(r['content-type'])
        quit()
        

# "last-modified" -> "If-Modified-Since"
obj = json.loads(content)


url = "blah.com/foo?" + urllib.urlencode(dic)


# so, for first MVP in actual app we need:

# - to poll notifications, and filter out all but pull requests
# - then to get the data for that pull request
# - then to post a comment on pull request saying it's being proposed for vote, with a link

# not too hard :-)

# the code which receives the pull request data + spits out a comment
# should be asynchronous from the notify thread, as it'll take a few mins probably?? not really actually!
# will just be a few db calls.
# Use concurrent.futures, it's dead easy & can switch between using threading and multiprocessing
#with ThreadPoolExecutor(max_workers=1) as executor:
#    future = executor.submit(pow, 323, 1235)
#    print(future.result())
    
