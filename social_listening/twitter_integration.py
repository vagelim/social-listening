import tweepy
from dagster import asset, Config
from dagster_slack import SlackResource
import time

class TwitterConfig(Config):
    api_key: str
    api_secret_key: str
    bearer_token: str
    brand_name: str
    slack_channel: str

@asset
def twitter_mention(config: TwitterConfig, slack: SlackResource):
    """
    Fetch and process Twitter mentions for a brand, then send notifications.
    """
    # Set up Twitter API v2 client
    client = tweepy.Client(bearer_token=config.bearer_token)

    # Search for tweets mentioning the brand
    try:
        query = f"{config.brand_name} -is:retweet"
        tweets = client.search_recent_tweets(query=query, max_results=100, tweet_fields=['author_id', 'created_at'])
    except tweepy.TooManyRequests:
        print("Rate limit exceeded. Waiting for 15 minutes.")
        time.sleep(900)  # Wait for 15 minutes
        tweets = client.search_recent_tweets(query=query, max_results=100, tweet_fields=['author_id', 'created_at'])
    except tweepy.TwitterServerError as e:
        print(f"Twitter server error: {e}")
        return {"mentions_count": 0}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"mentions_count": 0}

    # Process and send notifications
    for tweet in tweets.data or []:
        try:
            author = client.get_user(id=tweet.author_id).data
            message = f"New Twitter mention for {config.brand_name}:\n"
            message += f"User: @{author.username}\n"
            message += f"Tweet: {tweet.text}\n"
            message += f"Link: https://twitter.com/{author.username}/status/{tweet.id}"

            slack.get_client().chat_postMessage(channel=config.slack_channel, text=message)
        except Exception as e:
            print(f"Error processing tweet {tweet.id}: {e}")

    return {
        "mentions_count": len(tweets.data or [])
    }
