from datetime import datetime, timedelta
from typing import List, Optional, Union, Dict, Tuple, Literal

from pydantic import BaseModel, BaseSettings, Field, validator
from enum import Enum, auto, IntEnum
# from dataclasses import dataclass, field
import time

import http.client
import requests
import logging

# debug only
# logging.basicConfig(level=logging.DEBUG)
# http.client.HTTPConnection.debuglevel = 1


class FBPageInsightConst(IntEnum):
    default_between_days = 365


class DatePreset(Enum):
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
    """ TODO: not used, just prepare, add it later"""
    grant_type = auto()
    client_id = auto()
    client_secret = auto()
    fb_exchange_token = auto()

    metric = auto()
    date_preset = auto()
    period = auto()
    access_token = auto()


class QueryValue(Enum):
    """ TODO: not used, just prepare, add it later"""
    fb_exchange_token = auto()


class PostDetailMetric(Enum):
    """ support period: lifetime """
    post_clicks_by_type = auto()
    post_activity_by_action_type = auto()
    post_reactions_like_total = auto()
    post_reactions_love_total = auto()
    post_reactions_wow_total = auto()
    post_reactions_haha_total = auto()

    # not sure web uses it or below
    # post_negative_feedback_by_type_unique = auto()
    # post_negative_feedback_by_type = auto()


class PostMetric(Enum):
    """ support period: lifetime """
    post_impressions_organic_unique = auto()
    post_clicks = auto()
    post_activity = auto()


class PageMetric(Enum):
    """ support period: day/week/days_28/month """
    page_total_actions = auto()
    page_views_total = auto()

    # not sure web use this or below
    page_fan_adds_unique = auto()
    page_fan_adds = auto()

    page_post_engagements = auto()
    page_video_views = auto()
    # page_daily_follows_unique not found on https://developers.facebook.com/docs/graph-api/reference/v11.0/insights
    page_daily_follows_unique = auto()
    page_impressions_organic_unique = auto()


class PostActivityValue(BaseModel):
    share: int = None
    like: int = None
    comment: int = None


class PostClickValue(BaseModel):
    photo_view: int = Field(None, alias='photo view')
    link_clicks: int = Field(None, alias='link clicks')
    other_clicks: int = Field(None, alias='other clicks')


class ByTypeValue(PostActivityValue, PostClickValue):
    ''' since pydantic union has some bug, so combine them (intersection)'''
    # TODO: add more ByTypeValue, e.g. page_positive_feedback_by_type
    pass


class InsightsValue(BaseModel):
    # BUG (pydantic): how to handle union?
    # Dict is for post_negative_feedback_by_type_unique/post_negative_feedback_by_type part
    # remove PostActivityValue, PostClickValue in union since pydantic has bugs
    # when dealing with union, https://github.com/samuelcolvin/pydantic/issues/2941
    value: Union[int, ByTypeValue] = None
    # value: PostActivityValue

    # if period is lifetime, end_time will not appear here
    end_time: Optional[str]


class InsightData(BaseModel):
    id: str
    name: str
    period: str
    values: List[InsightsValue]
    title: Optional[str]  # might be json null
    description: str


class InsightsCursors(BaseModel):
    # not seen Optional case but add it just in case
    previous: Optional[str]  # similar query but add since & until
    # if query time range includes a future day,
    # next will be missing
    next: Optional[str]


# page & post both use this
class InsightsResponse(BaseModel):
    data: List[InsightData]
    # not seen Optional case but add it just in case
    paging: Optional[InsightsCursors]


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
    id: str
    # e.g. 2021-08-07T07:00:00+0000
    created_time: str = Field(
        format='date-time'
    )
    message: Optional[str]  # either message or story
    # "story": "PyCon Taiwan 更新了封面相片。", or "PyCon Taiwan updated their status."
    story: Optional[str]
    page_id: Optional[str]

    @validator('created_time')
    def set_created_time(cls, v):
        return datetime.strptime(
            v, '%Y-%m-%dT%H:%M:%S+%f').isoformat()


