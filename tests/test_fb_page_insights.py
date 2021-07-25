from python_fb_page_insights_client import FBPageInsight
import unittest
import os

from dotenv import load_dotenv


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_insight(self):
        load_dotenv()
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
        data = fb.get_page_full(pycontw_page_id, until_date=(2020, 11, 15))
        self.assertEqual("ok", "ok")


if __name__ == '__main__':
    unittest.main()
