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
    # page_daily_follows = auto()


class Category(BaseModel):
    id: str
    name: str


class PostClickValue(BaseModel):

    photo_view: int = Field(alias='photo view')
    link_clicks: int = Field(alias='link clicks')
    other_clicks: int = Field(alias='other clicks')


class PostActivityValue(BaseModel):
    share: Optional[int]
    like: Optional[int]
    comment: Optional[int]


class InsightsValue(BaseModel):
    # TODO: how to handle union?
    value: Union[int, PostClickValue, PostActivityValue,  Dict]  #
    # if period is lifetime, end_time will not appear here
    end_time: Optional[str]

    # post_negative_feedback_by_type_unique/post_negative_feedback_by_type
    # value: {} <- have never seen any data inside


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


class InsightsResponse(BaseModel):
    data: List[InsightData]
    paging: InsightsCursors


class AccountData(BaseModel):
    access_token: str
    category: str
    category_list: List[Category]
    name: str
    id: str
    tasks: List[str] = []


class AccountCursors(BaseModel):
    # get_page_tokens
    before: str
    after: str


class AccountPaging(BaseModel):
    cursors: AccountCursors


class AccountResponse(BaseModel):
    data: List[AccountData]
    paging: AccountPaging


class PostData(BaseModel):
    created_time: str
    message: Optional[str]  # either message or story
    story: Optional[str]  # "story": "PyCon Taiwan 更新了封面相片。",
    id: str


class PostCompositeData(BaseModel):
    meta: PostData
    insight_data: Optional[List[InsightData]]
    insight_data_complement: Optional[List[InsightData]]


class PageCompositeData(BaseModel):
    fetch_time: Optional[int]
    page: List[InsightData]
    posts: List[PostCompositeData]


class PostsPaging(BaseModel):
    cursors: AccountCursors
    next: Optional[str]


class PostsResponse(BaseModel):
    data: List[PostData]
    paging: PostsPaging


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
    def compose_page_insights_request(self, token, object_id, endpoint, param_dict: Dict[str, str] = {}):
        params = self.convert_para_dict(param_dict)
        url = f'{self.api_url}/{object_id}/{endpoint}?access_token={token}{params}'
        r = requests.get(url)
        json_dict = r.json()
        return json_dict

    def convert_para_dict(self, param_dict: Dict[str, str]):
        params = ""
        for key, value in param_dict.items():
            params += f'&{key}={value}'
        return params

    def convert_metric_list(self, metric_list: List[PageMetric]):
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
        metric_value = self.convert_metric_list(user_defined_metric_list)

        page_token = ""
        if self.page_access_token == "":
            page_token = self.get_page_tokens(page_id)
        else:
            page_token = self.page_access_token
        json_dict = self.compose_page_insights_request(page_token,
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
                    json_dict = self.compose_page_insights_request(page_token,
                                                                   # {"since": 1601555261, "until": 1625489082})
                                                                   page_id, "posts", {"since": since, "until": until})
                else:
                    json_dict = self.compose_page_insights_request(page_token,
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
        metric_value = self.convert_metric_list(metric_list)

        # TODO: refactor this part
        page_token = ""
        if self.page_access_token == "":
            page_token = self.get_page_tokens(page_id)
        else:
            page_token = self.page_access_token

        json_dict = self.compose_page_insights_request(page_token,
                                                       post_id, "insights", {"metric": metric_value})
        resp = InsightsResponse(**json_dict)
        return resp

    # def get_post_insight_complement(self, post_id, user_defined_metric_list: List[PostDetailMetric] = []):
    #     page_id = post_id.split('_')[0]

    #     if len(user_defined_metric_list) == 0:
    #         user_defined_metric_list = [e for e in PostDetailMetric]
    #     metric_value = self.convert_metric_list(user_defined_metric_list)

    #     page_token = ""
    #     if self.page_access_token == "":
    #         page_token = self.get_page_tokens(page_id)
    #     else:
    #         page_token = self.page_access_token

    #     json_dict = self.compose_page_insights_request(page_token,
    #                                                    post_id, "insights", {"metric": metric_value})

    #     resp = InsightsResponse(**json_dict)
    #     return resp

    # todo:
    # 1. refactor year part
    def get_page_full(self, page_id, since_date=(2020, 9, 7), until_date=None) -> PageCompositeData:
        # e.g.
        # {
        #   "data": [
        #     "name": "page_total_actions",
        #   ]
        #   "paging": {
        #   }
        # }
        page_summary = self.get_page_insights(page_id)
        page_summary_data = page_summary.data

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
        page_composite_data = PageCompositeData(fetch_time=int(time.time()),
                                                page=page_summary_data, posts=post_composite_list)
        return page_composite_data

    def dummy_test(self):
        return "ok"
