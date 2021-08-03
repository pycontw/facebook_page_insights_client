from typing import List, Optional, Union, Dict
from pydantic import BaseModel, Field
from enum import Enum, auto
from dataclasses import dataclass, field
import time
import datetime

import http.client
import requests
import logging
logging.basicConfig(level=logging.DEBUG)
http.client.HTTPConnection.debuglevel = 1


class DataPresent(Enum):
    today = auto()
    yesterday = auto()
    this_month = auto()
    last_month = auto()
    this_quarter = auto()
    maximum = auto()
    last_3d = auto()
    last_7d = auto()
    last_14d = auto()
    last_28d = auto()
    last_30d = auto()
    last_90d = auto()
    last_week_mon_sun = auto()
    last_week_sun_sat = auto()
    last_quarter = auto()
    last_year = auto()
    this_week_mon_today = auto()
    this_week_sun_today = auto()
    this_year = auto()


class Period(Enum):
    day = auto()
    week = auto()
    days_28 = auto()
    month = auto()
    lifetime = auto()


class QueryKey(Enum):
    grant_type = auto()
    client_id = auto()
    client_secret = auto()
    fb_exchange_token = auto()

    metric = auto()
    date_preset = auto()
    period = auto()
    access_token = auto()


class QueryValue(Enum):
    fb_exchange_token = auto()


class PostDetailMetric(Enum):
    post_clicks_by_type = auto()
    post_activity_by_action_type = auto()
    post_reactions_like_total = auto()
    post_reactions_love_total = auto()
    post_reactions_wow_total = auto()
    post_reactions_haha_total = auto()

    # not sure web uses it or below
    post_negative_feedback_by_type_unique = auto()
    post_negative_feedback_by_type = auto()


class PostMetric(Enum):
    post_impressions_organic_unique = auto()
    post_clicks = auto()
    post_activity = auto()


class PageMetric(Enum):
    page_total_actions = auto()
    page_views_total = auto()

    # not sure web use this or below
    page_fan_adds_unique = auto()
    page_fan_adds = auto()

    page_post_engagements = auto()
    page_video_views = auto()
    page_daily_follows_unique = auto()
    page_impressions_organic_unique = auto()


# class PostClickValue(BaseModel):


# class PostActivityValue(BaseModel):
#     share: int = None
#     like: int = None
#     comment: int = None

class PostExtraValue(BaseModel):
    ''' since pydantic union has some bug, so combine them (intersection)'''

    # PostActivityValue
    share: int = None
    like: int = None
    comment: int = None
    # PostActivityValue
    photo_view: int = Field(None, alias='photo view')
    link_clicks: int = Field(None, alias='link clicks')
    other_clicks: int = Field(None, alias='other clicks')


class InsightsValue(BaseModel):
    # TODO: how to handle union?
    # Dict is for post_negative_feedback_by_type_unique/post_negative_feedback_by_type part
    # remove PostActivityValue, PostClickValue in union since pydantic has bugs
    # when dealing with union, https://github.com/samuelcolvin/pydantic/issues/2941
    value: Union[int, PostExtraValue] = None
    #value: PostActivityValue

    # if period is lifetime, end_time will not appear here
    end_time: Optional[str]


class InsightData(BaseModel):
    name: str
    period: str
    values: List[InsightsValue]
    title: Optional[str]  # might be json null
    description: str
    id: str


class InsightsCursors(BaseModel):
    previous: str  # similar query but add since & until
    next: str


# page & post both use this
class InsightsResponse(BaseModel):
    data: List[InsightData]
    paging: InsightsCursors


class Category(BaseModel):
    id: str
    name: str


class AccountData(BaseModel):
    access_token: str
    category: str
    category_list: List[Category]
    name: str
    id: str
    tasks: List[str] = []


# AccountResponse & PostsResponse/PostsPaging both use this
class BeforeAfterCursors(BaseModel):
    # get_page_tokens
    before: str
    after: str


class AccountPaging(BaseModel):
    cursors: BeforeAfterCursors


class AccountResponse(BaseModel):
    data: List[AccountData]
    paging: AccountPaging


class PostData(BaseModel):
    created_time: str
    message: Optional[str]  # either message or story
    story: Optional[str]  # "story": "PyCon Taiwan 更新了封面相片。",
    id: str


class PostsPaging(BaseModel):
    cursors: BeforeAfterCursors
    next: Optional[str]


class PostsResponse(BaseModel):
    data: List[PostData]
    paging: PostsPaging


class PostCompositeData(BaseModel):
    meta: PostData
    insight_data: Optional[List[InsightData]]
    insight_data_complement: Optional[List[InsightData]]


# class PagePostsCompositeData(BaseModel):
#     fetch_time: Optional[int]
#     page: List[InsightData] = []
#     posts: List[PostCompositeData] = []


