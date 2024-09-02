import pytest
import tweepy
from unittest.mock import Mock, patch
from social_listening.twitter_integration import TwitterConfig, twitter_mention

@pytest.fixture
def mock_config():
    return TwitterConfig(
        api_key="test_api_key",
        api_secret_key="test_api_secret_key",
        bearer_token="test_bearer_token",
        brand_name="Test Brand",
        slack_channel="#test-channel"
    )

@pytest.fixture
def mock_slack():
    return Mock()

@pytest.fixture
def mock_tweepy_client():
    mock = Mock()
    mock.search_recent_tweets.return_value = Mock(data=[
        Mock(
            id="123",
            text="Test tweet",
            author_id="456"
        )
    ])
    mock.get_user.return_value = Mock(data=Mock(username="test_user"))
    return mock

@patch("social_listening.twitter_integration.tweepy.Client")
def test_twitter_mention(mock_client, mock_config, mock_slack, mock_tweepy_client):
    mock_client.return_value = mock_tweepy_client

    result = twitter_mention(mock_config, mock_slack)

    assert mock_client.call_count == 1
    assert mock_tweepy_client.search_recent_tweets.call_count == 1
    assert mock_tweepy_client.get_user.call_count == 1
    assert mock_slack.get_client().chat_postMessage.call_count == 1
    assert result == {"mentions_count": 1}

def test_twitter_config():
    config = TwitterConfig(
        api_key="test_api_key",
        api_secret_key="test_api_secret_key",
        bearer_token="test_bearer_token",
        brand_name="Test Brand",
        slack_channel="#test-channel"
    )
    assert config.api_key == "test_api_key"
    assert config.api_secret_key == "test_api_secret_key"
    assert config.bearer_token == "test_bearer_token"
    assert config.brand_name == "Test Brand"
    assert config.slack_channel == "#test-channel"

@patch("social_listening.twitter_integration.tweepy.Client")
def test_twitter_mention_no_data(mock_client, mock_config, mock_slack):
    mock_tweepy_client = Mock()
    mock_tweepy_client.search_recent_tweets.return_value = Mock(data=[])
    mock_client.return_value = mock_tweepy_client

    result = twitter_mention(mock_config, mock_slack)

    assert mock_client.call_count == 1
    assert mock_tweepy_client.search_recent_tweets.call_count == 1
    assert mock_slack.get_client().chat_postMessage.call_count == 0
    assert result == {"mentions_count": 0}

@patch("social_listening.twitter_integration.tweepy.Client")
def test_twitter_mention_rate_limit(mock_client, mock_config, mock_slack):
    mock_tweepy_client = Mock()
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.json.return_value = {"errors": [{"message": "Rate limit exceeded"}]}
    mock_tweepy_client.search_recent_tweets.side_effect = [
        tweepy.TooManyRequests(response=mock_response),
        Mock(data=[Mock(id="123", text="Test tweet", author_id="456")])
    ]
    mock_tweepy_client.get_user.return_value = Mock(data=Mock(username="test_user"))
    mock_client.return_value = mock_tweepy_client

    with patch("social_listening.twitter_integration.time.sleep") as mock_sleep:
        result = twitter_mention(mock_config, mock_slack)

    assert mock_client.call_count == 1
    assert mock_tweepy_client.search_recent_tweets.call_count == 2
    assert mock_sleep.call_count == 1
    assert mock_sleep.call_args[0][0] == 900  # 15 minutes
    assert mock_slack.get_client().chat_postMessage.call_count == 1
    assert result == {"mentions_count": 1}

@patch("social_listening.twitter_integration.tweepy.Client")
def test_twitter_mention_server_error(mock_client, mock_config, mock_slack):
    mock_tweepy_client = Mock()
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"errors": [{"message": "Internal server error"}]}
    mock_tweepy_client.search_recent_tweets.side_effect = tweepy.TwitterServerError(response=mock_response)
    mock_client.return_value = mock_tweepy_client

    result = twitter_mention(mock_config, mock_slack)

    assert mock_client.call_count == 1
    assert mock_tweepy_client.search_recent_tweets.call_count == 1
    assert mock_slack.get_client().chat_postMessage.call_count == 0
    assert result == {"mentions_count": 0}
