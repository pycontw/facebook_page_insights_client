import unittest

from facebook.page.insights import FBPageInsight


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_insight(self):
        fb = FBPageInsight()
        self.assertEqual(fb.dummy_test(), "ok")


if __name__ == '__main__':
    unittest.main()
