from __future__ import print_function, unicode_literals

import unittest
from mock import Mock, MagicMock, call
import tempfile
import os, os.path
import shutil
import json
import gevent, gevent.event

import democraticd.pr_db
import democraticd.config
from democraticd.utils import DebugLevel
from democraticd.github_api import GitHubAPI


class TestPrDbi(unittest.TestCase):
    test_data_dir = os.path.join(os.getcwd(), 'test_data')

    def setUp(self):
        self.working_dir = tempfile.mkdtemp()
        conf_dir = os.path.join(self.working_dir, 'conf')
        self.config = democraticd.config.Config(debug_level=DebugLevel.DEBUG, mark_read=True, conf_dir=conf_dir)
        self.pr_db  = democraticd.pr_db.PullRequestDB(self.config)
        
        self.quit_event = gevent.event.Event()
        self.github_api = GitHubAPI('username', 'password', self.quit_event, self.config.log, make_comments=True)
        self.github_api._api_call = MagicMock(side_effect=(lambda s, *args: self.mock_api_call(self, s, *args)))
        self.api_results = []
        
    def tearDown(self):
        os.chdir('/')
        shutil.rmtree(self.working_dir)
        
    def load_test_data(self, filename):
        filename = os.path.join(self.test_data_dir, filename)
        with open(filename, 'rt') as f:
            return json.loads(f.read())
        
    def mock_api_call(self, github_api, url, method='GET', fields=None, headers={}):
        result = Mock()
        if method == 'GET':
            result.status = 200
        else:
            result.status = 201
        result.data = json.dumps(self.api_results.pop(0)).encode()
        result.headers.get.return_value = None
        return result
        
        
    def test_config(self):
        self.assertEqual(self.config.get_repo_set(), set([]))
        self.config.add_package('foobar')
        self.assertEqual(self.config.get_repo_set(), set(['foobar']))
        self.config.del_package('foobar')
        self.assertEqual(self.config.get_repo_set(), set([]))

        repo = 'democraticd'
        self.config.add_package(repo)
        self.pr_db.read_pull_requests(repo)
        self.assertEqual(self.pr_db.pull_requests(repo), [])
        
    def test_read_prs(self):
        repo = 'democraticd'
        self.config.add_package(repo)
        self.pr_db.read_pull_requests(repo)
        self.assertEqual(self.pr_db.pull_requests(repo), [])

        shutil.copy(
            os.path.join(self.test_data_dir, 'pullrequests1.json'),
            self.config.get_pull_requests_filename(repo))

        self.pr_db.read_pull_requests(repo)
        self.assertEqual(len(self.pr_db.pull_requests(repo)), 2)
            
    def test_notifications(self):
        repo = 'democraticd'
        self.config.add_package(repo)
        shutil.copy(
            os.path.join(self.test_data_dir, 'pullrequests1.json'),
            self.config.get_pull_requests_filename(repo))
        self.pr_db.read_pull_requests(repo)
        self.assertEqual(len(self.pr_db.pull_requests(repo)), 2)

        self.api_results.append([])
        new_repo_dict, do_quit = self.pr_db.get_new_pull_requests(self.github_api)
        self.assertEqual(new_repo_dict, {})
        self.assertEqual(self.github_api._api_call.call_args_list, [call('/notifications')])

        self.api_results.append(self.load_test_data('notifications.json'))
        new_repo_dict, do_quit = self.pr_db.get_new_pull_requests(self.github_api)
        self.assertEqual(len(new_repo_dict['democraticd']), 1)

if __name__ == '__main__':
    unittest.main()
