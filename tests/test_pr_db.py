import unittest

import democraticd.pr_db
import democraticd.config
from democraticd.utils import DebugLevel

class TestPrDbi(unittest.TestCase):

    def setUp(self):
        self.config = democraticd.config.Config(debug_level=DebugLevel.DEBUG, mark_read=False)
        self.pr_db  = democraticd.pr_db.PullRequestDB(self.config)

    def test_foo(self):
        self.assertEqual(1, 1)
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
