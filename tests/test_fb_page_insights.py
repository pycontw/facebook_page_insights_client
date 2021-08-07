from python_fb_page_insights_client import FBPageInsight, PageWebInsightData, PostsWebInsightData, PageDefaultWebInsight, DatePreset, Period
import unittest


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_insight(self):

        fb = FBPageInsight()

        page_insight: PageWebInsightData = fb.get_page_default_web_insight(
            date_preset=DatePreset.last_7d, period=Period.day, since=1627901347, until=1628246947)

        posts_insight: PostsWebInsightData = fb.get_post_default_web_insight(
            until_date=(2020, 11, 15))

        self.assertEqual("ok", "ok")


if __name__ == '__main__':
    unittest.main()
