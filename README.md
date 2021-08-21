# Python Facebook Page Insights Client

## Usage

## Get needed secrets first

https://github.com/facebook/facebook-python-business-sdk#register-an-app is a reference and the steps are 
1. create a FB app and get its `app_id` and `secret`, 
2. In terms of `user_access_token`, make sure you are a registered developer of this fb app and get user access token on Graph Explorer. You will get a short-term user_token by default, expired in 2 or 3 months. To get long-term token, choose either of the below ways
    - using Graph Exploer -> Access token tool -> Extend access token
    - invoke get_long_lived_user_token of this library 

Rather than Graph Explorer, https://github.com/pycontw/python-fb-page-insights-client/issues/6 introduces another way which does not to be a registered developer of this fb app. But this way is not recommanded. 

### Pass secrets 

After getting secrets, you need to pass below arguments to the library 

```
fb_user_access_token=
fb_app_id=
fb_app_secret=
fb_default_page_id=
fb_default_page_access_token=
```

You can choose any of below ways:
- pass them as function paramets
- manually export them as enviornments variables
- create a .env to include them

if fb_user_access_token is filled, fb_default_page_access_token is not necessary and will be ignored. fb_user_access_token will be used to get page token internally. 

## Fetch data 

Use `FBPageInsight` class to fetch. Please checkout the unit test code as an example. You also need to find out the fb page id and has the permission to get data, e.g. admin/analyst role.

### Rate limit

- [Application level limit](https://developers.facebook.com/apps/1111808169305965/rate-limit-details/app/) When using a user access token, the rate limit is 200 request per hour per token. You can check reamining quota shown in fb app dashboard, e.g. https://developers.facebook.com/apps/fb_dev_app_id]/rate-limit-details/app/
    - api response header includes `x-app-usage`
- [Page-Level Rate Limiting](https://developers.facebook.com/apps/1111808169305965/rate-limit-details/new_page/): for using a page token 
    - Business Use Case (BUC) Rate Limits
        - `Calls within one hour = 4800 * Number of Engaged Users`
        - api response header inclues `x-business-use-case-usage`

## Development

1. `poetry shell`
2. `poetry install`


### Run tests

Two methods:

- `python -m tests.test_fb_page_insights`
- In VSCode, `cmd+shift+p` to choose either item
  - `Python: Run All Tests`
  - `Python: Debug All Tests`
  - click any `run test`/`debug test` in `test_fb_page_insights.py`

## TODO:

https://github.com/pycontw/python-fb-page-insights-client/discussions/4
