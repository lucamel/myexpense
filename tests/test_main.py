
import os
import unittest

from myexpense import project
from myexpense.project._config import basedir
from datetime import date

TEST_DB = 'test.db'

class MainTests(unittest.TestCase):

    # SetUp and TearDown

    def setUp(self):
        project.app.config['TESTING'] = True
        project.app.config['WTF_CSRF_ENABLED'] = False        
        project.app.config['DEBUG'] = False
        project.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, TEST_DB)

        self.app = project.app.test_client()
        project.db.create_all()

    def tearDown(self):
        project.db.session.remove()
        project.db.drop_all()
        