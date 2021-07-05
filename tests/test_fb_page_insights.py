import unittest

from facebook.page.insights import FBPageInsight
from dotenv import load_dotenv
import os

load_dotenv()


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_insight(self):
        user_access_token = os.getenv('user_access_token')
        fb_app_id = os.getenv('fb_app_id')
        fb_app_secret = os.getenv('fb_app_secret')
        args = {
            'user_access_token': user_access_token,
            'fb_app_id': fb_app_id,
            'fb_app_secret': fb_app_secret
        }
        pycontw_page_id = '160712400714277'
        fb = FBPageInsight(**args)
        data = fb.get_page_full(pycontw_page_id)
        self.assertEqual("ok", "ok")


if __name__ == '__main__':
    unittest.main()
