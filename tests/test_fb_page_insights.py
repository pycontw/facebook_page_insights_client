from python_fb_page_insights_client import FBPageInsight, PageCompositeData, PostMetric, PageMetric, PostDetailMetric
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
        resp: PageCompositeData = fb.get_page_full(
            pycontw_page_id, until_date=(2020, 11, 15))
        page_data = resp.page
        for page_insight_data in page_data:  # InsightData
            key = page_insight_data.name
            if key == PageMetric.page_total_actions.name:
                key = "Actions_On_Page"
            elif key == PageMetric.page_views_total.name:
                key = "Page_Views"
            elif key == PageMetric.page_fan_adds_unique.name:
                key = "People_Likes"
            elif key == PageMetric.page_fan_adds.name:
                pass
            elif key == PageMetric.page_post_engagements.name:
                key = "Post_Engagement"
            elif key == PageMetric.page_video_views.name:
                key = "Videos"
            elif key == PageMetric.page_daily_follows_unique.name:
                key = "Page_Followers"
            elif key == PageMetric.page_impressions_organic_unique.name:
                key = "Post_Reach"

            # we only care about name & values, other are meta fields
            # name: str
            # period: str, e.g. week/lifetime
            # title: Optional[str]  # might be json null
            # description: str
            # id: str
            # values: List[InsightsValue]

            # PageMetric
            value_obj = page_insight_data.values[0]  # union.
            value = value_obj.value
            print("done")
        posts_data = resp.posts
        for post_composite_data in posts_data:
            insight_data = post_composite_data.insight_data
            for post_inisght_data in insight_data:
                key = post_inisght_data.name
                if key == PostMetric.post_impressions_organic_unique.name:
                    key = "Reach"
                elif key == PostMetric.post_clicks.name:
                    key = "Engagement_Post_Clicks"
                elif key == PostMetric.post_activity.name:
                    key = "Engagement_Activity"

                # list of InsightsValue.
                value_obj = post_inisght_data.values[0]
                value = value_obj.value  # value is union, currently it is int now
            insight_data_complement = post_composite_data.insight_data_complement
            for post_inisght_data in insight_data_complement:
                key = post_inisght_data.name
                if key == PostDetailMetric.post_activity_by_action_type.name:
                    data = post_inisght_data.values[0].value
                    value = {}
                    # on web, this value = sum(on post + on shares) but no api to get sub part
                    value["Likes"] = data.like
                    value["Comments"] = data.comment
                    value["Shares"] = data.share
                elif key == PostDetailMetric.post_clicks_by_type.name:
                    data = post_inisght_data.values[0].value
                    value = {}
                    value["Photo_Views"] = data.photo_view
                    value["Link_Clicks"] = data.link_clicks
                    value["Other_Clicks"] = data.other_clicks
                elif key == PostDetailMetric.post_negative_feedback_by_type_unique.name:
                    # 1. not sure whether web use this or below
                    # 2. always see no data, empty {}
                    value_obj = post_inisght_data.values[0]
                    value_dict = value_obj.value
                elif key == PostDetailMetric.post_negative_feedback_by_type.name:
                    pass
                else:
                    if key == PostDetailMetric.post_reactions_like_total.name:
                        key = "Likes_Like"
                    elif key == PostDetailMetric.post_reactions_love_total.name:
                        key = "Likes_Love"
                    elif key == PostDetailMetric.post_reactions_wow_total.name:
                        key = "Likes_Wow"
                    elif key == PostDetailMetric.post_reactions_haha_total.name:
                        key = "Likes_Haha"

                    value_obj = post_inisght_data.values[0]
                    value = value_obj.value

                    # e.g.
                    # value field:
                    # x post_clicks_by_type
                    #   {photo_view:1, link_clicks: 13, other_clicks:32}
                    # x post_activity_by_action_type
                    #   {like: 34, comment, share}
                    # post_reactions_like_total
                    #   34
                    # post_reactions_love_total
                    #   0
                    # post_reactions_wow_total
                    #   0
                    # post_reactions_haha_total
                    #   0
        self.assertEqual("ok", "ok")


if __name__ == '__main__':
    unittest.main()
