import requests
from dagster import asset, Config, EnvVar
from dagster_slack import SlackResource

class InstagramConfig(Config):
    access_token: str
    ig_user_id: str
    brand_name: str
    slack_channel: str

@asset
def instagram_mention(config: InstagramConfig, slack: SlackResource):
    """
    Fetch and process Instagram mentions for a brand, then send notifications.
    """
    base_url = "https://graph.instagram.com/v12.0"

    # Fetch tagged media
    tagged_media_url = f"{base_url}/{config.ig_user_id}/tags"
    tagged_media_params = {
        "access_token": config.access_token,
        "fields": "id,caption,media_type,media_url,permalink,timestamp"
    }
    tagged_media_response = requests.get(tagged_media_url, params=tagged_media_params)
    tagged_media = tagged_media_response.json().get("data", [])

    # Fetch mentioned comments
    mentioned_comments_url = f"{base_url}/{config.ig_user_id}"
    mentioned_comments_params = {
        "access_token": config.access_token,
        "fields": "mentioned_comment.fields(text,timestamp)"
    }
    mentioned_comments_response = requests.get(mentioned_comments_url, params=mentioned_comments_params)
    mentioned_comments = mentioned_comments_response.json().get("mentioned_comment", {}).get("data", [])

    # Fetch mentioned media
    mentioned_media_url = f"{base_url}/{config.ig_user_id}"
    mentioned_media_params = {
        "access_token": config.access_token,
        "fields": "mentioned_media.fields(id,caption,media_type,media_url,permalink,timestamp)"
    }
    mentioned_media_response = requests.get(mentioned_media_url, params=mentioned_media_params)
    mentioned_media = mentioned_media_response.json().get("mentioned_media", {}).get("data", [])

    # Process and send notifications
    for media in tagged_media + mentioned_media:
        message = f"New Instagram mention for {config.brand_name}:\n"
        message += f"Type: {'Tagged' if media in tagged_media else 'Mentioned'} Media\n"
        message += f"Caption: {media.get('caption', 'N/A')}\n"
        message += f"Link: {media.get('permalink', 'N/A')}"

        slack.get_client().chat_postMessage(channel=config.slack_channel, text=message)

    for comment in mentioned_comments:
        message = f"New Instagram comment mention for {config.brand_name}:\n"
        message += f"Comment: {comment.get('text', 'N/A')}\n"
        message += f"Timestamp: {comment.get('timestamp', 'N/A')}"

        slack.get_client().chat_postMessage(channel=config.slack_channel, text=message)

    return {
        "tagged_media_count": len(tagged_media),
        "mentioned_comments_count": len(mentioned_comments),
        "mentioned_media_count": len(mentioned_media)
    }