class PostsPaging(BaseModel):
    # not see Optional case but add it just in case
    cursors: Optional[BeforeAfterCursors]
    next: Optional[str]


class PostsResponse(BaseModel):
    data: List[PostData]
    # not see Optional case but add it just in case
    paging: Optional[PostsPaging]


class PostCompositeData(BaseModel):
    # TODO: meta might not be a good name
    meta: PostData
    insight_data: Optional[List[InsightData]]
    insight_data_complement: Optional[List[InsightData]]


class PageDefaultWebInsight(BaseModel):
    page_id: str
    end_time: str = Field(
        format='date-time'
    )
    period: str = None

    actions_on_page: int = None
    page_views: int = None
    page_likes: int = None
    post_engagement: int = None
    videos: int = None
    page_followers: int = None
    post_reach: int = None

    @validator('end_time')
    def set_end_time(cls, v):
        return datetime.strptime(
            v, '%Y-%m-%dT%H:%M:%S+%f').isoformat()


class PartialJSONSchema(BaseModel):
    title: Optional[str]
    description: Optional[str]  # Optional
    type: Optional[str]
    # e.g.
    # "count": {
    #   "title": "Count",
    #   "type": "integer"
    # },
    properties: Optional[Dict[str, Dict]]

    # "required": [
    #   "count"
    # ]
    required: Optional[List[str]]  # Optional
    definitions: Optional[Dict[str, Dict]]  # Optional


class PageWebInsightData(BaseModel):
    insight_list: Optional[List[PageDefaultWebInsight]]
    insight_json_schema: Optional[PartialJSONSchema]
    # used_metric_desc_dict: Optional[Dict[str, str]]


class PostDefaultWebInsight(BaseModel):

    post_id: str = None

    # NOTE: this is injected, not in return data of fb page insight api request
    query_time: str = Field(None,
                            format='date-time')

    period: str = Period.lifetime.name

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
    # query_time: Optional[int]
    # period: str = Period.week.lifetime.name
    insight_list: List[PostDefaultWebInsight] = []
    insight_json_schema: Optional[PartialJSONSchema]
    # used_metric_desc_dict: Optional[Dict[str, str]]

    post_list: List[PostData] = []
    post_json_schema: Optional[PartialJSONSchema]


class LongLivedResponse(BaseModel):
    access_token: str
    token_type: str