class PageDefaultWebInsight(BaseModel):
    actions_on_page: int = None
    page_views: int = None
    page_likes: int = None
    post_engagement: int = None
    videos: int = None
    page_followers: int = None
    post_reach: int = None


class PartialJSONSchema(BaseModel):
    # e.g.
    # "count": {
    #   "title": "Count",
    #   "type": "integer"
    # },
    properties: Optional[Dict[str, Dict]]

    # "required": [
    #   "count"
    # ]
    required: Optional[List[str]]


class PageWebInsightData(BaseModel):
    data: Optional[PageDefaultWebInsight]
    json_schema: Optional[PartialJSONSchema]
    used_metric_desc_dict: Optional[Dict[str, str]]


class PostDefaultWebInsight(BaseModel):
    reach: int = None
    engagement_post_clicks: int = None
    engagement_activity: int = None
    likes: int = None
    comments: int = None
    shares: int = None
    photo_views: int = None
    link_clicks: int = None
    other_clicks: int = None
    likes_like: int = None
    likes_love: int = None
    likes_wow: int = None
    likes_haha: int = None


class PostsWebInsightData(BaseModel):
    data: List[PostDefaultWebInsight] = []
    json_schema: Optional[PartialJSONSchema]
    used_metric_desc_dict: Optional[Dict[str, str]]


class LongLivedResponse(BaseModel):
    access_token: str
    token_type: str


