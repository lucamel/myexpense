
import os
import unittest
import json
from datetime import date

from myexpense import project
from myexpense.project._config import basedir
from myexpense.project.models.user import User

TEST_DB = 'test.db'

class MainTests(unittest.TestCase):
    db = project.db
    projetc_app = project.app

    # SetUp and TearDown
    def setUp(self):
        basedir = os.path.abspath(os.path.dirname(__file__))
        self.projetc_app.config['TESTING'] = True
        self.projetc_app.config['WTF_CSRF_ENABLED'] = False        
        self.projetc_app.config['DEBUG'] = False
        self.projetc_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, TEST_DB)

        self.app = self.projetc_app.test_client()
        self.db.init_app(self.projetc_app)
        self.db.app = self.projetc_app
        self.db.create_all()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()

    def create_user(self, email = "janedoe@example.com", name = "Jane Doe", password = 'Secret12', confirmed = False):
        new_user = User(email = email, name = name, password = password, confirmed = confirmed)
        self.db.session.add(new_user)
        self.db.session.commit()
        return new_user

    def get_access_token(self, username = "access@example.com"):
        new_user = self.create_user(email = username, confirmed=True)
        response = self.app.post('/auth', data=json.dumps({'username':new_user.email, 'password':'Secret12'}), content_type='application/json')
        return response.get_json()["access_token"]