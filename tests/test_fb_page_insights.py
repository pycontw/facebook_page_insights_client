import unittest

from facebook.page.insights import FBPageInsight


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_insight(self):
        args = {
            'user_access_token': '',
            'fb_app_id': '1111808169305965',
            'fb_app_secret': ''
        }
        fb = FBPageInsight(**args)
        fb.get_page_insights('160712400714277')
        self.assertEqual(fb.dummy_test(), "ok")


if __name__ == '__main__':
    unittest.main()
