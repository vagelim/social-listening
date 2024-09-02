import pytest
from unittest.mock import Mock, patch
from social_listening.instagram_integration import InstagramConfig, instagram_mention

@pytest.fixture
def mock_config():
    return InstagramConfig(
        access_token="test_token",
        ig_user_id="test_user_id",
        brand_name="Test Brand",
        slack_channel="#test-channel"
    )

@pytest.fixture
def mock_slack():
    return Mock()

@pytest.fixture
def mock_requests_get():
    mock = Mock()
    mock.json.return_value = {
        "data": [
            {
                "id": "123",
                "caption": "Test caption",
                "permalink": "https://instagram.com/p/123"
            }
        ]
    }
    return mock

@patch("social_listening.instagram_integration.requests.get")
def test_instagram_mention(mock_get, mock_config, mock_slack, mock_requests_get):
    mock_get.return_value = mock_requests_get

    result = instagram_mention(mock_config, mock_slack)

    assert mock_get.call_count == 3
    assert mock_slack.get_client().chat_postMessage.call_count == 1
    assert result == {
        "tagged_media_count": 1,
        "mentioned_comments_count": 0,
        "mentioned_media_count": 0
    }

def test_instagram_config():
    config = InstagramConfig(
        access_token="test_token",
        ig_user_id="test_user_id",
        brand_name="Test Brand",
        slack_channel="#test-channel"
    )
    assert config.access_token == "test_token"
    assert config.ig_user_id == "test_user_id"
    assert config.brand_name == "Test Brand"
    assert config.slack_channel == "#test-channel"

@patch("social_listening.instagram_integration.requests.get")
def test_instagram_mention_no_data(mock_get, mock_config, mock_slack):
    mock_response = Mock()
    mock_response.json.return_value = {"data": []}
    mock_get.return_value = mock_response

    result = instagram_mention(mock_config, mock_slack)

    assert mock_get.call_count == 3
    assert mock_slack.get_client().chat_postMessage.call_count == 0
    assert result == {
        "tagged_media_count": 0,
        "mentioned_comments_count": 0,
        "mentioned_media_count": 0
    }