class FBPageInsight(BaseSettings):
    fb_page_access_token_dict: Optional[Dict[str, str]]
    fb_app_id = ""
    fb_app_secret = ""
    fb_user_access_token = ""
    fb_default_page_id = ""
    fb_default_page_access_token = ""

    # https://developers.facebook.com/docs/graph-api/reference/v10.0/insights
    # field(init=False, default='https://graph.facebook.com')
    api_server = 'https://graph.facebook.com'
    api_version = 'v10.0'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

    # class Config:
    #     env_file = ".env"

    @property
    def api_url(self):
        return f'{self.api_server}/{self.api_version}'

    # TODO:
    # 1. page_token is doable, too?
    def get_long_lived_user_token(self):
        if self.fb_user_access_token == "" or self.fb_app_id == "" or self.fb_app_secret == "":
            return ""
        url = f'{self.api_url}/oauth/access_token?grant_type=fb_exchange_token&client_id={self.fb_app_id}&client_secret={self.fb_app_secret}&fb_exchange_token={self.fb_user_access_token}'
        r = requests.get(url)
        json_dict = r.json()
        resp = LongLivedResponse(**json_dict)
        if resp.access_token != None:
            self.fb_user_access_token = resp.access_token
            return resp.access_token
        else:
            return ""

    # TODO: better way to refresh token instead of getting all pages' tokens?
    def get_page_token(self, target_page_id: str):
        if self.fb_user_access_token == "":
            if self.fb_default_page_access_token != "":
                # only use pre-defined page_token when user_token is not present
                return self.fb_default_page_access_token
            else:
                raise ValueError(
                    "fb_user_access_token should be assigned first")

        if target_page_id == None or target_page_id == "":
            raise ValueError("target_page_id should be a non empty string")
        if self.fb_page_access_token_dict == None:
            self.fb_page_access_token_dict = {}
        page_token = self.fb_page_access_token_dict.get(target_page_id)
        if page_token != None:
            return page_token

        url = f'{self.api_url}/me/accounts?access_token={self.fb_user_access_token}'
        r = requests.get(url)
        json_dict = r.json()
        resp = AccountResponse(**json_dict)
        if resp.data != None and len(resp.data) > 0:
            for data in resp.data:
                if data.access_token != None and data.id == target_page_id:
                    self.fb_page_access_token_dict[target_page_id] = data.access_token
                    return data.access_token
        return ""

    def compose_fb_graph_api_request(self, token: str, object_id: str, endpoint: str, param_dict: Dict[str, str] = {}):
        params = self._convert_para_dict(param_dict)
        url = f'{self.api_url}/{object_id}/{endpoint}?access_token={token}{params}'
        r = requests.get(url)
        json_dict = r.json()
        return json_dict

    def _convert_para_dict(self, param_dict: Dict[str, str]):
        params = ""
        for key, value in param_dict.items():
            params += f'&{key}={value}'
        return params

    def _convert_metric_list(self, metric_list: List[PageMetric]):
        metric_value = ''
        for i in range(0, len(metric_list)):
            metric = metric_list[i]
            if i == 0:
                metric_value += metric.name
            else:
                metric_value += ","+metric.name
        return metric_value

    def get_page_insights(self, page_id: str = None,
                          user_defined_metric_list: List[PageMetric] = [],
                          since: int = None, until: int = None,
                          date_preset: DatePreset = DatePreset.yesterday,
                          period: Period = Period.week):
        page_id = self._page_id(page_id)
        page_token = self.get_page_token(page_id)

        # TODO:
        # 1. validate parameters
        # 2. support empty period? it will return day/week/days_28

        if len(user_defined_metric_list) == 0:
            user_defined_metric_list = [e for e in PageMetric]
        metric_value = self._convert_metric_list(user_defined_metric_list)

        if since != None and until != None:
            json_dict = self.compose_fb_graph_api_request(page_token,
                                                          page_id, "insights", {"metric": metric_value, "date_preset": date_preset.name, 'period': period.name, "since": since, "until": until})
        else:
            json_dict = self.compose_fb_graph_api_request(page_token,
                                                          page_id, "insights", {"metric": metric_value, "date_preset": date_preset.name, 'period': period.name})
        resp = InsightsResponse(**json_dict)
        return resp

    # TODO: handle until is smaller than since
    def get_posts(self, page_id: str = None, since: int = None, until: int = None):
        # could use page_token or user_access_token
        page_id = self._page_id(page_id)
        page_token = self.get_page_token(page_id)

        # get_all = False
        next_url = ""
        post_data_list: List[PostData] = []
        while next_url != None:
            if next_url == "":
                if since != None and until != None:
                    json_dict = self.compose_fb_graph_api_request(page_token,
                                                                  # {"since": 1601555261, "until": 1625489082})
                                                                  page_id, "posts", {"since": since, "until": until})
                else:
                    json_dict = self.compose_fb_graph_api_request(page_token,
                                                                  page_id, "posts")
                resp = PostsResponse(**json_dict)
            else:
                r = requests.get(next_url)
                json_dict = r.json()
                resp = PostsResponse(**json_dict)
            next_url = resp.paging.next
            post_data_list += resp.data
        for post in post_data_list:
            post.page_id = page_id
        total_resp = PostsResponse(data=post_data_list, paging=resp.paging)
        return total_resp

    def get_post_insight(self, post_id: str, basic_metric=True, complement_metric=True, user_defined_metric_list: List[PageMetric] = []):
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
        metric_value = self._convert_metric_list(metric_list)

        page_token = self.get_page_token(page_id)

        json_dict = self.compose_fb_graph_api_request(page_token,
                                                      post_id, "insights", {"metric": metric_value})
        # NOTE: somehow FB will return invalid api result
        # if json_dict.get("data") == None:
        #     print("not ok") for debugging,
        resp = InsightsResponse(**json_dict)
        return resp

    def _page_id(self, page_id: str):
        if page_id == None:
            return self.fb_default_page_id
        return page_id

    def get_page_default_web_insight(self, page_id: str = None, since_date: Tuple[str, str, str] = None, until_date: Tuple[str, str, str] = None,
                                     date_preset: DatePreset = DatePreset.yesterday,
                                     period: Literal[Period.day, Period.week, Period.days_28, Period.month] = Period.week,  return_as_dict=False):
        """ period can not be lifetime"""
        page_id = self._page_id(page_id)
        if period == Period.lifetime:
            raise ValueError(
                'period can not be lifetime when querying default page insight')

        since = None
        until = None
        if since_date != None and until_date != None:
            since = int(datetime(
                *since_date).timestamp())
            until = int(datetime(
                *until_date).timestamp())

        page_summary = self.get_page_insights(
            page_id, since=since, until=until, date_preset=date_preset, period=period)
        page_summary_data = page_summary.data

        # page_composite_data = PagePostsCompositeData(
        #     fetch_time=int(time.time()), page=page_summary_data)

        resp = self._organize_to_web_page_data_shape(
            page_summary_data, page_id)

        if return_as_dict == True:
            return resp.dict()
        return resp

    def get_post_default_web_insight(self, page_id: str = None, since_date: Tuple[str, str, str] = None, until_date: Tuple[str, str, str] = None,  between_days: int = None,  return_as_dict=False):
        """
            since_date and until_date are the tuple form of (2020, 9, 7)
            if any of since_date and until_date is omitting, between_days will be used to decide either since_date or until_date and default value is 365. 
            if since_date & until_date both are omitting, until_date will be today (now)
            if since_date is omitting, since_date = until_date - between_days  
            if since_date is not omitting but until_date is omitting, then until_date = since_date + between_days
            since_date, until_date, period_days can not be all specified as non None at the same time, will throw a error 
        """

        if since_date != None and until_date != None and between_days != None:
            raise ValueError(
                "since_date, until_date, period_days can not all be non-None at the same time")

        query_time = datetime.now()  # int(time.time())
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

        if between_days == None:
            between_days = FBPageInsightConst.default_between_days

        if until_date == None:
            if since_date == None:
                until_time = query_time
            else:
                since_time = datetime(
                    *since_date)
                until_time = since_time + timedelta(days=between_days)
        else:
            until_time = datetime(*until_date)
        until = int(until_time.timestamp())

        if since_date == None:
            since_time = until_time - timedelta(days=between_days)
        else:
            since_time = datetime(
                *since_date)
        since = int(since_time.timestamp())

        recent_posts = self.get_posts(page_id, since, until)
        posts_data = recent_posts.data

        post_composite_list: List[PostCompositeData] = []
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
        resp = self._organize_to_web_posts_data_shape(
            post_composite_list, query_time)
        # resp.query_time = query_time
        if return_as_dict == True:
            return resp.dict()
        return resp

    def _organize_to_web_page_data_shape(self, page_data: List[InsightData], page_id: str):
        """ currently it only support one period, it querying with on specific period in low level api,
            will return multiple periods """

        insight_dict: Dict[int:PageDefaultWebInsight] = {}

        for page_insight_data in page_data:
            key = page_insight_data.name
            period = page_insight_data.period  # should be the same one
            # value_obj is union
            for value_obj in page_insight_data.values:
                value = value_obj.value
                end_time = value_obj.end_time
                # e.g. '2021-08-07T07:00:00+0000'
                # end_time = datetime.strptime(
                #     value_obj.end_time, '%Y-%m-%dT%H:%M:%S+%f').isoformat()  # .timestamp())
                insight = insight_dict.get(end_time)
                if insight == None:
                    insight = PageDefaultWebInsight(
                        period=period, page_id=page_id, end_time=end_time)
                    insight_dict[end_time] = insight
                    # insight.period = period
                    # insight.end_time = end_time
                if key == PageMetric.page_total_actions.name:
                    insight.actions_on_page = value
                elif key == PageMetric.page_views_total.name:
                    insight.page_views = value
                elif key == PageMetric.page_fan_adds_unique.name:
                    insight.page_likes = value
                elif key == PageMetric.page_fan_adds.name:
                    pass
                elif key == PageMetric.page_post_engagements.name:
                    insight.post_engagement = value
                elif key == PageMetric.page_video_views.name:
                    insight.videos = value
                elif key == PageMetric.page_daily_follows_unique.name:
                    insight.page_followers = value
                elif key == PageMetric.page_impressions_organic_unique.name:  # page_fans_gender_age?
                    insight.post_reach = value

            # we only care about name & values, other are meta fields
            # name: str
            # period: str, e.g. week/lifetime
            # title: Optional[str]  # might be json null
            # description: str
            # id: str
            # values: List[InsightsValue]

        pageInsightData = PageWebInsightData()
        pageInsightData.insight_list = list(insight_dict.values())
        # pageInsightData.used_metric_desc_dict = desc_dict
        pageInsightData.insight_json_schema = PartialJSONSchema(
            **PageDefaultWebInsight.schema())
        return pageInsightData

    def _organize_to_web_posts_data_shape(self, posts_data: List[PostCompositeData], query_time: datetime):

        postsWebInsight = PostsWebInsightData()
        # for post_composite_data in posts_data:
        for i, post_composite_data in enumerate(posts_data):
            insight = PostDefaultWebInsight(query_time=query_time.isoformat())
            # insight.query_time = query_time <- this way will not trigger any @validator
            insight_data = post_composite_data.insight_data
            insight.post_id = post_composite_data.meta.id

            postsWebInsight.insight_list.append(insight)
            postsWebInsight.post_list.append(post_composite_data.meta)

            for post_inisght_data in insight_data:

                key = post_inisght_data.name
                # desc_dict[key] = post_inisght_data.description

                # list of InsightsValue.
                value_obj = post_inisght_data.values[0]
                value = value_obj.value  # value is union, currently it is int now
                if key == PostMetric.post_impressions_organic_unique.name:
                    insight.reach = value
                elif key == PostMetric.post_clicks.name:
                    insight.engagement_post_clicks = value
                elif key == PostMetric.post_activity.name:
                    insight.engagement_activity = value

            insight_data_complement = post_composite_data.insight_data_complement
            for post_inisght_data in insight_data_complement:
                key = post_inisght_data.name
                # desc_dict[key] = post_inisght_data.description
                if key == PostDetailMetric.post_activity_by_action_type.name:
                    data = post_inisght_data.values[0].value
                    # on web, this value = sum(on post + on shares) but no api to get sub part
                    insight.likes = data.like
                    insight.comments = data.comment
                    insight.shares = data.share

                elif key == PostDetailMetric.post_clicks_by_type.name:
                    data = post_inisght_data.values[0].value

                    insight.photo_views = data.photo_view
                    insight.link_clicks = data.link_clicks
                    insight.other_clicks = data.other_clicks
                # elif key == PostDetailMetric.post_negative_feedback_by_type_unique.name:
                #     # TODO: add it later when we figure its data shape
                #     # 1. not sure whether web use this or below
                #     # 2. always see no data, empty {}
                #     # value_obj = post_inisght_data.values[0]
                #     # value_dict = value_obj.value
                #     pass
                # elif key == PostDetailMetric.post_negative_feedback_by_type.name:
                #     pass
                else:
                    value_obj = post_inisght_data.values[0]
                    value = value_obj.value
                    if key == PostDetailMetric.post_reactions_like_total.name:
                        insight.likes_like = value
                    elif key == PostDetailMetric.post_reactions_love_total.name:
                        insight.likes_love = value
                    elif key == PostDetailMetric.post_reactions_wow_total.name:
                        insight.likes_wow = value
                    elif key == PostDetailMetric.post_reactions_haha_total.name:
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
        postsWebInsight.insight_json_schema = PartialJSONSchema(
            **PostDefaultWebInsight.schema())
        postsWebInsight.post_json_schema = PartialJSONSchema(
            **PostData.schema())

        # postsWebInsight.used_metric_desc_dict = desc_dict
        return postsWebInsight
