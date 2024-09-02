from dagster_slack import SlackResource
from dagster import (
    Definitions,
    load_assets_from_modules,
    EnvVar,
)
from . import assets, instagram_integration, twitter_integration
from .sensors.reddit import reddit_comment_sensor, reddit_post_sensor
from .sensors.hackernews import hackernews_sensor
from .resources import Keyword
from .instagram_integration import InstagramConfig
from .twitter_integration import TwitterConfig

all_assets = load_assets_from_modules([assets, instagram_integration, twitter_integration])

defs = Definitions(
    assets=all_assets,
    sensors=[
        reddit_post_sensor,
        reddit_comment_sensor,
        hackernews_sensor,
    ],
    resources={
        "slack": SlackResource(token=EnvVar("SLACK_BOT_TOKEN")),
        "keyword": Keyword(value="dagster"),
        "instagram_config": InstagramConfig(
            access_token=EnvVar("INSTAGRAM_ACCESS_TOKEN"),
            ig_user_id=EnvVar("INSTAGRAM_USER_ID"),
            brand_name=EnvVar("BRAND_NAME"),
            slack_channel=EnvVar("SLACK_CHANNEL"),
        ),
        "twitter_config": TwitterConfig(
            api_key=EnvVar("TWITTER_API_KEY"),
            api_secret_key=EnvVar("TWITTER_API_SECRET_KEY"),
            bearer_token=EnvVar("TWITTER_BEARER_TOKEN"),
            brand_name=EnvVar("BRAND_NAME"),
            slack_channel=EnvVar("SLACK_CHANNEL"),
        ),
    },
)
