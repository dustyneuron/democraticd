from democraticd.utils import iso_8601, DebugLevel

import gevent
import gevent.monkey
# This doesn't work yet under python 3
# gevent.monkey.patch_socket()

import json
import urllib3
import base64
import time
import datetime
import dateutil.parser


class GitHubError(Exception):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr.repr(self.value)
        

class GitHubAPI:
    json_methods = set(['PUT', 'POST'])
    base_url = 'api.github.com'
    
    def __init__(self, username, password, quit_event, log_func, make_comments=True):
        self.username = username
        self.password = password
        self.next_notify_time = time.time()
        self.notify_poll_interval = 0
        self.last_modified = {}
        self.conn_pool = None
        self.quit_event = quit_event
        self.log_func = log_func
        self.make_comments = make_comments
        
    def log(self, *args):
        self.log_func(*args)
            
    def _api_call(self, url, method='GET', fields=None, headers={}):
        self.log('_api_call(' + method + ', ' + url + ')')
        
        auth = bytes.decode(base64.b64encode((self.username + ':' + self.password).encode()))
        headers['Authorization'] = 'Basic %s' % auth
        headers['User-Agent'] = 'democraticd (mailto:demod@dustyneuron.com)'
        headers['Accept'] = '*/*'
        last_modified_key = method + ' ' + url
        if last_modified_key in self.last_modified:
            headers['If-Modified-Since'] = self.last_modified[last_modified_key]
        if (fields != None) and (method in self.json_methods):
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
                
        self.log(headers, DebugLevel.INFO)
        if fields:
            self.log(fields, DebugLevel.INFO)

        if not self.conn_pool:
            self.conn_pool = urllib3.HTTPSConnectionPool(self.base_url, maxsize=1)
        
        if method in self.json_methods:
            body=None
            if fields:
                body=json.dumps(fields)
            result = self.conn_pool.urlopen(method, url, headers=headers, body=body)
        else:
            result = self.conn_pool.request_encode_url(method, url, headers=headers, fields=fields)
                
        if not result:
            raise GitHubError('urllib request did not return a result')
            
        if result.headers.get('last-modified'):
            self.last_modified[last_modified_key] = result.headers.get('last-modified')
        
        self.log(result.headers, DebugLevel.INFO)
        if result.data:
            self.log('result.data:\n' +
                json.dumps(json.loads(result.data.decode('utf-8')), sort_keys=True, indent=4),
                DebugLevel.DEBUG)
        
        return result
        
    def _return_json(self, result):
        if result.status == 304:
            return []
        data = json.loads(result.data.decode('utf-8'))
        if len(data) >= 30:
            raise GitHubError('TODO: implement pagination')
        return data

    def get_new_notifications(self, mark_read=True):
        current_time = time.time()
        if self.next_notify_time > current_time:
            sleep_time = int(self.next_notify_time - current_time)
            self.log('Sleeping for ' + str(sleep_time) + ' secs because of X-poll-interval')
            if self.quit_event.wait(sleep_time):
                return []
            
        result = self._api_call('/notifications')
        if result.headers.get('last-modified'):
            last_modified = dateutil.parser.parse(result.headers.get('last-modified'))
            # GitHub API is broken and thinks GMT == UTC
            last_modified = last_modified.replace(tzinfo=None)
            last_modified = last_modified + datetime.timedelta(seconds=1)
                
        if result.headers.get('x-poll-interval'):
            self.notify_poll_interval = float(result.headers.get('x-poll-interval'))
        self.next_notify_time = time.time() + self.notify_poll_interval
        
        n_list = self._return_json(result)
        if n_list and mark_read:
            last_read_at = iso_8601(last_modified)
            result = self._api_call('/notifications', 'PUT', fields={'last_read_at': last_read_at})
            if result.status != 205:
                raise GitHubError(str(result.status) + result.reason)
            result.release_conn()
                
        return n_list
        
    def list_pull_requests(self, repo):
        result = self._api_call('/repos/' + self.username + '/' + repo + '/pulls')
        data = self._return_json(result)
        result.release_conn()
        return data
        
    def create_pull_request_comment(self, pull_request):
        if self.make_comments:
            url = ( '/repos/' + self.username + '/' + pull_request.repo +
                    '/issues/' + str(pull_request.issue_id) + '/comments')
                    
            approve_cmd = '`demod-client approve ' + pull_request.repo + ' ' + str(pull_request.issue_id) + "`"
            comment = """\
Thanks you for contributing!
Your change proposal can be approved by running """ + approve_cmd + """.
Note that if you push any more changes to this branch, you'll lose
approval/any votes your proposal had collected."""

            result = self._api_call(url, 'POST', fields={'body': comment})
            if result.status != 201:
                raise GitHubError(str(result.status) + result.reason)
            pull_request.set_comment_log(self._return_json(result))
            result.release_conn()
        else:
            pull_request.set_state('COMMENTED')
        
