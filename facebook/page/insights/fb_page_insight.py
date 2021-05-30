from typing import List, Optional
from pydantic import BaseModel
from enum import Enum, auto
from dataclasses import dataclass, field

import http.client
import requests
import logging
logging.basicConfig(level=logging.DEBUG)
http.client.HTTPConnection.debuglevel = 1


# TODO: use these two
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


class Key(Enum):
    grant_type = auto()
    client_id = auto()
    client_secret = auto()
    fb_exchange_token = auto()

    metric = auto()
    date_preset = auto()
    period = auto()
    access_token = auto()


class Metric(Enum):
    page_total_actions = auto()
    page_views_total = auto()
    page_fan_adds_unique = auto()
    page_post_engagements = auto()
    page_video_views = auto()
    page_daily_follows_unique = auto()
    page_impressions_organic_unique = auto()
    page_fan_adds = auto()
    page_daily_follows = auto()


class Value(Enum):
    fb_exchange_token = auto()


class Category(BaseModel):
    id: str
    name: str


class InsightsValue(BaseModel):
    value: str
    end_time: str


class InsightsResult(BaseModel):
    name: str
    period: str
    values: List[InsightsValue]
    title: Optional[str]  # might be json null
    description: str
    id: str


class InsightsCursors(BaseModel):

    # get_page_insights
    previous: str  # similar query but add since & until
    next: str


# class InsightsPaging(BaseModel):
#     cursors: InsightsCursors


class InsightsResponse(BaseModel):
    data: List[InsightsResult]
    paging: InsightsCursors


class AccountResult(BaseModel):
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
    data: List[AccountResult]
    paging: AccountPaging


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
    mylist: list = field(default_factory=list)

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
    def compose_page_insights_request(self, token, object_id, endpoint, param_dict: dict[str, str]):
        params = self.convert_para_dict(param_dict)
        url = f'{self.api_url}/{object_id}/{endpoint}?access_token={token}{params}'
        r = requests.get(url)
        json_dict = r.json()
        return json_dict

    def convert_para_dict(self, param_dict: dict[str, str]):
        params = ""
        for key, value in param_dict.items():
            params += f'&{key}={value}'
        return params

    def convert_metric_list(self, metric_list: List[Metric]):
        metric_value = ''
        for metric in metric_list:
            metric_value += ","+metric.name
        return metric_value

    def get_page_insights(self, page_id, metric_list: List[Metric] = [], date_preset: DataPresent = DataPresent.yesterday, period: Period = Period.week):

        # TODO: validate parameters, metric_list: List[Metric] = [] is not clear to use default?

        if len(metric_list) == 0:
            metric_list = [e for e in Metric]

        metric_value = self.convert_metric_list(metric_list)

        page_token = ""
        if self.page_access_token == "":
            page_token = self.get_page_tokens(page_id)
        else:
            page_token = self.page_access_token
        json_dict = self.compose_page_insights_request(page_token,
                                                       page_id, "insights", {"metric": metric_value, "date_preset": date_preset.name, 'period': period.name})

        # parse it
        resp = InsightsResponse(**json_dict)
        return resp

    def get_posts(self):
        return

    def get_post_info(self):
        return

    def get_post_info_detailed(self):
        return

    def dummy_test(self):
        return "ok"