@dataclass
class FBPageInsight:
    fb_app_id: str = ""
    fb_app_secret: str = ""
    user_access_token: str = ""
    page_access_token: str = ""
    # https://developers.facebook.com/docs/graph-api/reference/v10.0/insights
    api_server: str = field(init=False, default='https://graph.facebook.com')
    api_version = 'v10.0'

    def __post_init__(self):
        pass

    @property
    def api_url(self):
        return f'{self.api_server}/{self.api_version}'

    # TODO: page_token is doable, too?
    def get_long_lived_token(self):
        if self.user_access_token == "" or self.fb_app_id == "" or self.fb_app_secret == "":
            return ""
        url = f'{self.api_url}/oauth/access_token?grant_type=fb_exchange_token&client_id={self.fb_app_id}&client_secret={self.fb_app_secret}&fb_exchange_token={self.user_access_token}'
        r = requests.get(url)
        json_dict = r.json()
        resp = LongLivedResponse(**json_dict)
        if resp.access_token != None:
            self.user_access_token = resp.access_token
            return resp.access_token
        else:
            return ""

    # TODO: better way to refresh token instead of getting all pages' tokens?
    def get_page_tokens(self, target_page_id=""):
        if self.user_access_token == "":
            return ""
        url = f'{self.api_url}/me/accounts?access_token={self.user_access_token}'
        r = requests.get(url)
        json_dict = r.json()
        resp = AccountResponse(**json_dict)
        if resp.data != None and len(resp.data) > 0:
            for data in resp.data:
                if data.access_token != None and data.id == target_page_id:
                    return data.access_token
        return ""

    # TODO: add since/until (e.g. since=1620802800&until=1620975600)
    def compose_insight_api_request(self, token, object_id, endpoint, param_dict: Dict[str, str] = {}):
        params = self.__convert_para_dict(param_dict)
        url = f'{self.api_url}/{object_id}/{endpoint}?access_token={token}{params}'
        r = requests.get(url)
        json_dict = r.json()
        return json_dict

    def __convert_para_dict(self, param_dict: Dict[str, str]):
        params = ""
        for key, value in param_dict.items():
            params += f'&{key}={value}'
        return params

    def __convert_metric_list(self, metric_list: List[PageMetric]):
        metric_value = ''
        for i in range(0, len(metric_list)):
            metric = metric_list[i]
            if i == 0:
                metric_value += metric.name
            else:
                metric_value += ","+metric.name
        return metric_value

    def get_page_insights(self, page_id, user_defined_metric_list: List[PageMetric] = [], date_preset: DataPresent = DataPresent.yesterday, period: Period = Period.week):

        # TODO: validate parameters, metric_list: List[Metric] = [] is not clear to use default?

        if len(user_defined_metric_list) == 0:
            user_defined_metric_list = [e for e in PageMetric]
        metric_value = self.__convert_metric_list(user_defined_metric_list)

        page_token = ""
        if self.page_access_token == "":
            page_token = self.get_page_tokens(page_id)
        else:
            page_token = self.page_access_token
        json_dict = self.compose_insight_api_request(page_token,
                                                     page_id, "insights", {"metric": metric_value, "date_preset": date_preset.name, 'period': period.name})

        resp = InsightsResponse(**json_dict)
        return resp

    # todo: handle until is smaller than since
    def get_recent_posts(self, page_id, since: int = 0, until: int = 0):
        # could use page_token or user_access_token
        page_token = ""
        if self.page_access_token == "":
            page_token = self.get_page_tokens(page_id)
        else:
            page_token = self.page_access_token

        # get_all = False
        next_url = ""
        post_data_list: List[PostData] = []
        while next_url != None:
            if next_url == "":
                if since != 0 and until != 0:
                    json_dict = self.compose_insight_api_request(page_token,
                                                                 # {"since": 1601555261, "until": 1625489082})
                                                                 page_id, "posts", {"since": since, "until": until})
                else:
                    json_dict = self.compose_insight_api_request(page_token,
                                                                 page_id, "posts")
                resp = PostsResponse(**json_dict)
            else:
                r = requests.get(next_url)
                json_dict = r.json()
                resp = PostsResponse(**json_dict)
            next_url = resp.paging.next
            post_data_list += resp.data
        total_resp = PostsResponse(data=post_data_list, paging=resp.paging)
        return total_resp

    def get_post_insight(self, post_id, basic_metric=True, complement_metric=True, user_defined_metric_list=[]):
        page_id = post_id.split('_')[0]

        if len(user_defined_metric_list) == 0:
            metric_list = []
            if basic_metric is True:
                metric_list += [
                    e for e in PostMetric]
            if complement_metric is True:
                metric_list += [e for e in PostDetailMetric]
        else:
            metric_list = user_defined_metric_list
        metric_value = self.__convert_metric_list(metric_list)

        # TODO: refactor this part
        page_token = ""
        if self.page_access_token == "":
            page_token = self.get_page_tokens(page_id)
        else:
            page_token = self.page_access_token

        json_dict = self.compose_insight_api_request(page_token,
                                                     post_id, "insights", {"metric": metric_value})
        resp = InsightsResponse(**json_dict)
        return resp

    # TODO: add since/until or date_preset/period
    def get_page_default_web_insight(self, page_id, as_dict=False):
        page_summary = self.get_page_insights(page_id)
        page_summary_data = page_summary.data

        # page_composite_data = PagePostsCompositeData(
        #     fetch_time=int(time.time()), page=page_summary_data)

        resp = self.__organize_to_web_page_data_shape(page_summary_data)

        if as_dict == True:
            return resp.dict()
        return resp

    def get_post_default_web_insight(self, page_id, since_date=(2020, 9, 7), until_date=None,  as_dict=False):

        # e.g.
        # {
        #   "data": [
        #     "name": "page_total_actions",
        #   ]
        #   "paging": {
        #   }
        # }
        # page_summary = self.get_page_insights(page_id)
        # page_summary_data = page_summary.data

        # if force_2021_whole_year:
        # first_day_next_month = datetime.datetime(2021, 1, 1)
        # e.g. 1609430400
        since = int(time.mktime(datetime.datetime(*since_date).timetuple()))

        if until_date == None:
            until = int(time.time())  # 1627209209
        else:
            until = int(time.mktime(
                datetime.datetime(*until_date).timetuple()))

        recent_posts = self.get_recent_posts(page_id, since, until)
        posts_data = recent_posts.data

        post_composite_list = []
        # iterate each post
        for post in posts_data:
            composite_data = PostCompositeData(meta=post)
            composite_data.insight_data = []
            composite_data.insight_data_complement = []
            post_composite_list.append(composite_data)
            post_id = post.id
            post_insight = self.get_post_insight(post_id)
            post_insight_data = post_insight.data
            for post_insight in post_insight_data:
                if post_insight.name in PostMetric.__members__:
                    composite_data.insight_data.append(post_insight)
                else:
                    composite_data.insight_data_complement.append(post_insight)
            print("query post info. done")
        print('query finish')
        # page_composite_data = PagePostsCompositeData(fetch_time=int(time.time()),
        #                                              posts=post_composite_list)

        # organize to the data structure shown on web
        resp = self.__organize_to_web_posts_data_shape(post_composite_list)

        if as_dict == True:
            return resp.dict()
        return resp

    def __organize_to_web_page_data_shape(self, page_data: List[InsightData]):
        insight = PageDefaultWebInsight()
        # desc_dict = {}

        # resp = {}
        for page_insight_data in page_data:  # InsightData
            key = page_insight_data.name
            value_obj = page_insight_data.values[0]  # union.
            value = value_obj.value
            # desc_dict[key] = page_insight_data.description
            if key == PageMetric.page_total_actions.name:
                # key = "actions_on_page"
                insight.actions_on_page = value
            elif key == PageMetric.page_views_total.name:
                # key = "page_views"
                insight.page_views = value
            elif key == PageMetric.page_fan_adds_unique.name:
                # key = "people_likes"
                insight.page_likes = value
            elif key == PageMetric.page_fan_adds.name:
                pass
            elif key == PageMetric.page_post_engagements.name:
                # key = "post_engagement"
                insight.post_engagement = value
            elif key == PageMetric.page_video_views.name:
                # key = "videos"
                insight.videos = value
            # not found on https://developers.facebook.com/docs/graph-api/reference/v11.0/insights
            elif key == PageMetric.page_daily_follows_unique.name:
                # key = "page_followers"
                insight.page_followers = value
            elif key == PageMetric.page_impressions_organic_unique.name:  # page_fans_gender_age?
                # key = "post_reach"
                insight.post_reach = value

            # we only care about name & values, other are meta fields
            # name: str
            # period: str, e.g. week/lifetime
            # title: Optional[str]  # might be json null
            # description: str
            # id: str
            # values: List[InsightsValue]

            # PageMetric

            # resp[key] = value
            # tt = type(value)
            # print("done")

        schema = PageDefaultWebInsight.schema()
        pageInsightData = PageWebInsightData()
        pageInsightData.data = insight
        # pageInsightData.used_metric_desc_dict = desc_dict
        partial = PartialJSONSchema(**schema)
        pageInsightData.json_schema = partial
        return pageInsightData

    def __organize_to_web_posts_data_shape(self, posts_data: List[PostCompositeData]):
        # todo: how to convert desc_dict to bigquery column desc as activity/click have 1 to many relation ???

        # desc_dict = {}
        postsWebInsight = PostsWebInsightData()
        # for post_composite_data in posts_data:
        for i, post_composite_data in enumerate(posts_data):
            insight = PostDefaultWebInsight()
            postsWebInsight.data.append(insight)
            insight_data = post_composite_data.insight_data
            for post_inisght_data in insight_data:

                key = post_inisght_data.name
                # desc_dict[key] = post_inisght_data.description

                # list of InsightsValue.
                value_obj = post_inisght_data.values[0]
                value = value_obj.value  # value is union, currently it is int now
                if key == PostMetric.post_impressions_organic_unique.name:
                    # key = "reach"
                    insight.reach = value
                elif key == PostMetric.post_clicks.name:
                    # key = "engagement_post_clicks"
                    insight.engagement_post_clicks = value
                elif key == PostMetric.post_activity.name:
                    # key = "engagement_activity"
                    insight.engagement_activity = value

            insight_data_complement = post_composite_data.insight_data_complement
            for post_inisght_data in insight_data_complement:
                key = post_inisght_data.name
                # desc_dict[key] = post_inisght_data.description
                if key == PostDetailMetric.post_activity_by_action_type.name:
                    data = post_inisght_data.values[0].value
                    # on web, this value = sum(on post + on shares) but no api to get sub part
                    # value["likes"] = data.like
                    # value["comments"] = data.comment
                    # value["shares"] = data.share
                    # try:
                    insight.likes = data.like  # data.get('like')
                    insight.comments = data.comment  # data.get('comment')
                    insight.shares = data.share  # data.get('share')
                    # except:
                    #     print(
                    #         "it is a hard handle case for union + empty data, it would use PostClickValue")

                elif key == PostDetailMetric.post_clicks_by_type.name:
                    data = post_inisght_data.values[0].value

                    insight.photo_views = data.photo_view  # get('photo view')
                    # get('link clicks')
                    insight.link_clicks = data.link_clicks
                    # get('other clicks')
                    insight.other_clicks = data.other_clicks

                    # except:
                    #print("it is a hard handle case for union")

                elif key == PostDetailMetric.post_negative_feedback_by_type_unique.name:
                    # TODO: add it later when we figure its data shape
                    # 1. not sure whether web use this or below
                    # 2. always see no data, empty {}
                    # value_obj = post_inisght_data.values[0]
                    # value_dict = value_obj.value
                    pass
                elif key == PostDetailMetric.post_negative_feedback_by_type.name:
                    pass
                else:
                    value_obj = post_inisght_data.values[0]
                    value = value_obj.value
                    if key == PostDetailMetric.post_reactions_like_total.name:
                        # key = "likes_like"
                        insight.likes_like = value
                    elif key == PostDetailMetric.post_reactions_love_total.name:
                        # key = "likes_love"
                        insight.likes_love = value
                    elif key == PostDetailMetric.post_reactions_wow_total.name:
                        # key = "likes_wow"
                        insight.likes_wow = value
                    elif key == PostDetailMetric.post_reactions_haha_total.name:
                        # key = "likes_haha"
                        insight.likes_haha = value

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
        schema = PostDefaultWebInsight.schema()
        partial = PartialJSONSchema(**schema)
        postsWebInsight.json_schema = partial
        # postsWebInsight.used_metric_desc_dict = desc_dict
        return postsWebInsight

    def dummy_test(self):
        return "ok"
